#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta as td
from odoo.exceptions import UserError


class ACSProduct(models.Model):
    _inherit = 'product.template'

    hospital_product_type = fields.Selection(selection_add=[('vaccination','Vaccination')])


class ResCompany(models.Model):
    _inherit = "res.company"

    vaccination_invoicing = fields.Boolean("Allow Vaccination Invoicing", default=True)

