# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    commission_product_id = fields.Many2one('product.product', string='Commission Product')
    commission_on_invoice_amount = fields.Boolean("Commission on Invoice Amount")


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    commission_on = fields.Float('Commission On')
    commission_partner1_id = fields.Many2one('res.partner', 'Dr. Commission')
    commission_partner2_id = fields.Many2one('res.partner', 'Ref. Dr. Commission')
    commission_partner3_id = fields.Many2one('res.partner', 'Third Party Commission')
    commission_amount1 = fields.Float('Dr. Commission Amount')
    commission_amount2 = fields.Float('Ref. Dr. Commission Amount')
    commission_amount3 = fields.Float('Third PartyCommission Amount')
    commission_percentage1 = fields.Float('Dr. Commission Percentage')
    commission_percentage2 = fields.Float('Ref. Dr. Commission Percentage')
    commission_percentage3 = fields.Float('Third Party Commission Percentage')
    commission_created = fields.Boolean("Commission Created")
    commission_ids = fields.One2many('acs.hms.commission', 'invoice_id', 'Sales Commission')

    @api.onchange('amount_untaxed')
    def onchange_total_amount(self):
        if self.company_id.commission_on_invoice_amount:
            self.commission_on = self.amount_untaxed

    @api.onchange('ref_physician_id')
    def onchange_ref_physician(self):
        if self.ref_physician_id and self.ref_physician_id.provide_commission:
            self.commission_partner2_id = self.ref_physician_id.id
            self.commission_percentage2 = self.ref_physician_id.commission_percentage

    @api.onchange('physician_id')
    def onchange_physician(self):
        if self.physician_id and self.physician_id.provide_commission:
            self.commission_partner1_id = self.physician_id.partner_id.id
            self.commission_percentage1 = self.physician_id.partner_id.commission_percentage

    @api.onchange('commission_on','commission_percentage1','commission_percentage2','commission_percentage3')
    def onchange_commission_on(self):
        if self.commission_on:
            self.commission_amount1 = (self.commission_on * self.commission_percentage1)/100
            self.commission_amount2 = (self.commission_on * self.commission_percentage2)/100
            self.commission_amount3 = (self.commission_on * self.commission_percentage3)/100

    @api.multi
    def create_commission(self):
        CommissionObj = self.env['acs.hms.commission']
        if self.commission_partner1_id:
            CommissionObj.create({
                'partner_id': self.commission_partner1_id.id,
                'commission_amount': self.commission_amount1,
                'commission_on': self.commission_on,
                'commission_percentage': self.commission_percentage1,
                'invoice_id': self.id,
            })
        if self.commission_partner2_id:
            CommissionObj.create({
                'partner_id': self.commission_partner2_id.id,
                'commission_amount': self.commission_amount2,
                'commission_on': self.commission_on,
                'commission_percentage': self.commission_percentage2,
                'invoice_id': self.id,
            })
        if self.commission_partner3_id:
            CommissionObj.create({
                'partner_id': self.commission_partner3_id.id,
                'commission_amount': self.commission_amount3,
                'commission_on': self.commission_on,
                'commission_percentage': self.commission_percentage3,
                'invoice_id': self.id,
            })
        self.commission_created = True

    @api.multi
    def action_invoice_open(self):
        for rec in self:
            if rec.commission_on > 0:
                rec.create_commission()
        return super(AccountInvoice, self).action_invoice_open()


class ResPartner(models.Model):
    _inherit = "res.partner"

    commission_ids = fields.One2many('acs.hms.commission', 'partner_id', 'Business Commission')
    provide_commission = fields.Boolean('Give Commission')
    commission_percentage = fields.Float('Commission Percentage')

    @api.multi
    def commission_action(self):
        action = self.env.ref('acs_hms_commission.acs_hms_commission_action').read()[0]
        action['domain'] = [('partner_id','=',self.id)]
        action['context'] = {'default_partner_id': self.id, 'search_default_not_invoiced': 1}
        return action


class Physician(models.Model):
    _inherit = "hms.physician"

    @api.multi
    def commission_action(self):
        action = self.env.ref('acs_hms_commission.acs_hms_commission_action').read()[0]
        action['domain'] = [('partner_id','=',self.partner_id.id)]
        action['context'] = {'default_partner_id': self.partner_id.id, 'search_default_not_invoiced': 1}
        return action


class Appointment(models.Model):
    _inherit = "hms.appointment"

    @api.multi
    def create_invoice(self):
        res = super(Appointment, self).create_invoice()
        for rec in self:
            rec.invoice_id.onchange_total_amount()
            rec.invoice_id.onchange_ref_physician()
            rec.invoice_id.onchange_physician()
            rec.invoice_id.onchange_commission_on()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: