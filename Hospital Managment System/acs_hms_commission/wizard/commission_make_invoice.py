# -*- coding: utf-8 -*-

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class CommissionInvoice(models.TransientModel):
    _name = "commission.invoice"
    _description = "Timesheet Invoice"

    @api.model
    def _get_default_journal(self):
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', self.env.user.company_id.id),
        ]
        default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        return default_journal_id.id and default_journal_id or False


    groupby_partner  = fields.Boolean(string='Groupby Partner', default=False,
        help='Set true if want to create single invoice for project')
    print_commission = fields.Boolean(string='Add Commision no in Description', default=False,
        help='Set true if want to append SO in invoice line Description')
    journal_id = fields.Many2one('account.journal', default=_get_default_journal, required=True)

    @api.multi
    def create_invoice(self, line):
        inv_obj = self.env['account.invoice']
        invoice = inv_obj.create({
            'type': 'in_invoice',
            'reference': False,
            'account_id': line.partner_id.property_account_payable_id.id,
            'partner_id': line.partner_id.id,
            'journal_id': self.journal_id.id,
        })
        return invoice

    @api.multi
    def create_invoice_line(self, line, invoice, product_id, print_commission=False):
        inv_line_obj = self.env['account.invoice.line']

        account_id = product_id.property_account_income_id or product_id.categ_id.property_account_income_categ_id
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (product_id.name,))
        name = product_id.name

        if print_commission:
            name = name + ': ' + line.name

        res = inv_line_obj.create({
            'invoice_id': invoice.id,
            'name': name,
            #'origin': ,
            'account_id': account_id.id,
            'price_unit': line.commission_amount,
            'quantity': 1,
            'discount': 0.0,
            'uom_id': product_id.uom_id.id,
            'product_id': product_id.id,
            'invoice_line_tax_ids': [(6, 0, product_id.supplier_taxes_id and product_id.supplier_taxes_id.ids or [])],
        })
        return res

    @api.multi
    def create_invoices(self):
        Commission = self.env['acs.hms.commission']
        groupby = False
        invoices = []
        product_id = self.env.user.company_id.commission_product_id
        if not product_id:
            raise UserError(_('Please set Commission Product in company first.'))
        if self.groupby_partner:
            groupby = 'partner_id'
        if groupby:
            commission_group = Commission.read_group([('id', 'in', self._context.get('active_ids', [])),
                ('invoice_line_id', '=', False)] , fields=[groupby], groupby=[groupby])
            for group in commission_group:
                domain = [('id', 'in', self._context.get('active_ids', [])),
                    ('invoice_line_id', '=', False)]
                if group[groupby]:
                    domain += [(groupby, '=', int(group[groupby][0]))]
                lines = Commission.search(domain)
                if lines:
                    invoice = self.create_invoice(lines[0])
                    invoices.append(invoice.id)
                    for line in lines:
                        line_rec = self.create_invoice_line(line, invoice, product_id, self.print_commission)
                        line.invoice_line_id = line_rec.id
                    invoice.compute_taxes()

        else:
            lines = Commission.browse(self._context.get('active_ids', []))
            for line in lines:
                if not line.invoice_line_id:
                    invoice = self.create_invoice(line)
                    invoices.append(invoice.id)
                    line_rec = self.create_invoice_line(line, invoice, product_id, self.print_commission)
                    invoice.compute_taxes()
                    line.invoice_line_id = line_rec.id
        if not invoices:
            raise UserError(_('Please check there is nothing to invoice in selected Commission may be you are missing partner or trying to invoice already invoiced Commissions.'))
        if self._context.get('open_invoices', False):
            action = self.env.ref('account.action_vendor_bill_template').read()[0]
            if len(invoices) > 1:
                action['domain'] = [('id', 'in', invoices)]
            elif len(invoices) == 1:
                action['views'] = [(self.env.ref('account.invoice_supplier_form').id, 'form')]
                action['res_id'] = invoices[0]
            else:
                action = {'type': 'ir.actions.act_window_close'}
            return action
        return {'type': 'ir.actions.act_window_close'}
