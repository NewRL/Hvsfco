# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.translate import _


class product_template(models.Model):
    _inherit = "product.template"

    # @api.model
    # def _get_default_form(self):
    #     form_id = self.env['drug.form'].search([], limit=1)
    #     return form_id and form_id.id or False

    form_id = fields.Many2one('drug.form', ondelete='cascade', string='Drug Form', 
        track_visibility='onchange')#, default=_get_default_form)
    active_component_ids = fields.Many2many('active.comp', 'product_active_comp_rel', 'product_id','comp_id','Active Component')
    drug_company_id = fields.Many2one('drug.company', ondelete='cascade', string='Drug Company', help='Company producing this drug')    
    lactation = fields.Boolean('Lactation')
    hospital_product_type = fields.Selection([
            ('medicament','Medicament'),
            ('bed', 'Bed'), 
            ('vaccine', 'Vaccine'),
            ('insurance_plan', 'Insurance Plan'),
            ('surgery', 'Surgery'),
            ('procedure', 'Procedure'),
            ('fdrinks', 'Food & Drinks'),
            ('pathology', 'Pathology'), 
            ('radiology', 'Radiology'),
            ('consultation','Consultation'),
            ('os', 'Other Service')
        ], string="Hospital Product Type", default='medicament')
    active_component_ids = fields.Many2many('active.comp','product_act_comp_rel',
        'medica_id','product_id',string='Active Component')
    indications = fields.Text(string='Indication', help='Indications') 
    therapeutic_action = fields.Char(size=256, string='Therapeutic Effect', help='Therapeutic action')
    overdosage = fields.Char(string='Overdosage', help='Overdosage')
    pregnancy_warning = fields.Boolean(string='Pregnancy Warning',
        help='The drug represents risk to pregnancy or lactancy')
    notes = fields.Text(string='Extra Info')
    storage = fields.Char(string='Storage')
    adverse_reaction = fields.Char(string='Adverse Reactions')
    dosage = fields.Float(string='Dosage', help='Dosage')
    pregnancy = fields.Text(string='Pregnancy and Lactancy',
        help='Warnings for Pregnant Women')
    route = fields.Many2one('drug.route', ondelete='cascade', 
        string='Route', help='')
    form = fields.Many2one('drug.form', ondelete='cascade', 
        string='Form',help='Drug form, such as tablet or gel')
    common_dosage = fields.Many2one('medicament.dosage', ondelete='cascade',
        string='Frequency', help='Drug form, such as tablet or gel')
