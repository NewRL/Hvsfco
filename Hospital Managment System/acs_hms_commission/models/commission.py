# -*- coding: utf-8 -*-

from openerp import fields, models, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class HMSCommission(models.Model):
    _name = 'acs.hms.commission'
    _inherit = ['mail.thread']

    @api.multi
    def _invoice_status(self):
        for rec in self:
            if rec.payment_invoice_id and rec.payment_invoice_id.state:
                rec.invoice_status = rec.payment_invoice_id.state
            else:
                rec.invoice_status = 'not_inv'

    name = fields.Char(string='Name',readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'done'),
        ('cancel', 'Cancelled'),
    ], string='Status', copy=False, default='draft', track_visibility='onchange',
        readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', 'Partner', required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    invoice_id = fields.Many2one('account.invoice', 'Invoice',
        readonly=True, states={'draft': [('readonly', False)]})
    commission_on = fields.Float('Commission On',
        readonly=True, states={'draft': [('readonly', False)]})
    commission_percentage = fields.Float('Commission Percentage',
        readonly=True, states={'draft': [('readonly', False)]})
    commission_amount = fields.Float('Commission Amount',
        readonly=True, states={'draft': [('readonly', False)]})
    invoice_line_id = fields.Many2one('account.invoice.line', 'Payment Invoice Line',
        readonly=True, states={'draft': [('readonly', False)]})
    payment_invoice_id = fields.Many2one('account.invoice', related="invoice_line_id.invoice_id", string='Payment Invoice', readonly=True)
    invoice_status = fields.Selection([
        ('not_inv', 'Not Invoiced'),
        ('draft', 'Draft Invoice'),
        ('profoma', 'Profoma'),
        ('profoma2', 'Profoma2'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'), 
    ], string='Payment Invoice Status', copy=False, default='not_inv', readonly=True, compute="_invoice_status")
    note = fields.Text("Note")

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete an record which is not draft or cancelled.'))
        return super(HMSCommission, self).unlink()

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('acs.hms.commission')
        return super(HMSCommission, self).create(values)

    @api.multi
    def done_commission(self):
        self.state = 'done'

    @api.multi
    def draft_commission(self):
        self.state = 'draft'

    @api.multi
    def cancel_commission(self):
        self.state = 'cancel'