# coding=utf-8

from odoo import api, fields, models, _, exceptions
from datetime import datetime, date, timedelta
import dateutil.relativedelta
from odoo.exceptions import ValidationError, AccessError, UserError, RedirectWarning, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Hospitalization(models.Model):
    _name = "acs.hospitalization"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Patient Hospitalization"

    @api.model
    def _default_checklist(self):
        vals = []
        checklists = self.env['inpatient.checklist.template'].search([])
        for checklist in checklists:
            vals.append((0, 0, {
                'name': checklist.name,
                'remark': checklist.remark,
            }))
        return vals

    @api.model
    def _default_prewardklist(self):
        vals = []
        prechecklists = self.env['pre.ward.check.list.template'].search([])
        for prechecklist in prechecklists:
            vals.append((0,0,{
                'name': prechecklist.name,
                'remark': prechecklist.remark,
            }))
        return vals

    @api.multi
    def _rec_count(self):
        Invoice = self.env['account.invoice']
        Prescription = self.env['prescription.order']
        for rec in self:
            rec.invoice_count = Invoice.search_count([('hospitalization_id','=',rec.id)])
            rec.prescription_count = Prescription.search_count([('hospitalization_id','=',rec.id)])

    name = fields.Char(string='Hospitalization#', copy=False, default="Hospitalization#")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('reserved', 'Reserved'),
        ('hosp','Hospitalized'), 
        ('discharged', 'Discharged'),
        ('cancel', 'Cancelled'),
        ('done', 'Done'),], string='Status', default='draft')
    patient_id = fields.Many2one('hms.patient', ondelete="restrict", string='Patient', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict", 
        string='Appointment', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    hospitalization_date = fields.Datetime(string='Hospitalization Date', 
        default=fields.Datetime.now, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', ondelete="restrict", 
        string='Institution', default=lambda self: self.env.user.company_id.id, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    department_id = fields.Many2one('hr.department', ondelete="restrict", 
        string='Department', domain=[('patient_depatment', '=', True)],
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    attending_physician_ids = fields.Many2many('hms.physician','hosp_pri_att_doc_rel','hosp_id','doc_id',
        string='Primary Doctors', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    relative_id = fields.Many2one('res.partner', ondelete="cascade", 
        domain=[('type', '=', 'contact')], string='Patient Relative Name', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    relative_number = fields.Char(string='Patient Relative Number')
    ward_id = fields.Many2one('hospital.ward', ondelete="restrict", string='Ward/Room', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    bed_id = fields.Many2one ('hospital.bed', ondelete="restrict", string='Bed No.', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    admission_type = fields.Selection([
        ('routine','Routine'),
        ('elective','Elective'),
        ('urgent','Urgent'),
        ('emergency','Emergency')], string='Admission type', default='routine', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    diseas_id = fields.Many2one ('hms.diseases', ondelete="restrict", 
        string='Disease', help="Reason for Admission", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    discharge_date = fields.Datetime (string='Discharge date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    no_invoice = fields.Boolean(string='Invoice Exempt', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    accomodation_history_ids = fields.One2many("patient.accomodation.history", "hospitalization_id", 
        string="Accomodation History", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    physician_id = fields.Many2one('hms.physician', string='Primary Physician', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    #CheckLists
    checklist_ids = fields.One2many('inpatient.checklist', 'hospitalization_id', 
        string='Admission Checklist', default=lambda self: self._default_checklist(), 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    pre_ward_checklist_ids = fields.One2many('pre.ward.check.list', 'hospitalization_id', 
        string='Pre-Ward Checklist', default=lambda self: self._default_prewardklist(), 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    #Hospitalization Surgery
    picking_type_id = fields.Many2one('stock.picking.type', ondelete="restrict", 
        string='Picking Type', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    consumable_line = fields.One2many('consumable.line', 'hospitalization_id',
        string='Consumable Line', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    # Discharge fields
    diagnosis = fields.Text(string="Diagnosis", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    clinincal_history = fields.Text(string="Clinical Summary", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    examination = fields.Text(string="Examination", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    investigation = fields.Text(string="Investigation", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    adv_on_dis = fields.Text(string="Advice on Discharge", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    discharge_diagnosis = fields.Text(string="Discharge Diagnosis", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    op_note = fields.Text(string="Operative Note", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    post_operative = fields.Text(string="Post Operative Course", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    instructions = fields.Text(string='Instructions', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    
    #Legal Details
    legal_case = fields.Boolean('Legal Case', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    medico_legal = fields.Selection([('yes','Yes'),('no','No')], string="If Medico legal", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    reported_to_police = fields.Selection([('yes','Yes'),('no','No')], string="Reported to police", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    fir_no = fields.Char(string="FIR No.", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    fir_reason = fields.Char(string="If not reported to police give reason", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    #For Basic Care Plan
    nurse_id = fields.Many2one('res.users', ondelete="cascade", string='Primary Nurse', 
        help='Anesthetist data of the patient', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    nursing_plan = fields.Text (string='Nursing Plan', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    ward_rounds = fields.One2many('ward.rounds', 'hospitalization_id', string='Ward Rounds', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    discharge_plan = fields.Text (string='Discharge Plan', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    move_ids = fields.One2many('stock.move','hospitalization_id', string='Moves', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    invoice_count = fields.Integer(compute='_rec_count', string='# Invoices')
    prescription_count = fields.Integer(compute='_rec_count', string='# Prescriptions')
    surgery_ids = fields.One2many('hms.surgery', 'hospitalization_id', "Surgeries")
    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    _sql_constraints = [('name_uniq', 'UNIQUE(name)', 'Hospitalization must be unique!')]


    @api.model
    def create(self, values):
        patient_id = values.get('patient_id')
        active_hospitalizations = self.search([('patient_id','=',patient_id),('state','not in',['cancel','done','discharged'])])
        if active_hospitalizations:
            raise ValidationError(_("Patient Hospitalization is already active at the moment. Please complete it before creating new."))
        if values.get('name', 'Hospitalization#') == 'Hospitalization#':
            values['name'] = self.env['ir.sequence'].next_by_code('acs.hospitalization') or 'Hospitalization#'
        return super(Hospitalization, self).create(values)

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'

    @api.multi
    def action_reserve(self):
        History = self.env['patient.accomodation.history']
        for rec in self:
            rec.bed_id.write({'state': 'reserved'})
            rec.state = 'reserved'
            History.create({
                'hospitalization_id': rec.id,
                'patient_id': rec.patient_id.id,
                'ward_id': self.ward_id.id,
                'bed_id': self.bed_id.id,
                'start_date': datetime.now(),
            })

    @api.multi
    def action_hospitalize(self):
        History = self.env['patient.accomodation.history']
        for rec in self:
            rec.bed_id.write({'state': 'occupied'})
            rec.state = 'hosp'
            rec.patient_id.write({'hospitalized': True})

    @api.multi
    def action_discharge(self):
        for rec in self:
            rec.bed_id.write({'state': 'free'})
            rec.state = 'discharged'
            rec.discharge_date = datetime.now()
            for history in rec.accomodation_history_ids:
                if rec.bed_id == history.bed_id:
                    history.end_date = datetime.now()
            rec.patient_id.write({'discharged': True})

    @api.multi
    def action_done(self):
        self.state = 'done'
        self.consume_material()
        if not self.discharge_date:
            self.discharge_date = datetime.now()

    @api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
            rec.bed_id.write({'state': 'free'}) 

    @api.multi
    def action_draft(self):
        self.state = 'draft'

    @api.multi
    def action_prescription(self):
        action = self.env.ref('acs_hms.act_open_hms_prescription_order_view').read()[0]
        action['domain'] = [('hospitalization_id', '=', self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_physician_id':self.physician_id.id,
            'default_hospitalization_id': self.id,
            'default_ward_id': self.ward_id.id,
            'default_bed_id': self.bed_id.id}
        return action

    @api.multi
    def action_view_surgery(self):
        action = self.env.ref('acs_hms_hospitalization.act_open_action_form_surgery').read()[0]
        action['domain'] = [('hospitalization_id', '=', self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_hospitalization_id': self.id}
        return action

    @api.multi
    def view_invoice(self):
        invoices = self.env['account.invoice'].search([('hospitalization_id', '=', self.id)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_view_moves(self):
        return {
            'name': _('Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'domain': [('id','in',self.move_ids.ids)],
        }

    @api.multi
    def consume_material(self):
        for hospitalization_id in self:
            stock_move = self.env['stock.move']
            if not hospitalization_id.company_id.usage_location:
                raise UserError(_('Please define a location where the consumables will be used during the surgery in company.'))
            for list_consumable in hospitalization_id.consumable_line.filtered(lambda s: not s.move_id):
                location_model , source_location_id  = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_stock')
                move = stock_move.create({
                    'name' : list_consumable.product_id.name,
                    'product_id': list_consumable.product_id.id,
                    'product_uom': list_consumable.product_id.uom_id.id,
                    'product_uom_qty': list_consumable.qty,
                    'date': hospitalization_id.hospitalization_date or fields.datetime.now(),
                    'date_expected': fields.datetime.now(),
                    'location_id': source_location_id,
                    'location_dest_id': hospitalization_id.company_id.usage_location.id,
                    'state': 'draft',
                    'origin': hospitalization_id.name,
                    'hospitalization_id': hospitalization_id.id,
                    'quantity_done': list_consumable.qty,
                })
                list_consumable.move_id = move.id
                move._action_confirm()
                move._action_assign()
                if move.state == 'assigned':
                    move._action_done()

    @api.multi
    def surgery_processed(self):
        self.consume_material()
        self.surgery_done = True

    @api.multi
    def action_create_invoice(self):
        Invoice = self.env['account.invoice']
        InvoiceLine = self.env['account.invoice.line']
        Property_obj = self.env['ir.property']
        prop = Property_obj.get('property_account_income_categ_id', 'product.category')
        prop_account_id = prop and prop.id or False
        for hospitalization_id in self:
            account_id = self.patient_id.partner_id.property_account_receivable_id
            inv_id = Invoice.create({
                'account_id': account_id and account_id.id or prop_account_id,
                'partner_id': self.patient_id.partner_id.id,
                'patient_id': hospitalization_id.patient_id.id,
                'date_invoice': fields.date.today(),
                'origin': self.name,
                'hospitalization_id': self.id,
                'create_stock_moves': False,
                'ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
                'physician_id': self.physician_id and self.physician_id.id or False,
            })
            if hospitalization_id.surgery_ids:
                for surgery in hospitalization_id.surgery_ids:
                    if surgery.surgery_product_id:
                        #Line for Surgery Charge
                        account_id = surgery.surgery_product_id.property_account_income_id
                        InvoiceLine.create({
                            'product_id': surgery.surgery_product_id.id,
                            'invoice_id': inv_id.id,
                            'price_unit':surgery.surgery_product_id.lst_price,
                            'account_id': account_id and account_id.id or prop_account_id,
                            'uom_id': surgery.surgery_product_id.uom_id.id,
                            'quantity': 1,
                            'name':  surgery.surgery_product_id.name
                        })

                    #Line for Surgery Consumables
                    for surgery_consumable in surgery.consumable_line:
                        account_id = surgery_consumable.product_id.property_account_income_id
                        InvoiceLine.create({
                            'product_id': surgery_consumable.product_id.id,
                            'name':  surgery_consumable.product_id.name,
                            'uom_id': surgery_consumable.product_id.uom_id.id,
                            'quantity':surgery_consumable.qty,
                            'price_unit': surgery_consumable.product_id.lst_price,
                            'invoice_id': inv_id.id,
                            'account_id': account_id and account_id.id or prop_account_id,
                        })


            if hospitalization_id.accomodation_history_ids:
                for bed_history in hospitalization_id.accomodation_history_ids:
                    account_id = bed_history.bed_id.product_id.property_account_income_id.id
                    InvoiceLine.create({
                        'product_id': bed_history.bed_id.product_id.id,
                        'name':  bed_history.bed_id.product_id.name,
                        'uom_id': bed_history.bed_id.product_id.uom_id.id,
                        'price_unit': bed_history.bed_id.product_id.lst_price,
                        'invoice_id': inv_id.id,
                        'quantity': bed_history.days,
                        'account_id': account_id and account_id.id or prop_account_id,
                    })
            if hospitalization_id.consumable_line:
                for list_consumable in hospitalization_id.consumable_line:
                    account_id = list_consumable.product_id.property_account_income_id
                    InvoiceLine.create({
                        'product_id': list_consumable.product_id.id,
                        'name':  list_consumable.product_id.name,
                        'uom_id': list_consumable.product_id.uom_id.id,
                        'quantity':list_consumable.qty,
                        'price_unit': list_consumable.product_id.lst_price,
                        'invoice_id': inv_id.id,
                        'account_id': account_id and account_id.id or prop_account_id,
                    })
            #hospitalization_id.state = 'done'
   
    @api.multi
    def button_indoor_medication(self):
        action = self.env.ref('acs_hms.act_open_hms_prescription_order_view').read()[0]
        action['domain'] = [('hospitalization_id', '=', self.id)]
        action['views'] = [(self.env.ref('acs_hms.view_hms_prescription_order_form').id, 'form')]
        action['context'] = {
                'default_patient_id': self.patient_id.id,
                'default_physician_id':self.physician_id.id,
                'default_hospitalization_id': self.id,
                'default_ward_id': self.ward_id.id,
                'default_bed_id': self.bed_id.id}

        return action
        return action
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: