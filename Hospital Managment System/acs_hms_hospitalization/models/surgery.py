# coding=utf-8
from odoo import api, fields, models
from odoo.tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ACSDietplan(models.Model):
    _name = "hms.dietplan"
    _description = "Dietplan"

    name = fields.Char(string='Name', required=True)


class ACSSurgeryTemplate(models.Model):
    _name = "hms.surgery.template"
    _description = "Surgery Template"

    name= fields.Char(string='Surgery Code', 
        help="Procedure Code, for example ICD-10-PCS Code 7-character string")
    surgery_name= fields.Char (string='Surgery Name')
    diseases_id = fields.Many2one ('hms.diseases', ondelete='restrict', 
        string='Disease', help="Reason for the surgery.")
    dietplan = fields.Many2one('hms.dietplan', ondelete='set null', 
        string='Diet Plan')
    surgery_product_id = fields.Many2one('product.product', ondelete='cascade',
        string= "Surgery Product", required=True)
    diagnosis = fields.Text(string="Diagnosis")
    clinincal_history = fields.Text(string="Clinical History")
    examination = fields.Text(string="Examination")
    investigation = fields.Text(string="Investigation")
    adv_on_dis = fields.Text(string="Advice on Discharge")
    notes = fields.Text(string='Operative Notes')
    classification = fields.Selection ([
            ('o','Optional'),
            ('r','Required'),
            ('u','Urgent')
        ], string='Surgery Classification', index=True)
    extra_info = fields.Text (string='Extra Info')
    special_precautions = fields.Text(string="Special Precautions")
    consumable_line = fields.One2many('consumable.line', 'surgery_template_id', string='Consumable Line', help="List of items that are consumed during the surgery.")
    medicament_line = fields.One2many('medicament.line', 'surgery_template_id', string='Medicament Line', help="Define the medicines to be taken after the surgery")
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Institution', default=lambda self: self.env.user.company_id.id)


class ACSSurgery(models.Model):
    _name = "hms.surgery"
    _description = "Surgery"

    @api.model
    def _default_prechecklist(self):
        vals = []
        prechecklists = self.env['pre.operative.check.list.template'].search([])
        for prechecklist in prechecklists:
            vals.append((0,0,{
                'name': prechecklist.name,
                'remark': prechecklist.remark,
            }))
        return vals

    name = fields.Char(string='Surgery Number', copy=False, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),], string='Status', default='draft', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    surgery_name= fields.Char (string='Surgery Name', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    diseases_id = fields.Many2one ('hms.diseases', ondelete='restrict', 
        string='Disease', help="Reason for the surgery.", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    dietplan = fields.Many2one('hms.dietplan', ondelete='set null', 
        string='Diet Plan', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    surgery_product_id = fields.Many2one('product.product', ondelete='cascade',
        string= "Surgery Product", required=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    surgery_template_id = fields.Many2one('hms.surgery.template', ondelete='restrict',
        string= "Surgery Template", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    diagnosis = fields.Text(string="Diagnosis", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    clinincal_history = fields.Text(string="Clinical History", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    examination = fields.Text(string="Examination", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    investigation = fields.Text(string="Investigation", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    adv_on_dis = fields.Text(string="Advice on Discharge", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    notes = fields.Text(string='Operative Notes', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    classification = fields.Selection ([
            ('o','Optional'),
            ('r','Required'),
            ('u','Urgent')
        ], string='Surgery Classification', index=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    age = fields.Char(string='Patient age',
        help='Patient age at the moment of the surgery. Can be estimative', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    extra_info = fields.Text (string='Extra Info', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    special_precautions = fields.Text(string="Special Precautions", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    consumable_line = fields.One2many('consumable.line', 'surgery_id', string='Consumable Line', help="List of items that are consumed during the surgery.", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    medicament_line = fields.One2many('medicament.line', 'surgery_id', string='Medicament Line', help="Define the medicines to be taken after the surgery", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    #Hospitalization Surgery
    hospital_ot = fields.Many2one('acs.hospital.ot', ondelete="restrict", 
        string='Operation Theater', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    start_date = fields.Datetime(string='Surgery Date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    end_date = fields.Datetime(string='End Date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    anesthetist_id = fields.Many2one('hms.physician', string='Anesthetist', ondelete="set null", 
        help='Anesthetist data of the patient', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    anaesthesia_id = fields.Many2one('anaesthesia', ondelete="set null", 
        string="Anaesthesia", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    primary_physician = fields.Many2one ('hms.physician', ondelete="restrict", 
        string='Main Surgeon', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    primary_physician_ids = fields.Many2many('hms.physician','hosp_pri_doc_rel','hosp_id','doc_id',
        string='Primary Surgeons', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    assisting_surgeons = fields.Many2many('hms.physician','hosp_doc_rel','hosp_id','doc_id',
        string='Assisting Surgeons', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    scrub_nurse = fields.Many2one('res.users', ondelete="set null", 
        string='Scrub Nurse', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    pre_operative_checklist_ids = fields.One2many('pre.operative.check.list', 'surgery_id', 
        string='Pre-Operative Checklist', default=lambda self: self._default_prechecklist(), 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict", string='Hospitalization')

    notes = fields.Text(string='Operative Notes', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    post_instruction = fields.Text(string='Instructions', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    special_precautions = fields.Text(string="Special Precautions", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Institution', related='hospitalization_id.company_id')

    @api.onchange('surgery_template_id')
    def on_change_surgery_id(self):
        medicament_lines = []
        consumable_lines = []
        Consumable = self.env['consumable.line']
        if self.surgery_template_id:
            self.surgery_name = self.surgery_template_id.surgery_name
            self.diseases_id = self.surgery_template_id.diseases_id and self.surgery_template_id.diseases_id.id
            self.surgery_product_id = self.surgery_template_id.surgery_product_id and self.surgery_template_id.surgery_product_id.id
            self.diagnosis = self.surgery_template_id.diagnosis
            self.clinincal_history = self.surgery_template_id.clinincal_history
            self.examination = self.surgery_template_id.examination
            self.investigation = self.surgery_template_id.investigation
            self.adv_on_dis = self.surgery_template_id.adv_on_dis
            self.notes = self.surgery_template_id.notes
            self.classification = self.surgery_template_id.classification

            for line in self.surgery_template_id.consumable_line:
                self.consumable_line += Consumable.new({
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom and line.product_uom.id or False,
                    'qty': line.qty,
                })

            for line in self.surgery_template_id.medicament_line:
                medicament_lines.append((0,0,{
                    'product_id': line.product_id.id,
                    'common_dosage': line.common_dosage and line.common_dosage.id or False,
                    'dose': line.dose,
                    'active_component_ids': [(6, 0, [x.id for x in line.active_component_ids])],
                    'form' : line.form.id,
                    'qty': line.qty,
                    'instruction': line.instruction,
                }))
                self.medicament_line = medicament_lines

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('hms.surgery') or 'Surgery#'
        return super(ACSSurgery, self).create(values)

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_draft(self):
        self.state = 'draft'


class PastSurgerys(models.Model):
    _name = "past.surgeries"
    _description = "Past Surgerys"
   
    result= fields.Char(string='Result')
    date= fields.Date(string='Date')
    hosp_or_doctor= fields.Char(string='Hospital/Doctor')
    description= fields.Char(string='Description', size=128)
    complication = fields.Text("Complication")
    patient_id= fields.Many2one('hms.patient', ondelete="restrict", string='Patient ID', help="Mention the past surgeries of this patient.")


class ACSConsumableLine(models.Model):
    _name = "consumable.line"
    _description = "List of Consumables"

    name = fields.Char(string='Name',default=lambda self: self.product_id.name)
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Consumable')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', help='Amount of medication (eg, 250 mg) per dose')
    qty = fields.Float(string='Quantity', default=1.0)
    surgery_template_id = fields.Many2one('hms.surgery.template', ondelete="cascade", string='Surgery Template')
    surgery_id = fields.Many2one('hms.surgery', ondelete="cascade", string='Surgery')
    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict", string='Hospitalization')
    move_id = fields.Many2one('stock.move', string='Stock Move')
    date = fields.Date("Consumed Date", default=fields.Date.context_today)

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id


class ACSMedicamentLine(models.Model):
    _name = "medicament.line"
    _description = "Medicine Lines"
    
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Medicine Name')
    name = fields.Char(string='Name')
    medicine_uom = fields.Many2one('uom.uom', string='Unit', help='Amount of medication (eg, 250 mg) per dose')
    qty = fields.Float(string='Qty',default=1.0)
    active_component_ids = fields.Many2many('active.comp','medica_line_comp_rel','medica_id','line_id',string='Active Component')
    form = fields.Many2one('drug.form', ondelete="cascade", string='Form', help='Drug form, such as tablet or gel')
    dose = fields.Float(string='Dosage', digits=(16, 2) ,help="Amount of medication (eg, 250 mg) per dose")
    common_dosage = fields.Many2one('medicament.dosage', ondelete="cascade", string='Frequency', help='Drug form, such as tablet or gel')    
    surgery_template_id = fields.Many2one('hms.surgery.template', ondelete="cascade", string='Surgery Template')
    surgery_id = fields.Many2one('hms.surgery', ondelete="cascade", string='Surgery')
    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict", string='Inpatient')
    # comment = fields.Char("Comment")
    instruction = fields.Char("Instructions")
    administered_by = fields.Many2one('res.users', ondelete='cascade', string='Administered by', help='Nurse/ Relative ')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.form = self.product_id.form_id.id
            self.dose = self.product_id.dosage
            self.medicine_uom = self.product_id.uom_id.id
            self.common_dosage = self.product_id.common_dosage.id
            self.active_component_ids = [(6, 0, [x.id for x in self.product_id.active_component_ids])]
