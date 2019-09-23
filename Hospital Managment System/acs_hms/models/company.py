# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _description = "Hospital"
    _inherit = "res.company"

    registration_product_id = fields.Many2one('product.product', 
        domain=[('type','=','service')],
        string='Treatment Registration Invoice Product', 
        ondelete='cascade', help='Registration Product')
    consultation_product_id = fields.Many2one('product.product', 
        domain=[('type','=','service')],
        string='Consultation Invoice Product', 
        ondelete='cascade', help='Consultation Product')
    followup_days = fields.Float('Followup Days', default=30)
    followup_product_id = fields.Many2one('product.product', 
        domain=[('type','=','service')],
        string='Follow-up Invoice Product', 
        ondelete='cascade', help='Followup Product')
    birthday_mail_template = fields.Many2one('mail.template', 'Birthday Wishes Template',
            help="This will set the default mail template for birthday wishes.")
    registration_date = fields.Char(string='Date of Registration')
    appointment_anytime_invoice = fields.Boolean("Allow Invoice Anytime in Appointment")
    appo_invoice_advance = fields.Boolean("Invoice before Confirmation in Appointment")
    app_usage_location = fields.Many2one('stock.location', 
        string='Usage Location for Consumed Products in Appointment')

    @api.onchange('appointment_anytime_invoice')
    def onchnage_appointment_anytime_invoice(self):
        if self.appointment_anytime_invoice:
            self.appo_invoice_advance = False

    @api.onchange('appo_invoice_advance')
    def onchnage_appo_invoice_advance(self):
        if self.appo_invoice_advance:
            self.appointment_anytime_invoice = False
