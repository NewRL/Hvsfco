# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class Patient(models.Model):
    _inherit = "hms.patient"

    @api.multi
    def _acs_get_attachemnts(self):
        AttachmentObj = self.env['ir.attachment']
        attachments = AttachmentObj.search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id)])
        attachments += self.appointment_ids.mapped('attachment_ids')
        return attachments

    @api.multi
    def _acs_attachemnt_count(self):
        AttachmentObj = self.env['ir.attachment']
        for rec in self:
            attachments = rec._acs_get_attachemnts()
            rec.attach_count = len(attachments)
            rec.attachment_ids = [(6,0,attachments.ids)]

    attach_count = fields.Integer(compute="_acs_attachemnt_count", readonly=True, string="Documents")
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_patient_rel', 'patient_id', 'attachment_id', compute="_acs_attachemnt_count", string="Attachments")

    @api.multi
    def action_view_attachments(self):
        self.ensure_one()
        domain = [('id', 'in', self.attachment_ids.ids)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Documents are attached to the record.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_is_document': True}" % (self._name, self.id)
        }


class HmsAppointment(models.Model):
    _inherit = "hms.appointment"

    @api.multi
    def _acs_attachemnt_count(self):
        AttachmentObj = self.env['ir.attachment']
        for rec in self:
            attachments = AttachmentObj.search([
                ('res_model', '=', self._name),
                ('res_id', '=', rec.id)])
            rec.attachment_ids = [(6,0,attachments.ids)]
            rec.attach_count = len(attachments.ids)

    attach_count = fields.Integer(compute="_acs_attachemnt_count", readonly=True, string="Documents")
    attachment_ids = fields.Many2many('ir.attachment', 'attachment_patient_rel', 'appointment_id', 'attachment_id', compute="_acs_attachemnt_count", string="Attachments")

    @api.multi
    def action_view_attachments(self):
        self.ensure_one()
        domain = [('id', 'in', self.attachment_ids.ids)]
        return {
            'name': _('Documents'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'help': _('''<p class="o_view_nocontent_smiling_face">
                        Documents are attached to the record.
                    </p>'''),
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d, 'default_is_document': True}" % (self._name, self.id)
        }