# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT


class AppointmentSchedulerWizard(models.TransientModel):
    _name = 'appointment.scheduler.wizard'
    _description = 'Appointment Shedular Wiz'

    @api.multi
    def _check_dates(self):
        for wizard in self:
            if wizard.start_date > wizard.end_date:
                return False
        return True
    
    schedule_id = fields.Many2one("appointment.schedule", string="Appointment schedule", required=True, ondelete="cascade")
    start_date = fields.Date('Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date('End Date',required=True) 
    
    _constraints = [(_check_dates, "Scheduler 'Start Date' must be before 'End Date'.", ['start_date', 'end_date'])]
    
    @api.multi
    def appointment_slot_create_wizard(self):
        Slot = self.env['appointment.schedule.slot']
        cron = self.env['ir.model.data'].get_object('acs_hms_online_appointment', 'ir_cron_create_slot')
        
        # create slot
        start_date = self.start_date
        end_date = self.end_date

        while (start_date != end_date + timedelta(days=1)):
            slot_found = Slot.search([('slot_date','=',start_date.strftime(DEFAULT_SERVER_DATE_FORMAT))])
            if slot_found:
                raise UserError(_("Appointment Slot exist for date %s." % start_date.strftime(DEFAULT_SERVER_DATE_FORMAT)))
            Slot.create_appointment_slot(start_date, self.schedule_id)
            start_date = start_date  + timedelta(days=1)
        end_scheduler =(end_date - timedelta(days=7)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        cron.write({'nextcall':end_scheduler})
