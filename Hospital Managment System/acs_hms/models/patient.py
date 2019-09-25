# -*- coding: utf-8 -*-

from odoo import api, fields, models ,_
from odoo.exceptions import UserError
from datetime import datetime


class ACSPatient(models.Model):
    _name = 'hms.patient'
    _description = 'Patient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {
        'res.partner': 'partner_id',
    }

    @api.multi
    def _rec_count(self):
        Invoice = self.env['account.invoice']
        Prescription = self.env['prescription.order']
        Treatment = self.env['hms.treatment']
        Appointment = self.env['hms.appointment']
        for rec in self:
            rec.invoice_count = Invoice.search_count([('partner_id','=',rec.partner_id.id)])
            rec.prescription_count = Prescription.search_count([('patient_id','=',rec.id)])
            rec.treatment_count = Treatment.search_count([('patient_id','=',rec.id)])
            rec.appointment_count = Appointment.search_count([('patient_id','=',rec.id)])

    @api.model
    def _get_service_id(self):
        consultation = False
        if self.env.user.company_id.registration_product_id:
            registration_product = self.env.user.company_id.registration_product_id.id
        return registration_product

    partner_id = fields.Many2one('res.partner', 'Partner', required=True, ondelete='restrict')
    gov_code = fields.Char(string='Government ID')
    marital_status = fields.Selection([
        ('single', 'Single'), 
        ('married', 'Married'),
        ('widow', 'Widowed'),
        ('divorcee', 'Divorced'),
        ('separate', 'Separated'),
        ('livein', 'Live In Relationship'),
    ], string='Marital Status', sort=False)
    is_corpo_tieup = fields.Boolean(string='Corporate Tie-Up', 
        help="If not checked, these Corporate Tie-Up Group will not be visible at all.")
    corpo_company_id = fields.Many2one('res.partner', string='Corporate Company', 
        domain="[('is_company', '=', True),('customer', '=', True)]", ondelete='restrict')
    emp_code = fields.Char(string='Employee ID')
    user_id = fields.Many2one('res.users', string='Related User', ondelete='cascade', 
        help='User-related data of the patient')
    primary_doctor = fields.Many2one('hms.physician', 'Primary Care Doctor', ondelete='restrict')
    ref_doctor = fields.Many2many('res.partner', 'rel_doc_pat', 'doc_id', 
        'patient_id', 'Referring Doctors', domain=[('is_referring_doctor','=',True)])
    hospitalized = fields.Boolean()
    discharged = fields.Boolean()

    #Diseases
    medical_history = fields.Text(string="Past Medical History")
    patient_diseases = fields.One2many('hms.patient.disease', 'patient_id', string='Diseases')

    #Family Form Tab
    genetic_risks = fields.One2many('hms.patient.genetic.risk', 'patient_id', 'Genetic Risks')
    family_history = fields.One2many('hms.patient.family.diseases', 'patient_id', 'Family Diseases History')
    department_ids = fields.Many2many('hr.department', 'patint_department_rel','patient_id', 'department_id',
    domain=[('patient_depatment', '=', True)], string='Departments')

    medications = fields.One2many('hms.patient.medication', 'patient_id', string='Medications')
    ethnic_group = fields.Many2one('acs.ethnicity', string='Ethnic group')
    cod = fields.Many2one('hms.diseases', string='Cause of Death')
    family_member_ids = fields.One2many('acs.family.member', 'patient_id', string='Family')

    invoice_count = fields.Integer(compute='_rec_count', string='# Invoices')
    prescription_count = fields.Integer(compute='_rec_count', string='# Prescriptions')
    treatment_count = fields.Integer(compute='_rec_count', string='# Treatments')
    appointment_count = fields.Integer(compute='_rec_count', string='# Appointments')
    appointment_ids = fields.One2many('hms.appointment', 'patient_id', 'Appointments')
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'patient_medical_alert_rel','patient_id', 'alert_id',
    string='Medical Alerts')
    occupation = fields.Char("Occupation")
    religion = fields.Char("Religion")
    caste = fields.Char("Tribe")
    registration_product_id = fields.Many2one('product.product', default=_get_service_id, string="Registration Service")
    invoice_id = fields.Many2one("account.invoice","Registration Invoice")

    @api.model
    def create(self, values):
        if values.get('code','/')=='/':
            values['code'] = self.env['ir.sequence'].next_by_code('hms.patient') or ''
        values['customer'] = True
        return super(ACSPatient, self).create(values)

    @api.onchange('state_id')
    def onchange_state(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id

    @api.multi
    def create_invoice(self):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        inv_line_obj = self.env['account.invoice.line']
        account_id =  False
        Property_obj = self.env['ir.property']
        prop = Property_obj.get('property_account_income_categ_id', 'product.category')
        prop_account_id = prop and prop.id or False
        registration_product_id = self.registration_product_id or self.env.user.company_id.registration_product_id
        if not registration_product_id:
            raise UserError(_("Please Configure Registration Product in Configuration first."))

        if registration_product_id.id:
            account_id = registration_product_id.property_account_income_id.id
        if not account_id:
            prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = prop and prop.id or False
        invoice = inv_obj.create({
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
            'patient_id': self.id,
            'type': 'out_invoice',
            'name': '-',
            'origin': self.name,
            'currency_id': self.env.user.company_id.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': registration_product_id.name or 'Patient Registration',
                'price_unit': registration_product_id.lst_price,
                'account_id': account_id,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': registration_product_id.uom_id.id,
                'product_id': registration_product_id.id,
                'account_analytic_id': False,
            })],
        })
        
        self.invoice_id = invoice.id

    @api.multi
    def view_invoices(self):
        invoices = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action['domain'] = [('id', 'in', invoices.ids)]
            action['context'] = {'default_partner_id': self.partner_id.id}
        return action

    @api.multi
    def action_appointment(self):
        action = self.env.ref('acs_hms.action_appointment').read()[0]
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_doctor.id, 'default_urgency': 'a'}
        return action

    @api.multi
    def action_prescription(self):
        action = self.env.ref('acs_hms.act_open_hms_prescription_order_view').read()[0]
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_doctor.id}
        return action

    @api.multi
    def action_treatment(self):
        action = self.env.ref('acs_hms.acs_action_form_hospital_treatment').read()[0]
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.id, 'default_physician_id': self.primary_doctor.id}
        return action

    @api.model
    def send_birthday_email(self):
        temp_obj = self.env['mail.template']
        wish_template_id = self.env['ir.model.data'].get_object_reference('acs_hms', 'email_template_birthday_wish')[1]
        today = datetime.now()
        today_month_day = '%-' + today.strftime('%m') + '-' + today.strftime('%d')
        patient_ids = self.search([('dob', 'like', today_month_day)])
        for patient_id in patient_ids:
            if patient_id.email:
                temp_obj.send_mail(patient_id.company_id.birthday_mail_template and patient_id.company_id.birthday_mail_template.id or wish_template_id, patient_id.id, force_send=True)

    @api.multi
    def action_take_picture(self):
        res_id = self.env['ir.model.data'].get_object('acs_hms', 'action_take_photo')
        dict_act_window = res_id.read()[0]
        if not dict_act_window.get('params', False):
            dict_act_window.update({'params': {}})
        dict_act_window['params'].update({'patient_id': self.ids[0]})
        return dict_act_window


class ACSFamilyMember(models.Model):
    _name = 'acs.family.member'
    _description= 'Family Member'

    member = fields.Many2one('res.partner', string='Member', help='Family Member Name')
    role = fields.Char(string='Relation', required=True)
    patient_id = fields.Many2one('hms.patient', string='Patient')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: