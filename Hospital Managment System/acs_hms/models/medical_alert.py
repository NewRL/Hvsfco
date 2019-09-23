# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class ACSMedicalAlert(models.Model):
    _name = 'acs.medical.alert'
    _description = "Medical Alert for Patient"

    name = fields.Char(required=True)
    description = fields.Text('Description')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: