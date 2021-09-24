from odoo import api, fields, models, _, tools
import requests
import xmlrpc.client
import json
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)



class CrmLead(models.Model):
    _inherit = 'crm.lead'


    @api.depends('order_ids.state', 'order_ids.currency_id', 'order_ids.amount_untaxed', 'order_ids.date_order', 'order_ids.company_id')
    def _compute_sale_data(self):
        for lead in self:
            total = 0.0
            quotation_cnt = 0
            sale_order_cnt = 0
            company_currency = lead.company_currency or self.env.company.currency_id
            for order in lead.order_ids:
                if order.state in ('sent'):
                    quotation_cnt += 1
                if order.state not in ('draft', 'approve', 'sent', 'cancel'):
                    sale_order_cnt += 1
                    total += order.currency_id._convert(
                        order.amount_untaxed, company_currency, order.company_id, order.date_order or fields.Date.today())
            lead.sale_amount_total = total
            lead.quotation_count = quotation_cnt
            lead.sale_order_count = sale_order_cnt
            _logger.info("quotation_count=== '" + str(lead.quotation_count) + "' ok !")


    def action_view_sale_quotation(self):
        action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
        action['context'] = {
            'search_default_draft': 1,
            'search_default_partner_id': self.partner_id.id,
            'default_partner_id': self.partner_id.id,
            'default_opportunity_id': self.id
        }
        action['domain'] = [('opportunity_id', '=', self.id), ('state', 'in', ['sent'])]
        quotations = self.mapped('order_ids').filtered(lambda l: l.state in ('sent'))
        if len(quotations) == 1:
            action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
            action['res_id'] = quotations.id
        return action
