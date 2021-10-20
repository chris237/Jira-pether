# Copyright 2021 Pether Solutions - Elvige MEKONE <elvige.mekone@pether.io>

from odoo import api, fields, models,_, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime
import time
import calendar
from datetime import date
import json
import requests
from operator import itemgetter
import itertools
from itertools import groupby
from json import dumps
from itertools import zip_longest
from hashlib import sha256  
from datetime import date
from datetime import timedelta

from collections import defaultdict
import re
import logging
_logger = logging.getLogger(__name__)

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}
class AccountLedgerReport(models.Model):
    '''
    Account Ledger Report
    '''
    _name = 'account.ledger.report'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Ledger Report"
    _order = "id desc, date desc"
    _rec_name ='account_id'

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())
    
    date = fields.Date(readonly=True , index=True, tracking=True, required=True, string='Date', states={'draft': [('readonly', False)]}, default=_get_default_date)
    date_from = fields.Date(readonly=True, string='From', required=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date(readonly=True, string='To', required=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', index=True, tracking=True, readonly=True)
    line_ids = fields.One2many('account.ledger.report.line', 'ledger_report_id', string='Ledger Report' , index=True, copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True)    
    account_id = fields.Many2one('account.account', string='Name account',required=True)
 
    def compute(self):
        results = []
        deb=cred=bal= 0
        total_deb=total_cred=total_bal=0.0
        move_lines = self.env['account.move.line'].search([('parent_state', '=', 'posted'),('account_id', '=', self.account_id.id)])
        for move_lin in move_lines:
            date_en_cours = fields.Date.from_string(fields.Date.today())
            years = date_en_cours.year
            from_year = self.date_from.year
            dateyear = move_lin.date.year
            #solde initial

            if years == dateyear and years == from_year:
                if move_lin.date < self.date_from:
                    deb = move_lin.debit
                    cred = move_lin.credit
                    bal = deb - cred
                
                total_deb += deb
                total_cred += cred
                total_bal += bal

                # _logger.info("total_deb=== '" + str(total_deb) + "' ok !")
            
        val = {
            'move_name':"initial balance",  
            'debit':total_deb,
            'credit':total_cred,
            'balance':total_bal,
            'ledger_report_id':self.id
        }


        for move_line in move_lines:
        
            if self.date_from <= move_line.date <= self.date_to:
                res=({
                    'move_line1': move_line.id,
                    'move_name1':move_line.move_name,  
                    'id_move1': move_line.move_id.id,
                    'date1':move_line.date, 
                    'ledger_report_id1':self.id,
                    'communication1':move_line.ref,
                    'partner1':move_line.partner_id.name,
                    'account1': move_line.account_id.code,
                    'debit1':move_line.debit,
                    'credit1':move_line.credit,
                    'balance1':move_line.debit - move_line.credit
                    # 'balance1':move_line.balance
                })
                results.append(res)


       
        def keyfun(x):
            return x['id_move1']
        lineGroups = itertools.groupby(results, keyfun)
        line = self.env['account.ledger.report.line'].create(val) 
        for resu in lineGroups:
            move_id2 = resu[0]
            line_moves = resu[1]
            debs=creds=bals=0
            for line_move in line_moves:
                debs += line_move['debit1']
                creds += line_move['credit1']
                bals += line_move['balance1']

            total_bal += debs - creds
                
           
            line = self.env['account.ledger.report.line'].create({
                    'move_line': line_move['move_line1'],
                    'move_name':line_move['move_name1'],  
                    'date':line_move['date1'], 
                    'ledger_report_id':line_move['ledger_report_id1'],
                    'communication':line_move['communication1'],
                    'partner':line_move['partner1'],
                    'account': line_move['account1'],
                    'debit':debs,
                    'credit':creds,
                    'balance':total_bal
                    })   
        self.confirm_sheet()

    def confirm_sheet(self):
        """
        confirm Ledger report  - confirmed ledger report after computing ledger Lines..
        """
        for ledger in self:
            if not ledger.line_ids:
                raise UserError(_('You can not generate ledger report without ledger lines because the invoices do not exist for this account or it has already been generated.'))
            date = fields.Date.from_string(fields.Date.today())
            for line in ledger.line_ids:
                line.move_line.ledgerr = True
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('ledger.report')   
            ledger.write({
                'number': 'LEDGER' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })  
            # _logger.info("youpiii")

    def set_to_draft(self):
        """Resets Ledger report as draft.
        """
        self.write({'state': 'draft'})

    def cancel_sheet(self):
        """Marks Ledger report as cancelled.
        """
        self.write({'state': 'cancel'})

    
class AccountLedgerReportLine(models.Model):
    '''
    Bank ledger report Lines
    '''
    _name = 'account.ledger.report.line'
    _description = 'Ledger Report Lines'
    
    ledger_report_id = fields.Many2one('account.ledger.report', string='Ledger report', ondelete="cascade")
    account_id = fields.Many2one('account.account', string='Name account')
    move_name = fields.Char(string='Name')
    account = fields.Char(string='GL Acc')
    date = fields.Date(string='Date')
    communication = fields.Char(string='Detail')
    partner = fields.Char(string='Payee')
    debit = fields.Float(string='Debit', digits='Payroll')
    credit = fields.Float(string='Credit', digits='Payroll')
    balance = fields.Float(string='Balance', digits='Payroll')
    move_line = fields.Many2one('account.move.line', string='move line', required=False)



class ledgerrepo(models.AbstractModel):
    _name = "report.client_pi.report_ledger"
    _template = 'client_pi.report_ledger'
    _description = "ledger Report"

    def get_total_debit (self):
        return self.total_debit
    def get_total_credit(self):
        return self.total_credit
    def get_total_balance(self):
        return self.total_balance           

    def get_detail(self, line_ids):
        result = []
        self.total_debit = 0.00
        self.total_credit = 0.00
        self.total_balance = 0.00
        for l in line_ids:
            res = {}
            res.update({
                    'move_name': l.move_name,  
                    'date': l.date, 
                    'communication': l.communication,
                    'partner': l.partner,
                    'account': l.account,
                    'debit': l.debit,
                    'credit': l.credit,
                    'balance': l.balance
                    })
            self.total_debit += l.debit
            self.total_credit += l.credit
            self.total_balance = l.balance
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        ledger = self.env['account.ledger.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.ledger.report',
            'data': data,
            'docs': ledger,
            'time': time,
            'get_detail': self.get_detail,
            'get_total_debit': self.get_total_debit,
            'get_total_credit': self.get_total_credit,
            'get_total_balance': self.get_total_balance,
        }
