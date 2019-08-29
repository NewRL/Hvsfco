# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class infilefel_account_invoice(models.Model):
    _name = "account.invoice"
    _inherit = "account.invoice"

    infilefel_uuid = fields.Char('Document UUID', copy=False)
    infilefel_sat_uuid = fields.Char('SAT UUID', copy=False)
    infilefel_source_xml = fields.Text('Source XML', copy=False)
    infilefel_signed_xml = fields.Text('Signed XML', copy=False)
    infilefel_result_xml = fields.Text('Result XML', copy=False)
    infilefel_void_uuid = fields.Char('Void document UUID', copy=False)
    infilefel_void_sat_uuid = fields.Char('Void SAT UUID', copy=False)
    infilefel_void_source_xml = fields.Text('Void source XML', copy=False)
    infilefel_void_signed_xml = fields.Text('Void signed XML', copy=False)
    infilefel_void_result_xml = fields.Text('Void result XML', copy=False)
    infilefel_sign_date = fields.Datetime('Sign date', copy=False)

    @api.multi
    def action_invoice_open(self):
        settings = self.env['infilefel.settings'].search([])
        if settings:
            settings.sign_document(self)
        else:
            raise UserError(_('InFile FEL settings not found'))
        return super(infilefel_account_invoice, self).action_invoice_open()

    @api.multi
    def infilefel_invoice_void(self):
        settings = self.env['infilefel.settings'].search([])
        for inv in self:
            if inv.infilefel_sat_uuid:
                settings.void_document(inv)
        return True
