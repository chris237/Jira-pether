''' 
from odoo import fields, api, models, tools
from datetime import date
import time
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from calendar import monthrange
from operator import itemgetter

class payroll_advice_report(models.AbstractModel):
    _name = 'report.client_pi.report_journal_entry'
    _description = "Report Journal Entry"
    
    def get_detail(self, line_ids):
        result = []
        for l in line_ids:
            res = {}
            res.update({
                    'account_id': l.account_id,
                    'partner_id': l.partner_id,
                    'name': l.name,
                    'debit': l.debit,
                    'credit': l.credit,
                    })
            result.append(res)
        #result = sorted(result, key=itemgetter('account_id'))
        return result
    
    @api.model
    def _get_report_values(self, docids, data=None):
        journal_entry = self.env['account.move'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.move',
            'data': data,
            'docs': journal_entry,
            'get_detail': self.get_detail(),
        } '''
        
from odoo import api, models
class accountdeitjournal(models.Model):
    _inherit = "account.move"

    def total_debit_credit(self):
        res = {}
        for move in self:
            dr_total = 0.0
            cr_total = 0.0
            for line in move.line_ids:
                dr_total += line.debit
                cr_total += line.credit
            dr_total = round(dr_total, 2)
            cr_total = round(cr_total, 2)
            res.update({'cr_total': cr_total, 'dr_total': dr_total})
        return res