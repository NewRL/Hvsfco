# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from datetime import datetime

class ResPartner(models.Model):
    _inherit= "res.partner"

    @api.depends('dob', 'date_of_death')
    @api.multi
    def _get_age(self):
        for rec in self:
            age = ''
            if rec.dob:
                end_data = rec.date_of_death or fields.Datetime.now()
                delta = relativedelta(end_data, rec.dob)
                if delta.years <= 2:
                    age = str(delta.years) + _(" Year") + str(delta.months) + _(" Month ") + str(delta.days) + _(" Days")
                else:
                    age = str(delta.years) + _(" Year")
            rec.age = age

    code = fields.Char(string='Identification Code', default='/',
        help='Identifier provided by the Health Center.')
    sex = fields.Selection([
        ('male', 'Male'), 
        ('female', 'Female'), 
        ('other', 'Other')], string='Gender', required=True, default='male')
    dob = fields.Date(string='Date of Birth')
    date_of_death = fields.Date(string='Date of Death')
    age = fields.Char(string='Age', compute='_get_age')
    is_referring_doctor = fields.Boolean(string="Is Refereinng Physician")
    hospital_name = fields.Char()
    blood_group = fields.Selection([
        ('A+', 'A+'),('A-', 'A-'),
        ('B+', 'B+'),('B-', 'B-'),
        ('AB+', 'AB+'),('AB-', 'AB-'),
        ('O+', 'O+'),('O-', 'O-')], string='Blood Group')


class ResUsers(models.Model):
    _inherit= "res.users"

    department_ids = fields.Many2many('hr.department', 'user_department_rel', 'user_id','department_id', 
        domain=[('patient_depatment', '=', True)], string='Departments')


class HospitalDepartment(models.Model):
    _inherit = 'hr.department'

    note = fields.Text('Note')
    patient_depatment = fields.Boolean("Patient Department", default=True)


class ACSEthnicity(models.Model):
    _description = "Ethnicity"
    _name = 'acs.ethnicity'

    name = fields.Char(string='Name', required=True ,translate=True)
    code = fields.Char(string='Code')
    notes = fields.Char(string='Notes')

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Name must be unique!')]