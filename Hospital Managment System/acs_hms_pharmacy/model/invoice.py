# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError, UserError, RedirectWarning, Warning


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _get_default_warehouse(self):
        warehouse_id = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        return warehouse_id

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', default=_get_default_warehouse)
    create_stock_moves = fields.Boolean("Create Stock Moves?", copy=False, default=False)
    picking_id = fields.Many2one('stock.picking', 'Picking', copy=False)
    patient_id = fields.Many2one('hms.patient',string="Patient")
    pharmacy_invoice = fields.Boolean("Pharmacy Invoice", copy=False)

    @api.model
    def create_move(self, invoice, picking_type_id, location_id, location_dest_id):
        StockMove = self.env['stock.move']
        MoveLine = self.env['stock.move.line']
        picking_id = self.env['stock.picking'].create({
            'partner_id': invoice.partner_id.id,
            'date': fields.datetime.now(), 
            'company_id': invoice.company_id.id,
            'picking_type_id': picking_type_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'origin': invoice.number,
        })

        invoice.picking_id = picking_id.id
        for line in invoice.invoice_line_ids:
            if line.product_id and line.product_id.type != 'service':
                quantity = line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                move_id = StockMove.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': quantity ,
                    'product_uom': line.product_id.uom_id.id,
                    'date': fields.datetime.now(),
                    'date_expected': fields.datetime.now(),
                    'picking_id': picking_id.id,
                    'state': 'draft',
                    'name': line.name,
                    'location_id': location_id.id,
                    'location_dest_id': location_dest_id.id,
                    'quantity_done': quantity,
                })
 
        picking_id.action_confirm()
        picking_id.action_assign()
        for inv_line in invoice.invoice_line_ids:
            quantity = inv_line.uom_id._compute_quantity(inv_line.quantity, inv_line.product_id.uom_id)
            if inv_line.batch_no:
                move_line_id = MoveLine.search([('product_id', '=', inv_line.product_id.id),('picking_id','=',picking_id.id),('qty_done','=',quantity),('lot_id','=',False)],limit=1)
                if move_line_id:
                    move_line_id.lot_id = inv_line.batch_no.id
        if picking_id.state == 'assigned':
            picking_id.button_validate()

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        if self.picking_id:
            self.picking_id.action_cancel()

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        stock_location_obj = self.env['stock.location']

        for inv in self:
            if inv.create_stock_moves:
                if inv.type == 'out_invoice':
                    picking_type_id = inv.warehouse_id.out_type_id
                    location_id = inv.warehouse_id.lot_stock_id
                    location_dest_id = inv.partner_id.property_stock_customer
                    self.create_move(inv, picking_type_id, location_id, location_dest_id)

                if inv.type == 'in_invoice':
                    picking_type_id = inv.warehouse_id.in_type_id
                    location_id = inv.partner_id.property_stock_supplier
                    location_dest_id = inv.warehouse_id.lot_stock_id
                    self.create_move(inv, picking_type_id, location_id, location_dest_id)

                elif inv.type == 'out_refund':
                    picking_type_id = inv.warehouse_id.in_type_id
                    location_id = inv.partner_id.property_stock_customer
                    location_dest_id = inv.warehouse_id.lot_stock_id
                    self.create_move(inv, picking_type_id, location_id, location_dest_id)

                elif inv.type == 'in_refund':
                    picking_type_id = inv.warehouse_id.out_type_id
                    location_id = inv.warehouse_id.lot_stock_id
                    location_dest_id = inv.partner_id.property_stock_supplier
                    self.create_move(inv, picking_type_id, location_id)
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    product_id = fields.Many2one(domain=[('sale_ok', '=', True),('hospital_product_type', '=', 'medicament')])
    batch_no = fields.Many2one("stock.production.lot", domain=[('locked', '=', False)], string="Batch Number")
    exp_date = fields.Datetime(string="Expiry Date")

    @api.onchange('quantity', 'batch_no')
    def onchange_batch(self):
        if self.batch_no and self.invoice_id.type=='out_invoice':
            if self.batch_no.product_qty < self.quantity:
                batch_product_qty = self.batch_no.product_qty
                self.batch_no = False
                warning = {
                    'title': "Warning",
                    'message': _("Selected Lot do not have enough qty. %s qty needed and lot have only %s" %(self.quantity,batch_product_qty)),
                }
                return {'warning': warning}

            self.exp_date = self.batch_no.use_date
            if self.batch_no.mrp:
                self.price_unit = self.batch_no.mrp

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(AccountInvoiceLine, self)._onchange_product_id()
        if self.invoice_id and self.product_id and self.invoice_id.type =='in_invoice':
            self.uom_id = self.product_id.uom_po_id.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: