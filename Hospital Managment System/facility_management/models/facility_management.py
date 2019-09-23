# -*- encoding: utf-8 -*-

from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
import calendar

class FacilityActivity(models.Model):
    _name = 'facility.activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Facility Activity'
    _order = 'id desc'

    name = fields.Char(size=256, string='Sequence')
    activity_name = fields.Char('Activity Name', required="True")
    date_activity = fields.Date('Date')
    assigned_id = fields.Many2one('res.users','Assigned To', help="Name of the reviewer who is Assigned the Activity", ondelete="restrict")
    reviewer_id = fields.Many2one('res.users','Reviewer', help="Name of the reviewer who is reviewing the Activity", ondelete="restrict")
    date_review = fields.Date('Reviewer Date', readonly="True")
    state = fields.Selection([('draft','Draft'),('done','Done')], 'Status', default="draft", track_visibility='onchange') 
    remark = fields.Text('Remark')

    @api.model
    def create(self, values):
        if values.get('name', '') == '':
            values['name'] = self.env['ir.sequence'].next_by_code('facility.activity') or ''
        return super(FacilityActivity, self).create(values)

    @api.multi
    def action_done(self):
        self.date_review = fields.Date.today()
        self.reviewer_id =  self.env.user.id
        self.state = 'done'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete an record which is not draft or cancelled.'))
        return super(FacilityActivity, self).unlink()

      
class FacilityMaster(models.Model):
    _name = 'facility.master'
    _description = "Facility Master"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'


    name = fields.Char(size=256, string='Sequence')
    facility_name = fields.Char('Name', required="True")
    reviewer_id = fields.Many2one('res.users','Reviewer', help="Name of the reviewer who is reviewing the task", ondelete="restrict")
    time_type = fields.Selection([('daily','Daily'),('days','2 Days'),('weekly','Weekly'),('monthly','Monthly')], 'Type', default="daily")
    responsible_id = fields.Many2one('res.users','Responsible', help="Name of the person who is responsible for the task", ondelete="restrict")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    next_execution_date = fields.Date('Next Execution Date')
    state = fields.Selection([('draft','Draft'),('running','Running'),('done','Done'),('cancel','Cancel')], 'Status', default="draft", track_visibility='onchange')
    remark = fields.Text('Remark')

    @api.model
    def create(self, values):
        if values.get('name', '') == '':
            values['name'] = self.env['ir.sequence'].next_by_code('facility.master') or ''
        return super(FacilityMaster, self).create(values) 

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError(_('You cannot delete an record which is not draft or cancelled.'))
        return super(FacilityMaster, self).unlink()

    @api.multi
    def action_running(self):
        self.state = 'running'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_done(self):
        self.state = 'done'

    @api.model
    def create_facility_activity(self):
        activity_obj = self.env['facility.activity']
        today = date.today()
        master_data_ids = self.search([
            ('start_date', '<=', fields.date.today()), '|',
            ('end_date', '>', fields.date.today()), ('end_date', '=', False),
            ('state', '=', 'running'),
            '|', ('next_execution_date','=',False),
                ('next_execution_date','=',fields.date.today())
            ])
        for master in master_data_ids: 
            time_type = master.time_type
            if time_type == 'daily':
                start_date = today
                master.next_execution_date = master.start_date + timedelta(days=1)

            elif time_type == 'days':
                start_date = today - timedelta(days=today.weekday())
                master.next_execution_date = master.start_date + timedelta(days=2)

            elif time_type == 'weekly':
                start_date = today - timedelta(days=today.weekday())
                master.next_execution_date = master.start_date + timedelta(days=7)

            elif time_type == 'monthly':
                month_range = calendar.monthrange(today.year, today.month)
                start_date = today.replace(day=1)
                master.next_execution_date = today.replace(day=month_range[1])

            activity_obj.create({
                'activity_name': master.facility_name,
                'date_activity': start_date,
                'assigned_id': master.responsible_id.id,
                'reviewer_id': master.reviewer_id.id
            })

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: