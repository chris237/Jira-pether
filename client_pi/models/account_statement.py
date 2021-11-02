# Copyright 2020 Pether Solutions - Elvige MEKONE <elvige.mekone@pethersolutions.com>

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
import itertools
from operator import itemgetter
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


class AccountStatement(models.Model):
    '''
    Account Statement
    '''
    _name = 'account.statement'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Statement of Account"
    _order = "id desc, date desc"
    _rec_name ='number'

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())
        
    
    date = fields.Date(readonly=True , index=True, tracking=True, required=True, string='Date', states={'draft': [('readonly', False)]}, default=_get_default_date)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft', index=True, tracking=True, readonly=True)
    line_ids = fields.One2many('account.statement.line', 'acc_statement_id', string='Account Statement' , index=True, copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True, default ='/')    
    partner_id = fields.Many2one('res.partner', string='Partner',required=True)
    date_from = fields.Date(readonly=True, string='From', required=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date(readonly=True, string='To', required=True, states={'draft': [('readonly', False)]})
 
    my_date = fields.Date.from_string(fields.Date.today())
    mydate10 = my_date.strftime("%d %B %Y")


    def compute(self):
        results = []
        moves = self.env['account.move'].search([('type', '=', 'out_invoice'),('partner_id', '=', self.partner_id.id)])
        for move in moves:
            m_date0 = move.date
            m_date = m_date0.month
            m_date_y = m_date0.year

            # date of invoice
            if m_date == 1:
                m_mois = "JANUARY"
            if m_date == 2:
                m_mois = "FEBUARY"
            if m_date == 3:
                m_mois = "MARCH"
            if m_date == 4:
                m_mois = "APRIL"
            if m_date == 5:
                m_mois = "MAY"
            if m_date == 6:
                m_mois = "JUNE"
            if m_date == 7:
                m_mois = "JULY"
            if m_date == 8:
                m_mois = "AUGUST"
            if m_date == 9:
                m_mois = "SEPTEMBER"
            if m_date == 10:
                m_mois = "OCTOBER"
            if m_date == 11:
                m_mois = "NOVEMBER"
            if m_date == 12:
                m_mois = "DECEMBER"

            payment_voucher = move.invoice_payments_widget
            payment_voucher = json.loads(payment_voucher)

            if self.date_from <= move.date <= self.date_to: 
                _logger.info("date=== '" + str(move.date)) 
                if payment_voucher:
                    pvs = payment_voucher['content']
                    # _logger.info("pvs=== '" + str(pvs))
                    for pv in pvs:
                        state = self.env['account.payment'].search([('id', '=', pv['account_payment_id'])]).state
                        if state != "draft":
                            date_paid = self.env['account.payment'].search([('id', '=', pv['account_payment_id'])]).payment_date
                            amount_paid = self.env['account.payment'].search([('id', '=', pv['account_payment_id'])]).amount
                        else:
                            raise ValidationError("Partner has his payment in draft state") 
                
                        
                        p_date = date_paid.month
                        p_date_y = date_paid.year
                        # date of payment invoice
                        if p_date == 1:
                            p_mois = "JANUARY"
                        if p_date == 2:
                            p_mois = "FEBUARY"
                        if p_date == 3:
                            p_mois = "MARCH"
                        if p_date == 4:
                            p_mois = "APRIL"
                        if p_date == 5:
                            p_mois = "MAY"
                        if p_date == 6:
                            p_mois = "JUNE"
                        if p_date == 7:
                            p_mois = "JULY"
                        if p_date == 8:
                            p_mois = "AUGUST"
                        if p_date == 9:
                            p_mois = "SEPTEMBER"
                        if p_date == 10:
                            p_mois = "OCTOBER"
                        if p_date == 11:
                            p_mois = "NOVEMBER"
                        if p_date == 12:
                            p_mois = "DECEMBER"       
                        
                        res=({
                            'acc_statement_id1':self.id,
                            'partner_id1':move.partner_id.id,
                            'invoice_date1':m_mois + ','+str(m_date_y), 
                            'amount_bill1':move.amount_total,  
                            'payment_month1':p_mois+ ','+str(p_date_y), 
                            'amount_paid1':amount_paid,
                            'outstand_bal1':move.amount_residual,
                            'move1': move.id
                        })
                        results.append(res)
       
                else:
                    res=({
                        'acc_statement_id1':self.id,
                        'partner_id1':move.partner_id.id,
                        'invoice_date1':m_mois + ','+str(m_date_y), 
                        'amount_bill1':move.amount_total,  
                        'payment_month1':" ", 
                        'amount_paid1':0,
                        'outstand_bal1':move.amount_residual,
                        'move1': move.id
                    })
                    results.append(res)

        def keyfun(x):
            return x['move1']
        lineGroups = itertools.groupby(results, keyfun)
        for resu in lineGroups:
            move2 = resu[0]
            line_moves = resu[1]
            amount_paids=outstand_bals=0
            for line_move in line_moves:
                amount_paids += line_move['amount_paid1']
                outstand_bals += line_move['outstand_bal1']                   
                    
            line = self.env['account.statement.line'].create({
                'acc_statement_id':line_move['acc_statement_id1'],
                'partner_id':line_move['partner_id1'],
                'invoice_date':line_move['invoice_date1'], 
                'amount_bill':line_move['amount_bill1'],  
                'payment_month':line_move['payment_month1'], 
                'amount_paid':amount_paids,
                'outstand_bal':outstand_bals,
                'move': line_move['move1']
                })
        self.confirm_sheet()

    def confirm_sheet(self):
        """
        confirm account statement  - confirmed account statement after computing statement Lines..
        """
        for statement in self:
            if not statement.line_ids:
                raise UserError(_('You can not generate account statement without statement lines because the invoices do not exist for this customer.'))
            date = fields.Date.from_string(fields.Date.today())
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('payment.statement')    
            statement.write({
                'number': 'STATEMENT' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })  

    
class AccountStatementLine(models.Model):
    '''
    Account Statement Lines
    '''
    _name = 'account.statement.line'
    _description = 'Account Statement Lines'
    
    acc_statement_id = fields.Many2one('account.statement', string='Account Statement', ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string='Partner')
    invoice_date = fields.Char(string='Invoice Date')
    amount_bill = fields.Float(string='Total Bill')
    payment_month = fields.Char(string='Payment Month')
    amount_paid = fields.Float(string='Payment')
    outstand_bal = fields.Float(string='Outstanding Bal.')
    move = fields.Many2one('account.move', string='move', required=True)



class accountstat(models.AbstractModel):
    _name = "report.client_pi.report_statement"
    _template = 'client_pi.report_statement'
    _description = "statement account"

    def get_total_amount_bill (self):
        return self.total_amount_bill
    def get_total_amount_paid(self):
        return self.total_amount_paid
    def get_total_outstand(self):
        return self.total_outstand            

    def get_detail(self, line_ids):
        result = []
        self.total_amount_bill = 0
        self.total_amount_paid = 0
        self.total_outstand = 0
        for l in line_ids:
            res = {}
            res.update({
                    'invoice_date': l.invoice_date, 
                    'amount_bill': l.amount_bill, 
                    'payment_month': l.payment_month, 
                    'amount_paid': l.amount_paid,
                    'outstand_bal': l.outstand_bal
                    })
            self.total_amount_bill += l.amount_bill
            self.total_amount_paid += l.amount_paid
            self.total_outstand += l.outstand_bal
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        statement = self.env['account.statement'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.statement',
            'data': data,
            'docs': statement,
            'time': time,
            'get_detail': self.get_detail,
            'get_total_amount_bill': self.get_total_amount_bill,
            'get_total_amount_paid': self.get_total_amount_paid,
            'get_total_outstand': self.get_total_outstand,
        }
