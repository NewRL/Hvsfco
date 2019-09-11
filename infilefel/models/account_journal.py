# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class infilefel_account_journal(models.Model):
    _name = "account.journal"
    _inherit = "account.journal"

    infilefel_type = fields.Selection([
        ('', ''),
        ('FACT', 'FACT'),
        ('FCAM', 'FCAM'),
        ('NCRE', 'NCRE'),
    ], string='FEL Invoice type', default='')
    infilefel_previous_authorization = fields.Char('Previous invoice authorization')
    infilefel_previous_serial = fields.Char('Previous invoice serial')
