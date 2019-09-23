# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import date, datetime, timedelta


class AppointmentPurpose(models.Model):
    _name = 'appointment.purpose'
    _description = "Appointment Purpose"

    name = fields.Char(string='Appointment Purpose', required=True, translate=True)


class AppointmentCabin(models.Model):
    _name = 'appointment.cabin'
    _description = "Appointment Cabin"

    name = fields.Char(string='Appointment Cabin', required=True, translate=True)


class Appointment(models.Model):
    _name = 'hms.appointment'
    _description = "Appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _get_service_id(self):
        consultation = False
        if self.env.user.company_id.consultation_product_id:
            consultation = self.env.user.company_id.consultation_product_id.id
        return consultation

    @api.onchange('department_id')
    def onchange_department(self):
        res = {}
        if self.department_id:
            physicians = self.env['hms.physician'].search([('department_ids', 'in', self.department_id.id)])
            res['domain'] = {'physician_id':[('id','in',physicians.ids)]}
        return res

    @api.multi
    @api.depends('medical_alert_ids')
    def _get_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.medical_alert_ids)


    name = fields.Char(string='Appointment Id', readonly=True, copy=False, states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    patient_id = fields.Many2one('hms.patient', ondelete='restrict',  string='Patient',
        required=True, index=True,help='Patient Name', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    image = fields.Binary(related='patient_id.image',string='Image', readonly=True)
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Physician', 
        index=True, help='Physician\'s Name', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    department_id = fields.Many2one('hr.department', ondelete='restrict', 
        domain=[('patient_depatment', '=', True)],
        string='Department', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    no_invoice = fields.Boolean(string='Invoice Exempt', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    date = fields.Datetime(string='Date', default=fields.Datetime.now, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    
    follow_date = fields.Datetime(string="Follow Up Date", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    weight = fields.Float(string='Weight', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    temp = fields.Char(string='Temp', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    hr = fields.Char(string='HR', help="Heart Rate",
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    rr = fields.Char(string='RR', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, help='Respiratory Rate')
    bp = fields.Char(string='BP', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, help='Blood Pressure')
    spo2 = fields.Char(string='SpO2', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, help='Oxygen Saturation, percentage of oxygen bound to hemoglobin')
    differencial_diagnosis = fields.Text(string='Differencial Diagnosis', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    medical_advice = fields.Text(string='Medical Advice', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    chief_complain = fields.Text(string='Chief Complaints', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    present_illness = fields.Text(string='History of Present Illness', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    lab_report = fields.Text(string='Lab Report', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    radiological_report = fields.Text(string='Radiological Report', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    notes = fields.Text(string='Notes', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    past_history = fields.Text(string='Past History', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    invoice_id = fields.Many2one('account.invoice', string='Invoice', ondelete='cascade')
    urgency = fields.Selection([
            ('a', 'Normal'),
            ('b', 'Urgent'),
            ('c', 'Medical Emergency'),
        ], string='Urgency Level', default='a', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('waiting', 'Waiting'),
            ('in_consultation', 'In consultation'),
            ('to_invoice', 'To Invoice'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='State',default='draft', required=True, copy=False, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    product_id = fields.Many2one('product.product', ondelete='restrict', 
        string='Consultation Service', help="Consultation Services", 
        domain=[('hospital_product_type', '=', "consultation")], required=True, 
        default=_get_service_id, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    age = fields.Char(related='patient_id.age', string='Age', readonly=True)
    company_id = fields.Many2one('res.company', ondelete='restrict', 
        string='Institution',default=lambda self: self.env.user.company_id.id, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})  
    anytime_invoice = fields.Boolean(related="company_id.appointment_anytime_invoice")
    advance_invoice = fields.Boolean(related="company_id.appo_invoice_advance")
    no_invoice = fields.Boolean('Invoice Exempt', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    consultation_type = fields.Selection([
        ('consultation','Consultation'),
        ('followup','Follow Up')],'Consultation Type', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    #Diseases
    diseas_id = fields.Many2one('hms.diseases', 'Disease')
    medical_history = fields.Text(related='patient_id.medical_history', 
        string="Past Medical History", readonly=True)
    patient_diseases = fields.One2many('hms.patient.disease', 
        related='patient_id.patient_diseases', string='Diseases', 
        help='Mark if the patient has died', readonly=True)

    duration = fields.Float(string='Duration', default=15.00, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    waiting_date_start = fields.Datetime('Waiting Start Date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    waiting_date_end = fields.Datetime('Waiting end Date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    waiting_duration = fields.Float('Wait Time', readonly=True)
    waiting_duration_timer = fields.Float('Wait Timer', readonly=True, default="0.1")

    date_start = fields.Datetime(string='Start Date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    date_end = fields.Datetime(string='End Date',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    appointment_duration = fields.Float('Consultation Time', readonly=True)
    appointment_duration_timer = fields.Float('Consultation Timer', readonly=True, default="0.1")

    purpose_id = fields.Many2one('appointment.purpose', ondelete='cascade', 
        string='Purpose', help="Appointment Purpose", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    cabin_id = fields.Many2one('appointment.cabin', ondelete='cascade', 
        string='Cabin', help="Appointment Cabin", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    treatment_id = fields.Many2one('hms.treatment', ondelete='cascade', 
        string='Treatment', help="Treatment Id",
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    ref_physician_id = fields.Many2one('res.partner', ondelete='restrict', string='Referring Physician', 
        index=True, help='Referring Physician', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    responsible_id = fields.Many2one('hms.physician', "Responsible Nurse/Doctor")
    medical_alert_ids = fields.Many2many('acs.medical.alert', 'appointment_medical_alert_rel','appointment_id', 'alert_id',
     string='Medical Alerts', related='patient_id.medical_alert_ids')
    alert_count = fields.Integer(compute='_get_alert_count', default=0)
    consumable_line = fields.One2many('appointment.consumable', 'appointment_id',
        string='Consumable Line', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)], 'to_invoice': [('readonly', True)]})

    @api.model
    def create(self, values):
        if values.get('name', 'New Appointment') == 'New Appointment':
            values['name'] = self.env['ir.sequence'].next_by_code('hms.appointment') or 'New Appointment'
        return super(Appointment, self).create(values)

    @api.multi
    def unlink(self):
        for data in self:
            if data.state in ['done']:
                raise UserError(_('You can not delete record in done state'))
        return super(Appointment, self).unlink()

    @api.multi
    def print_report(self):
        return self.env.ref('acs_hms.action_appointment_report').report_action(self)

    @api.multi
    def action_appointment_send(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('acs_hms', 'acs_appointment_email')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'hms.appointment',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            #'custom_layout': "sale.mail_template_data_notification_email_sale_order",
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def create_invoice(self):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        inv_line_obj = self.env['account.invoice.line']
        account_id =  False
        Property_obj = self.env['ir.property']
        prop = Property_obj.get('property_account_income_categ_id', 'product.category')
        prop_account_id = prop and prop.id or False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id
        if not account_id:
            prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = prop and prop.id or False
        invoice = inv_obj.create({
            'account_id': self.patient_id.partner_id.property_account_receivable_id.id,
            'partner_id': self.patient_id.partner_id.id,
            'patient_id': self.patient_id.id,
            'type': 'out_invoice',
            'name': '-',
            'origin': self.name,
            'currency_id': self.env.user.company_id.currency_id.id,
            'ref_physician_id': self.ref_physician_id and self.ref_physician_id.id or False,
            'physician_id': self.physician_id and self.physician_id.id or False,
            'invoice_line_ids': [(0, 0, {
                'name': self.product_id.name,
                'price_unit': self.product_id.lst_price,
                'account_id': account_id,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'account_analytic_id': False,
            })],
        })

        for consumable in self.consumable_line:
            account_id = consumable.product_id.property_account_income_id
            self.env['account.invoice.line'].create({
                'product_id': consumable.product_id.id,
                'name':  consumable.product_id.name,
                'uom_id': consumable.product_id.uom_id.id,
                'quantity':consumable.qty,
                'price_unit': consumable.product_id.lst_price,
                'invoice_id': invoice.id,
                'account_id': account_id and account_id.id or prop_account_id,
            })

        self.invoice_id = invoice.id
        if self.state == 'to_invoice':
            self.state = 'done'

    @api.multi
    def view_invoice(self):
        invoices = self.mapped('invoice_id')
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
    def action_refer_doctor(self):
        action = self.env.ref('acs_hms.action_appointment').read()[0]
        action['domain'] = [('patient_id','=',self.id)]
        action['context'] = {'default_patient_id': self.patient_id.id, 'default_physician_id': self.physician_id.id, 'default_urgency': 'a'}
        return action

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        if self.patient_id:
            self.age = self.patient_id.age
            followup_days = self.env.user.company_id.followup_days
            followup_day_limit = (datetime.now() + timedelta(days=followup_days)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            appointment_id = self.search([('patient_id', '=', self.patient_id.id),('date','<=',followup_day_limit)])
            self.physician_id = self.patient_id.primary_doctor and self.patient_id.primary_doctor.id
            if appointment_id:
                self.consultation_type = 'followup'
                if self.env.user.company_id.followup_product_id:
                    self.product_id = self.env.user.company_id.followup_product_id.id
            else:
                self.consultation_type = 'consultation'

    @api.onchange('physician_id')
    def onchange_doctor(self):
        if self.physician_id:
            self.product_id = self.physician_id.consul_service.id or False
            if self.consultation_type=='followup':
                if self.physician_id.followup_service:
                    self.product_id = self.physician_id.followup_service.id

                elif self.env.user.company_id.followup_product_id:
                   self.product_id = self.env.user.company_id.followup_product_id.id

    @api.one
    def appointment_confirm(self):
        if self.company_id.appo_invoice_advance and not self.invoice_id:
            raise UserError(_('Invoice is not created yet'))
        
        self.state = 'confirm'

    @api.one
    def appointment_waiting(self):
        self.state = 'waiting'
        self.waiting_date_start = datetime.now()
        self.waiting_duration = 0.1

    @api.one
    def appointment_consultation(self):
        if not self.waiting_date_start:
            raise UserError(('No waiting start time defined.'))
        datetime_diff = datetime.now() - self.waiting_date_start
        m, s = divmod(datetime_diff.total_seconds(), 60)
        h, m = divmod(m, 60)
        self.waiting_duration = float(('%0*d')%(2,h) + '.' + ('%0*d')%(2,m*1.677966102))
        self.state = 'in_consultation'
        self.waiting_date_end = datetime.now()
        self.date_start = datetime.now()

    @api.one
    def consultation_done(self):
        if self.date_start:
            datetime_diff = datetime.now() - self.date_start
            m, s = divmod(datetime_diff.total_seconds(), 60)
            h, m = divmod(m, 60)
            self.appointment_duration = float(('%0*d')%(2,h) + '.' + ('%0*d')%(2,m*1.677966102))
        self.date_end = datetime.now()
        if self.no_invoice or self.invoice_id:
            self.state = 'done'
        else:
            self.state ='to_invoice'
        if self.consumable_line:
            self.consume_material()

    @api.one
    def appointment_done(self):
        self.state = 'done'

    @api.one
    def appointment_cancel(self):
        self.state = 'cancel'
        self.waiting_date_start = False
        self.waiting_date_end = False

    @api.one
    def appointment_draft(self):
        self.state = 'draft'

    @api.multi
    def action_prescription(self):
        action = self.env.ref('acs_hms.act_open_hms_prescription_order_view').read()[0]
        action['domain'] = [('appointment', '=', self.id)]
        action['context'] = {
                'default_patient_id': self.patient_id.id,
                'default_physician_id':self.physician_id.id,
                'default_diseases': self.diseas_id and self.diseas_id.id or False,
                'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
                'default_appointment': self.id}
        return action

    @api.multi
    def button_pres_req(self):
        action = self.env.ref('acs_hms.act_open_hms_prescription_order_view').read()[0]
        action['domain'] = [('appointment', '=', self.id)]
        action['views'] = [(self.env.ref('acs_hms.view_hms_prescription_order_form').id, 'form')]
        action['context'] = {
                'default_patient_id': self.patient_id.id,
                'default_physician_id':self.physician_id.id,
                'default_diseases': self.diseas_id and self.diseas_id.id or False,
                'default_treatment_id': self.treatment_id and self.treatment_id.id or False,
                'default_appointment': self.id}
        return action

    @api.multi
    def consume_material(self):
        for appointment in self:
            stock_move = self.env['stock.move']
            if not appointment.company_id.app_usage_location:
                raise UserError(_('Please define a location where the consumables will be used.'))
            for list_consumable in appointment.consumable_line.filtered(lambda s: not s.move_id):
                location_model , source_location_id  = self.env['ir.model.data'].get_object_reference('stock', 'stock_location_stock')
                move = stock_move.create({
                    'name' : list_consumable.product_id.name,
                    'product_id': list_consumable.product_id.id,
                    'product_uom': list_consumable.product_id.uom_id.id,
                    'product_uom_qty': list_consumable.qty,
                    'date': appointment.date or fields.datetime.now(),
                    'date_expected': fields.datetime.now(),
                    'location_id': source_location_id,
                    'location_dest_id': appointment.company_id.app_usage_location.id,
                    'state': 'draft',
                    'origin': appointment.name,
                    'appointment_id': appointment.id,
                    'quantity_done': list_consumable.qty,
                })
                list_consumable.move_id = move.id
                move._action_confirm()
                move._action_assign()
                if move.state == 'assigned':
                    move._action_done()

class ACSAppointmentConsumable(models.Model):
    _name = "appointment.consumable"
    _description = "List of Consumables"

    name = fields.Char(string='Name',default=lambda self: self.product_id.name)
    product_id = fields.Many2one('product.product', ondelete="cascade", string='Consumable')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', help='Amount of medication (eg, 250 mg) per dose')
    qty = fields.Float(string='Quantity', default=1.0)
    appointment_id = fields.Many2one('hms.appointment', ondelete="restrict", string='Hospitalization')
    move_id = fields.Many2one('stock.move', string='Stock Move')
    date = fields.Date("Consumed Date", default=fields.Date.context_today)

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.product_uom = self.product_id.uom_id.id

class StockMove(models.Model):
    _inherit = "stock.move"

    appointment_id = fields.Many2one('hms.appointment', "Appointment")
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: