# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ACSTreatment(models.Model):
    _name = 'hms.treatment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.multi
    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)

    name = fields.Char(string='Appointment Id', readonly=True, index=True, copy=False)
    patient_id = fields.Many2one('hms.patient', 'Patient', required=True, index=True,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    department_id = fields.Many2one('hr.department', ondelete='restrict', string='Department',
        domain=[('patient_depatment', '=', True)],
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    image = fields.Binary(related='patient_id.image', string='Image', readonly=True)
    date = fields.Datetime(string='Date of Diagnosis', default=fields.Datetime.now,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    healed_date = fields.Date(string='Healed Date',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    end_date = fields.Date(string='End Date',help='End of treatment date',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    diagnosis_id = fields.Many2one('hms.diseases',string='Diagnosis',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Physician',
        help='Physician who treated or diagnosed the patient',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    attending_physician_ids = fields.Many2many('hms.physician','hosp_treat_doc_rel','treat_id','doc_id', string='Primary Doctors',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    #V13: Remove it as not needed i think
    prescription_line = fields.One2many('prescription.line', 'treatment_id','Prescription',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    finding = fields.Text(string="Findings",
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    appointment_ids = fields.One2many('hms.appointment', 'treatment_id', string='Appintments',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    state = fields.Selection([
            ('draft', 'Draft'),
            ('running', 'Running'),
            ('done', 'Completed'),
            ('cancel', 'Cancelled'),
        ], string='State',default='draft', required=True, copy=False, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    description = fields.Char(string='Treatment Description',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    is_allergy = fields.Boolean(string='Allergic Disease',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    pregnancy_warning = fields.Boolean(string='Pregnancy warning',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    lactation = fields.Boolean('Lactation',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    disease_severity = fields.Selection([
            ('mild', 'Mild'),
            ('moderate', 'Moderate'),
            ('severe', 'Severe'),
        ], string='Severity',index=True, sort=False,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    disease_status = fields.Selection([
            ('acute', 'Acute'),
            ('chronic', 'Chronic'),
            ('unchanged', 'Unchanged'),
            ('healed', 'Healed'),
            ('improving', 'Improving'),
            ('worsening', 'Worsening'),
        ], string='Status of the disease',index=True, sort=False,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    is_infectious = fields.Boolean(string='Infectious Disease',
        help='Check if the patient has an infectious' \
        'transmissible disease',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    allergy_type = fields.Selection([
            ('da', 'Drug Allergy'),
            ('fa', 'Food Allergy'),
            ('ma', 'Misc Allergy'),
            ('mc', 'Misc Contraindication'),
        ], string='Allergy type',index=True, sort=False,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    age = fields.Char(string='Age when diagnosed',
        help='Patient age at the moment of the diagnosis. Can be estimative',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    patient_disease_id = fields.Many2one('hms.patient.disease', string='Patient Disease',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    invoice_id = fields.Many2one('account.invoice',string='Invoice', ondelete='restrict')
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Company',default=lambda self: self.env.user.company_id.id, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'treatment_medical_alert_rel','treatment_id', 'alert_id',
    string='Medical Alerts', related="patient_id.medical_alert_ids")
    alert_count = fields.Integer(compute='_get_alert_count', default=0)

    @api.model
    def create(self, values):
        if values.get('name', 'New Treatment') == 'New Treatment':
            values['name'] = self.env['ir.sequence'].next_by_code('hms.treatment') or 'New Treatment'
        return super(ACSTreatment, self).create(values)

    @api.multi
    def unlink(self):
        for data in self:
            if data.state in ['done']:
                raise UserError(('You can not delete record in done state'))
        return super(ACSTreatment, self).unlink()

    @api.one
    def treatment_draft(self):
        self.state = 'draft'

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        self.age = self.patient_id.age

    @api.one
    def treatment_running(self):
        #Create Patient Disease
        patient_disease_id = self.env['hms.patient.disease'].create({
            'patient_id': self.patient_id.id,
            'treatment_id': self.id,
            'disease': self.diagnosis_id.id,
            'age': self.age,
            'diagnosed_date': self.date,
            'healed_date': self.healed_date,
            'allergy_type': self.allergy_type,
            'is_infectious': self.is_infectious,
            'status': self.disease_status,
            'disease_severity': self.disease_severity,
            'lactation': self.lactation,
            'pregnancy_warning': self.pregnancy_warning,
            'is_allergy': self.is_allergy,
            'description': self.description,
        })
        self.patient_disease_id = patient_disease_id.id
        self.state = 'running'

    @api.one
    def treatment_done(self):
        self.state = 'done'

    @api.one
    def treatment_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_appointment(self):
        action = self.env.ref('acs_hms.action_appointment').read()[0]
        action['domain'] = [('treatment_id','=',self.id)]
        action['context'] = { 
            'default_treatment_id': self.id, 
            'default_patient_id': self.patient_id.id, 
            'default_physician_id': self.physician_id.id, 
            'default_urgency': 'a'}
        return action

    @api.multi
    def create_invoice(self):
        inv_obj = self.env['account.invoice']
        product_obj = self.env['product.product']
        reg_product = self.env.user.company_id.registration_product_id
        #Note: Check if condition is not working
        if reg_product==product_obj:
            UserError(('Please first configure patient treatment registration fee Product in Hospital Configuration.'))

        account_id = False
        if reg_product.property_account_income_id:
            account_id = reg_product.property_account_income_id.id
        if not account_id:
            prop = self.env['ir.property'].get('property_account_income_categ_id', 'product.category')
            account_id = prop and prop.id or False
        invoice = inv_obj.create({
            'name': '-',
            'account_id': self.patient_id.partner_id.property_account_receivable_id.id,
            'partner_id': self.patient_id.partner_id.id,
            'patient_id': self.id,
            'origin': self.name,
            'type': 'out_invoice',
            'currency_id': self.env.user.company_id.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': reg_product.name,
                'price_unit': reg_product.lst_price,
                'account_id': account_id,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': reg_product.uom_id.id,
                'product_id': reg_product.id,
                'account_analytic_id': False,
                'invoice_line_tax_ids': [(6, 0, [x.id for x in reg_product.taxes_id])]
            })],
        })
        return self.write({'invoice_id': invoice.id})

    @api.multi
    def view_invoice(self):
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        action['res_id'] = self.invoice_id.id
        return action