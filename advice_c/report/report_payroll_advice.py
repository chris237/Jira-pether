# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from operator import itemgetter
import time

from odoo import api, models


class move_advi_report(models.AbstractModel):
    _name = 'report.advice_c.report_moveadvi'
    _description = "Payement Advice Report"

    def get_month(self, input_date):
        res = {
               'from_name': '', 'to_name': ''
               }
        slip = self.env['account.move'].search([('date_from', '<=', input_date), ('date_to', '>=', input_date)], limit=1)
        if slip:
            from_date = slip.date_from
            to_date = slip.date_to
            res['from_name'] = from_date.strftime('%d') + '-' + from_date.strftime('%B') + '-' + from_date.strftime('%Y')
            res['to_name'] = to_date.strftime('%d') + '-' + to_date.strftime('%B') + '-' + to_date.strftime('%Y')
        return res

    def get_bysal_total(self):
        return self.total_bysal

    def get_detail(self, line_ids):
        result = []
        self.total_bysal = 0.00
        for l in line_ids:
            res = {}
            res.update({
                    'pay': l.pay.name,
                    'name': l.partner_id.name,
                    'chequ': l.chequ,
                    'comm': l.comm,
                    'bysal': l.bysal,
                    })
            self.total_bysal += l.bysal
            result.append(res)
        result = sorted(result, key=itemgetter('chequ'))
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        advice = self.env['account.move.advi'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move.advi',
            'data': data,
            'docs': advice,
            'time': time,
            'get_month': self.get_month,
            'get_detail': self.get_detail,
            'get_bysal_total': self.get_bysal_total,
        }
