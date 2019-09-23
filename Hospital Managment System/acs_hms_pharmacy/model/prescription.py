# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class inpatient_prescription(models.Model):
    _inherit = ['prescription.order']

    invoice_id = fields.Many2one('account.invoice', ondelete="restrict", string='Invoice')

    @api.multi
    def create_invoice(self):
        Invoice = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        InvoiceLine = self.env['account.invoice.line']
        prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
        account_id = prop and prop.id or False
        invoice = Invoice.create({
            'account_id': self.patient_id.partner_id.property_account_receivable_id.id,
            'partner_id': self.patient_id.partner_id.id,
            'patient_id': self.patient_id.id,
            'type': 'out_invoice',
            'name': '-',
            'origin': self.name,
            'currency_id': self.env.user.company_id.currency_id.id,
            'create_stock_moves': True,
            'pharmacy_invoice': True,
            'physician_id': self.physician_id and self.physician_id.id or False,
        })
        for line in self.prescription_line:
            account_id = False
            if line.product_id.id:
                account_id = line.product_id.property_account_income_id.id
            if not account_id:
                prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                account_id = prop and prop.id or False

            InvoiceLine.create({
                'name': line.product_id.name,
                'price_unit': line.product_id.lst_price,
                'account_id': account_id,
                'quantity': line.quantity,
                'discount': 0.0,
                'uom_id': line.product_id.uom_id.id,
                'product_id': line.product_id.id,
                'account_analytic_id': False,
                'invoice_id': invoice.id,
            })
        self.invoice_id = invoice.id

    @api.multi
    def view_invoice(self):
        invoices = self.mapped('invoice_id')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
