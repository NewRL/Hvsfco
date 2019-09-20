# -*- coding: utf-8 -*-

from odoo import api,fields,models,_
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
 
    physician_id = fields.Many2one('hms.physician', string='Physician') 
    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', readonly=True, states={'draft': [('readonly', False)]})

    def split_invoice(self):
        for record in self: 
            lines_to_split = record.invoice_line_ids.filtered(lambda r: r.split)
            if len(lines_to_split) >= 1:
                new_inv_id = self.copy()
                for line in new_inv_id.invoice_line_ids:
                    if not line.split:
                        line.unlink()
                    else:
                        line.split = False
                        line.quantity = line.qty_to_split
                        line.qty_to_split = 0

                for line in record.invoice_line_ids:
                    if line.split:
                        if line.quantity == line.qty_to_split:
                            line.unlink()
                        else:
                            line.quantity -= line.qty_to_split 
            else:
                raise ValidationError(_('Please Lines To Split'))


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
   
    split = fields.Boolean(string='Split') 
    qty_to_split = fields.Float(string='Split Qty.')

    @api.onchange('split')
    def onchange_split(self):
        if self.split:
            self.qty_to_split = 1