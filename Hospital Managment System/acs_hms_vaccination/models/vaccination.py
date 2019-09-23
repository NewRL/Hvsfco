#-*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta as td
from odoo.exceptions import UserError


class VaccinationGroupLine(models.Model):
    _name = 'vaccination.group.line'
    _description = "Vaccination Group Line"

    group_id = fields.Many2one('vaccination.group', 'Group')
    product_id = fields.Many2one('product.product', 'Product', required=True)
    date_due_day = fields.Integer('Days to add',help="Days to add for next date")


class VaccinationGroup(models.Model):
    _name = 'vaccination.group'
    _description = "Vaccination Group"

    name = fields.Char(string='Group Name', required=True)
    group_line = fields.One2many('vaccination.group.line', 'group_id', string='Medicament line')


class ACSPatient(models.Model):
    _inherit = 'hms.patient'

    vaccination_group_id = fields.Many2one('vaccination.group',string='Vaccination Group', ondelete="restrict")
    vaccination_line = fields.One2many('acs.vaccination','patient_id', 'Vaccination')
    vaccination_on_dob = fields.Boolean('Schedule on DOB')

    @api.onchange('vaccination_group_id')
    def onchange_vaccination_group_id(self):
        product_lines = []
        Line = self.env['acs.vaccination']
        base_date = fields.Date.from_string(fields.Date.today())
        if self.vaccination_on_dob:
            if not self.dob:
                raise UserError(_('Please set Date Of Birth first.'))
            base_date = fields.Date.from_string(self.dob)

        for line in self.vaccination_group_id.group_line:
            days = line.date_due_day
            self.vaccination_line += Line.new({
                'product_id': line.product_id.id,
                'patiend_id': self.id, 
                'due_date': (base_date+ td(days=days)),
                'state': 'sheduled',
            })


class ACSVaccination(models.Model):
    _name = 'acs.vaccination'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Vaccination"

    name = fields.Char(size=256, string='Name')
    vaccine_lot = fields.Char(size=256, string='Lot Number',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
        help='Please check on the vaccine (product) production lot numberand'\
        ' tracking number when available !')
    patient_id = fields.Many2one('hms.patient', string='Patient', required=True,
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    product_id = fields.Many2one('product.product', 'Vaccination', required=True, domain=[('hospital_product_type', '=', "vaccination")],
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},
        help='Vaccine Name. Make sure that the vaccine (product) has all the'\
        ' proper information at product level. Information such as provider,'\
        ' supplier code, tracking number, etc.. This  information must always'\
        ' be present. If available, please copy / scan the vaccine leaflet'\
        ' and attach it to this record')
    dose = fields.Integer(string='Dose #',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},)
    observations = fields.Char(string='Observations',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},)
    next_dose_date = fields.Datetime(string='Next Dose Date',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},)
    due_date = fields.Date('Due Date',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},)
    given_date = fields.Date('Given Date',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},)
    batch_image = fields.Binary('Batch Photo',
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]},)
    state = fields.Selection([
            ('sheduled', 'Sheduled'),
            ('to_invoice', 'To Invoice'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
        ], string='State', default='sheduled')
    invoice_id = fields.Many2one('account.invoice', string='Invoice', ondelete='cascade')
    physician_id = fields.Many2one('hms.physician', ondelete='restrict', string='Physician', 
        index=True, states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    @api.one
    def action_done(self):
        if self.env.user.company_id.vaccination_invoicing:
            self.state = 'to_invoice'
        else:
            self.state = 'done'
        self.given_date = fields.Date.today()

    @api.one
    def action_cancel(self):
        self.state = 'cancel'

    @api.one
    def action_shedule(self):
        self.state = 'sheduled'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ['cancel']:
                raise UserError(_('Record can be deleted only in Cancelled state.'))
        return super(ACSVaccination, self).unlink()
 
    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('acs.vaccination') or 'New Vaccination'
        return super(ACSVaccination, self).create(values)

    @api.multi
    def action_create_invoice(self):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        inv_line_obj = self.env['account.invoice.line']
        account_id =  False
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

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: