# -*- encoding: utf-8 -*-
from odoo import api, fields, models,_
from datetime import datetime
from datetime import timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT


class ResCompany(models.Model):
    _inherit = "res.company"

    allowed_booking_online_days = fields.Integer("Allowed Advance Booking Days", help="No of days for which advance booking is allowed", default=7)
    booking_slot_time = fields.Integer("Minutes in each slot", help="Configure your slot length, 15-30min.", default=15)
    allowed_booking_per_slot = fields.Integer("Allowed Booking per Slot", help="No of allowed booking per slot.", default=4)
    allowed_booking_payment = fields.Boolean("Allowed Advance Booking Payment", help="Allow user to do online Payment", default=False)


class Appointment(models.Model):
    _inherit = 'hms.appointment'

    @api.multi
    @api.depends('date')
    def _get_schedule_date(self):
        for rec in self:
            rec.schedule_date = rec.date.date()

    schedule_date = fields.Date(string='Schedule Date', compute="_get_schedule_date", store=True)
    schedule_slot_id = fields.Many2one('appointment.schedule.slot.lines', string = 'Schedule Slot')
    booked_online = fields.Boolean('Booked Online')

    @api.model
    def clear_appointment_cron(self):
        if self.env.user.company_id.allowed_booking_payment:
            appointments = self.search([('booked_online','=', True),('invoice_id.state','!=','paid'),('state','=','draft')])
            for appointment in appointments:
                #cancel appointment after 20 minute if not paid
                create_time = appointment.create_date + timedelta(minutes=20)
                if create_time <= datetime.now():
                    appointment.invoice_id.action_invoice_cancel()
                    appointment.state = 'cancel'


class HrDepartment(models.Model):
    _inherit = "hr.department"

    allowed_online_booking = fields.Boolean("Allowed Online Booking", default=False)
