# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResourceCalendar(models.Model):
    _description = "Working Schedule"
    _inherit = "resource.calendar"

    category = fields.Selection([
            ('doctor', 'Doctor'),
            ('nurse', 'Nurse'),
        ], string='Category', default='doctor')
    department_id = fields.Many2one('hr.department', ondelete='restrict', 
        domain=[('patient_depatment', '=', True)],
        string='Department', help="Department for which the schedule is applicable.")
    doctors = fields.Many2many('hms.physician', 'rel_doc_resource', 'doctor_id', 
        'resource_id', 'Doctors')