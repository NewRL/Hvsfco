# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models
from odoo.exceptions import ValidationError, AccessError, UserError, RedirectWarning, Warning


class InsuranceCompany(models.Model):
    _name = 'hms.insurance.company'
    _description = "Insurance Company"

    name = fields.Char('Name')
    description = fields.Text()


class Insurance(models.Model):
    _name = 'hms.patient.insurance'
    _description = "Patient Insurance"
    
    patient_id = fields.Many2one('hms.patient', string ='Patient', ondelete='restrict')
    insurance_company = fields.Many2one('hms.insurance.company', string ="Insurance Company")
    policy_number = fields.Char(string ="Policy Number")
    insured_value = fields.Float(string ="Insured Value")
    validity = fields.Date(string="Validity")
    active = fields.Boolean(string="Active", default=True)


class Patient(models.Model):
    _inherit = 'hms.patient'

    insurance_ids = fields.One2many('hms.patient.insurance','patient_id',
        string='Insurance')


class Invoice(models.Model):
    _inherit = 'account.invoice'

    claim_id = fields.Many2one('hms.insurance.claim', 'Claim')
    insurance_company_id = fields.Many2one('hms.insurance.company', related='claim_id.insurance_company_id', string='Insurance Company', readonly=True)
    hospital_invoice_type = fields.Selection([
            ('claim', 'Claim'), ('inpatient', 'Inpatient')], string="Hospital Invoice Type")


class InsuranceTPA(models.Model):
    _name = 'insurance.tpa'
    _description = "Insurance TPA"
    _inherits = {
        'res.partner': 'partner_id',
    }

    partner_id = fields.Many2one('res.partner', 'Partner', required=True, ondelete='restrict')


class InsuranceChecklistTemp(models.Model):
    _name = 'hms.insurance.checklist.template'
    _description = "Insurance Checklist Template"

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class RequiredDocuments(models.Model):
    _name = 'hms.insurance.req.doc'
    _description = "Insurance Req Doc"
    
    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)


class InsuCheckList(models.Model):
    _name="hms.insurance.checklist"
    _description = "Insurance Checklist"

    name = fields.Char(string="Name")
    is_done = fields.Boolean(string="Y/N", default=False)
    remark = fields.Char(string="Remarks")
    claim_id = fields.Many2one("hms.insurance.claim", string="Claim")


class Attachments(models.Model):
    _inherit = "ir.attachment"

    patient_id = fields.Many2one('hms.patient', 'Patient')
    hospitalization_id = fields.Many2one('acs.hospitalization', 'Hospitalization')
    claim_id = fields.Many2one('hms.insurance.claim', 'Claim')


class Hospitalization(models.Model):
    _inherit = 'acs.hospitalization'

    @api.multi
    def action_patient_doc_view(self):
        res = {
            'name': 'Documents',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'domain': [('res_id', '=', self.patient_id.id), ('res_model', '=', 'hms.patient')],
            'context': {'default_res_id': self.patient_id.id,
                'default_res_model': 'hms.patient',
                'default_patient_id': self.patient_id.id,
                'default_hospitalization_id': self.id,
                'default_is_document': True
            },
        }
        return res

    @api.multi
    def action_claim_view(self):
        action = self.env.ref('acs_hms_insurance.action_insurance_claim').read()[0]
        action['domain'] = [('patient_id', '=', self.patient_id.id),('hospitalization_id','=',self.id)]
        action['context'] = {
            'default_patient_id': self.patient_id.id,
            'default_hospitalization_id': self.id
        }
        return action

    cashless = fields.Boolean(string="Cashless",default=False, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    package_id = fields.Many2one('hospitalization.package', string='Package', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    #ACS: Remove in v12 only invoice field will be ok
    package_bill_created = fields.Boolean(string="Package Bill Created", default=False, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    package_invoice_id = fields.Many2one('account.invoice', string="Package Invoice", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    claim_ids = fields.One2many('hms.insurance.claim','hospitalization_id', "Claims")

    @api.one
    def create_package_invoce(self):
        #self.state = 'invoiced'
        #self.package_bill_created = True
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        inv_line_obj = self.env['account.invoice.line']

        prop = ir_property_obj.get('property_account_income_categ_id', 'product.category')
        prop_account_id = prop and prop.id or False

        invoice = inv_obj.create({
            'account_id': self.patient_id.partner_id.property_account_receivable_id.id,
            'partner_id': self.patient_id.partner_id.id,
            'patient_id': self.patient_id.id,
            'type': 'out_invoice',
            'name': '-',
            'origin': self.name,
            'currency_id': self.env.user.company_id.currency_id.id,
            'hospital_invoice_type': 'claim',
            'claim_id': self.claim_ids and self.claim_ids[0].id or False,
            'hospitalization_id': self.id
        })
        self.package_invoice_id = invoice.id

        if self.package_id:
            for line in self.package_id.order_line:
                account_id = line.product_id.property_account_income_id.id
                inv_line_obj.create({
                    'name': line.name,
                    'price_unit': line.price_unit,
                    'account_id': account_id or prop_account_id,
                    'quantity': line.product_uom_qty,
                    'discount': line.discount,
                    'uom_id': line.product_uom.id,
                    'product_id': line.product_id.id,
                    'account_analytic_id': False,
                    'invoice_id': invoice.id,
                })


class InsuranceClaim(models.Model):
    _name = 'hms.insurance.claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Claim'

    @api.multi
    def _get_diff(self):
        for claim in self:
            claim.amount_difference = claim.amount_requested - claim.amount_pass
            claim.amount_total = claim.amount_received + claim.amount_tds

    @api.model
    def _default_insu_checklist(self):
        vals = []
        checklists = self.env['hms.insurance.checklist.template'].search([('active', '=', True)])
        for checklist in checklists:
            vals.append((0, 0, {
                'name': checklist.name,
            }))
        return vals

    @api.depends('checklist_ids')
    def _compute_checklist_ids_marked(self):
        for rec in self:
            done_checklist = rec.checklist_ids.filtered(lambda x: x.is_done)
            if len(rec.checklist_ids) >=1 :
                rec.checklist_marked = (len(done_checklist)* 100)/len(rec.checklist_ids)


    name = fields.Char('Claim Number', required=True, default="/", 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    patient_id = fields.Many2one('hms.patient', 'Patient', required=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    hospitalization_id = fields.Many2one('acs.hospitalization', 'Hospitalization', required=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    insurance_company_id = fields.Many2one('hms.insurance.company', 'Insurance Company', required=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    policy_number = fields.Char('Policy Number', required=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    amount_requested = fields.Float('Total Claim Amount', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    amount_pass = fields.Float('Passed Amount', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    amount_received = fields.Float('Received Amount', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    amount_difference = fields.Float(compute='_get_diff', string='Difference Amount', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    amount_tds = fields.Float('TDS Amount', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    amount_total = fields.Float(compute='_get_diff', string='Total Amount', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    date = fields.Datetime(string='Claim Date', 
        default=fields.Datetime.now, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    date_received = fields.Date('Claim Received Date', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    tpa_id = fields.Many2one('insurance.tpa', 'TPA', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    req_document_ids = fields.Many2many('hms.insurance.req.doc', 'hms_insurance_req_doc_rel', 'claim_id', 'doc_id', 'Required Documents', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    question = fields.Text('Question', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    answer = fields.Text('Answer', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('sent', 'Sent For Approval'),
        ('approve', 'Approved'),
        ('received', 'Received'),
        ('cancel', 'Cancelled'),
        ('done', 'Done')], 'State', default='draft')
    doc_ids = fields.One2many(comodel_name='ir.attachment', inverse_name='claim_id', string='Document', 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    checklist_ids = fields.One2many('hms.insurance.checklist', 'claim_id', string='Checklist', default=lambda self: self._default_insu_checklist(), 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    package_id = fields.Many2one('hospitalization.package', related="hospitalization_id.package_id", string='Package', 
        readonly=True)
    checklist_marked = fields.Float('Checklist Progress', compute='_compute_checklist_ids_marked',store=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    max_exit_value = fields.Float(default=100.0, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('hms.insurance.claim') or 'New Claim'
        return super(InsuranceClaim, self).create(values)

    @api.multi
    def unlink(self):
        for data in self:
            if data.state in ['done']:
                raise UserError(('You can not delete record in done state'))
        return super(InsuranceClaim, self).unlink()

    @api.onchange('package_id')
    def onchange_package_id(self):
        if self.package_id:
            self.amount_requested = self.package_id.amount_total

    @api.one
    def action_done(self):
        self.date_received = fields.Date.today()
        self.state = 'done'

    @api.one
    def action_draft(self):
        self.state = 'draft'

    @api.one
    def action_confirm(self):
        self.state = 'confirm'

    @api.one
    def action_sent(self):
        self.state = 'sent'

    @api.one
    def action_approve(self):
        self.state = 'approve'

    @api.one
    def action_received(self):
        self.state = 'received'

    @api.one
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_view_invoice(self):
        invoices = self.env['account.invoice'].search([('hospital_invoice_type', '=', 'claim'), ('claim_id', '=', self.id)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action