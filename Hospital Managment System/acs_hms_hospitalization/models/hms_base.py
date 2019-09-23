# -*- encoding: utf-8 -*-
from odoo import api, fields, models,_


class ResCompany(models.Model):
    _inherit = "res.company"

    usage_location = fields.Many2one('stock.location', 
        string='Usage Location for Consumed Products')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict", string='Hospitalization',
        help="Enter the patient hospitalization code")

 
class inpatient_prescription(models.Model):
    _inherit = 'prescription.order'

    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict", string='Hospitalization',help="Enter the patient hospitalization code",
        states={'cancel': [('readonly', True)], 'prescription': [('readonly', True)]})
    ward_id = fields.Many2one('hospital.ward',string='Ward/Room No.', ondelete="restrict",
        states={'cancel': [('readonly', True)], 'prescription': [('readonly', True)]})
    bed_id = fields.Many2one("hospital.bed",string="Bed No.", ondelete="restrict",
        states={'cancel': [('readonly', True)], 'prescription': [('readonly', True)]})
 

class ACSAppointment(models.Model):
    _inherit = 'hms.appointment'

    hospitalization_id = fields.Many2one('acs.hospitalization', ondelete="restrict", string='Hospitalization', help="Enter the patient hospitalization code",invisible=True, 
        states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})

    @api.multi
    def button_hospitalize(self):
         return {
            'name': _('Hospitalizations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'acs.hospitalization',
            'type': 'ir.actions.act_window',
            'domain': [('patient_id','=',self.patient_id.id)],
            'context': {'default_patient_id': self.patient_id.id,'default_appointment_id': self.id},
        }


class ACSPatient (models.Model):
    _inherit = "hms.patient"
    
    past_surgeries_ids = fields.One2many('past.surgeries', 'patient_id', string='Past Surgerys')

    @api.multi
    def action_view_surgery(self):
        action = self.env.ref('acs_hms_hospitalization.act_open_action_form_surgery').read()[0]
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id}
        return action

    @api.multi
    def action_hospitalization(self):
        action = self.env.ref('acs_hms_hospitalization.acs_action_form_inpatient').read()[0]
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id}
        return action
