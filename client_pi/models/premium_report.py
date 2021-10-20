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


class PremiumReport(models.Model):
    '''
    Premium Report
    '''
    _name = 'premium.report'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Premium Report"
    _order = "id desc, date desc"


    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())
    
    date = fields.Date(readonly=True , index=True, tracking=True, required=True, string='Date', states={'draft': [('readonly', False)]}, default=_get_default_date)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', index=True, tracking=True, readonly=True)
    line_ids = fields.One2many('premium.report.line', 'premium_report_id', string='Premium Report' , index=True, copy=True, readonly=True,
        domain=[('exclude_from_premium_tab', '=', False)],
        states={'draft': [('readonly', False)]})
    sum_line_ids = fields.One2many('premium.report.line', 'premium_report_id', string='Summary Report' , index=True, copy=True, readonly=True,
        domain=[('exclude_from_sum_tab', '=', False)],
        states={'draft': [('readonly', False)]})    
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True)
    mois = fields.Char(string='Month', index=True, tracking=True)


    def compute(self):
        results = []
        moves = self.env['account.move'].search([('type', '=', "out_invoice"), ('state', '=', "posted")])
        for move in moves:
            payment_voucher = move.invoice_payments_widget
            payment_voucher = json.loads(payment_voucher)
            m_date0 = move.date
            m_date = m_date0.month
            m_day = m_date0.day

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

                    p_date0 = date_paid
                    p_date = p_date0.month
                    p_day = p_date0.day
                    note = self.env['account.move'].search([('type', '=', "out_refund"), ('reversed_entry_id', '=', move.id)]).amount_total
                    if p_date == 1:
                        if m_date == 1:
                            moiss = "JAN'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            # 'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            # 'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': amount_paid,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0, 
                            'bal_pay1': move.amount_residual,  
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)
                    elif p_date == 2:
                        if m_date == 2:
                            moiss = "FEB'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            # 'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            # 'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': amount_paid,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)
                    elif p_date == 3:
                        if m_date == 3:
                            moiss = "MAR'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': amount_paid,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)
                    elif p_date == 4:
                        if m_date == 4:
                            moiss = "APR'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': amount_paid,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0, 
                            'bal_pay1': move.amount_residual,  
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)
                    elif p_date == 5:
                        if m_date == 5:
                            moiss = "MAY'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': amount_paid,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)  
                    elif p_date == 6:
                        if m_date == 6:
                            moiss = "JUN'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': amount_paid,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)
                    elif p_date == 7:
                        if m_date == 7:
                            moiss = "JUL'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': amount_paid,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0, 
                            'bal_pay1': move.amount_residual,  
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)    
                    elif p_date == 8:
                        if m_date == 8:
                            moiss = "AUG'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': amount_paid,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)    
                    elif p_date == 9:
                        if m_date == 9:
                            moiss = "SEP'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': amount_paid,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,
                            'bal_pay1': move.amount_residual,   
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)      
                    elif p_date == 10:
                        if m_date == 10:
                            moiss = "OCT'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': amount_paid,
                            'nov_pay1': 0.0,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)      
                    elif p_date == 11:
                        if m_date == 11:
                            moiss = "NOV'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': amount_paid,
                            'dec_pay1': 0.0,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)    
                    elif p_date == 12:
                        if m_date == 12:
                            moiss = "DEC'" + str(m_day)
                        res=({
                            'name_policy1': move.partner_id.name,  
                            #'amount1': move.amount_untaxed, 
                            'name_move1': move.name, 
                            #'credit_note1': note,
                            'net_invoice1': move.amount_total,
                            'invoice_month1': moiss,
                            'jan_pay1': 0.0,
                            'feb_pay1': 0.0,
                            'march_pay1': 0.0,
                            'april_pay1': 0.0,
                            'may_pay1': 0.0,
                            'june_pay1': 0.0,
                            'july_pay1': 0.0,
                            'aug_pay1': 0.0,
                            'sept_pay1': 0.0,
                            'oct_pay1': 0.0,
                            'nov_pay1': 0.0,
                            'dec_pay1': amount_paid,  
                            'bal_pay1': move.amount_residual, 
                            'premium_report_id1':self.id,
                            'move1': move.id
                        })
                        results.append(res)            
            else:
                note = self.env['account.move'].search([('type', '=', "out_refund"), ('reversed_entry_id', '=', move.id)]).amount_total
                if m_date == 1:
                    moiss = "JAN'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)  
                elif m_date == 2:
                    moiss = "FEB'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)  
                elif m_date == 3:
                    moiss = "MAR'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res) 
                elif m_date == 4:
                    moiss = "APR'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)  
                elif m_date == 5:
                    moiss = "MAY'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed,
                        'name_move1': move.name,  
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res) 
                elif m_date == 6:
                    moiss = "JUN'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)  
                elif m_date == 7:
                    moiss = "JUL'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)   
                elif m_date == 8:
                    moiss = "AUG'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)  
                elif m_date == 9:
                    moiss = "SEP'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)   
                elif m_date == 10:
                    moiss = "OCT'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed,
                        'name_move1': move.name,  
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res) 
                elif m_date == 11:
                    moiss = "NOV'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)   
                elif m_date == 12:
                    moiss = "DEC'" + str(m_day)
                    res=({
                        'name_policy1': move.partner_id.name,  
                        #'amount1': move.amount_untaxed, 
                        'name_move1': move.name, 
                        #'credit_note1': note,
                        'net_invoice1': move.amount_total,
                        'invoice_month1': moiss,
                        'jan_pay1': 0,
                        'feb_pay1': 0,
                        'march_pay1': 0,
                        'april_pay1': 0,
                        'may_pay1': 0,
                        'june_pay1': 0,
                        'july_pay1': 0,
                        'aug_pay1': 0,
                        'sept_pay1': 0,
                        'oct_pay1': 0,
                        'nov_pay1': 0,
                        'dec_pay1': 0,  
                        'bal_pay1': move.amount_residual, 
                        'premium_report_id1':self.id,
                        'move1': move.id
                    })
                    results.append(res)                                


                    
        
        def keyfun(x):
            return x['name_move1']
        lineGroups = itertools.groupby(results, keyfun)
        for resu in lineGroups:
            name_move2 = resu[0]
            line_moves = resu[1]
            jans=fevs=mars=avrs=mays=juns=juls=augs=seps=octs=novs=decs=bals=0
            for line_move in line_moves:
                jans += line_move['jan_pay1']
                fevs += line_move['feb_pay1']
                mars += line_move['march_pay1']
                avrs += line_move['april_pay1']
                mays += line_move['may_pay1']
                juns += line_move['june_pay1']
                juls += line_move['july_pay1']
                augs += line_move['aug_pay1']
                seps += line_move['sept_pay1']
                octs += line_move['oct_pay1']
                novs += line_move['nov_pay1']
                decs += line_move['dec_pay1']
                # bals += line_move['bal_pay1']
                
                

            line = self.env['premium.report.line'].create({
                    'name_policy': line_move['name_policy1'],  
                    #'amount': line_move['amount1'], 
                    #'credit_note': line_move['credit_note1'],
                    'net_invoice': line_move['net_invoice1'],
                    'invoice_month': line_move['invoice_month1'],
                    'jan_pay': jans,
                    'feb_pay': fevs,
                    'march_pay': mars,
                    'april_pay': avrs,
                    'may_pay': mays,
                    'june_pay': juns,
                    'july_pay': juls,
                    'aug_pay': augs,
                    'sept_pay': seps,
                    'oct_pay': octs,
                    'nov_pay': novs,
                    'dec_pay': decs,
                    'bal_pay': line_move['bal_pay1'],
                    'exclude_from_sum_tab': True,
                    'premium_report_id':line_move['premium_report_id1'],
                    'move': line_move['move1']
                    })      
        self.confirm_sheet()

    
    def compute_month(self):
        results = []
        moves = self.env['account.move'].search([('type', '=', "out_invoice"), ('state', '=', "posted")])
        if self.mois:
            for move in moves:
                qte = total_qte =0
                move_lines = self.env['account.move.line'].search([('move_id', '=', move.id)])
                for move_l in move_lines:
                    if move_l.product_id:
                        qte += move_l.quantity
                total_qte = qte

                payment_voucher = move.invoice_payments_widget
                payment_voucher = json.loads(payment_voucher)

                m_date0 = move.date
                m_date = m_date0.month

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

                        
                        if m_date == 1:
                            m_mois = "january"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)
                        elif m_date == 2:
                            m_mois = "febuary"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)
                        elif m_date == 3:
                            m_mois = "march"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)
                        elif m_date == 4:
                            m_mois = "april"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)
                        elif m_date == 5:
                            m_mois = "may"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res) 
                        elif m_date == 6:
                            m_mois = "june"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)
                        elif m_date == 7:
                            m_mois = "july"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)  
                        elif m_date == 8:
                            m_mois = "august"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res) 
                        elif m_date == 9:
                            m_mois = "september"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)   
                        elif m_date == 10:
                            m_mois = "october"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)   
                        elif m_date == 11:
                            m_mois = "november"
                            if m_mois == self.mois :
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)  
                        elif m_date == 12:
                            m_mois = "december"
                            if m_mois == self.mois:
                                res=({
                                    'name_move1': move.name, 
                                    'name_policy1': move.partner_id.name,  
                                    'prem_r1': amount_paid, 
                                    'ind_enr1': total_qte, 
                                    'written_prem1': move.amount_total,
                                    'exclude_from_premium_tab1': True,
                                    'premium_report_id1':self.id,
                                    'move1': move.id
                                })
                                results.append(res)  
                else:
                    if m_date == 1:
                        m_mois = "january"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)
                    elif m_date == 2:
                        m_mois = "febuary"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)
                    elif m_date == 3:
                        m_mois = "march"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)
                    elif m_date == 4:
                        m_mois = "april"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)
                    elif m_date == 5:
                        m_mois = "may"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res) 
                    elif m_date == 6:
                        m_mois = "june"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)
                    elif m_date == 7:
                        m_mois = "july"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)   
                    elif m_date == 8:
                        m_mois = "august"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)   
                    elif m_date == 9:
                        m_mois = "september"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)  
                    elif m_date == 10:
                        m_mois = "october"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)  
                    elif m_date == 11:
                        m_mois = "november"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res) 
                    elif m_date == 12:
                        m_mois = "december"
                        if m_mois == self.mois:
                            res=({
                                'name_move1': move.name, 
                                'name_policy1': move.partner_id.name,  
                                'prem_r1': 0, 
                                'ind_enr1': total_qte, 
                                'written_prem1': move.amount_total,
                                'exclude_from_premium_tab1': True,
                                'premium_report_id1':self.id,
                                'move1': move.id
                            })
                            results.append(res)   


            def keyfun(x):
                return x['name_move1']
            lineGroups = itertools.groupby(results, keyfun)
            for resu in lineGroups:
                name_move2 = resu[0]
                line_moves = resu[1]
                prem_rs=0
                for line_move in line_moves:
                    prem_rs += line_move['prem_r1']
                
                

                line = self.env['premium.report.line'].create({
                    'name_policy': line_move['name_policy1'],  
                    'prem_r': prem_rs, 
                    'ind_enr': line_move['ind_enr1'], 
                    'written_prem': line_move['written_prem1'],
                    'exclude_from_premium_tab': line_move['exclude_from_premium_tab1'],
                    'premium_report_id':line_move['premium_report_id1'],
                    'move': line_move['move1']
                })

            self.confirm_sheet_sum()
        else:
            raise UserError(_('Enter the month before to generate summary report.'))   
    
    
    def confirm_sheet(self):
        """
        confirm Premium report  - confirmed Premium report after computing premium Lines..
        """
        for premium in self:
            if not premium.line_ids:
                raise UserError(_('You can not generate premium report without premium lines because the invoices do not exist for this customer or it has already been generated.'))
            date = fields.Date.from_string(fields.Date.today())
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('payment.premium')    
            premium.write({
                'number': 'PREMIUM' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })  

    def confirm_sheet_sum(self):
        """
        confirm summary report  - confirmed Summary report after computing summary Lines..
        """
        for summary in self:
            if not summary.sum_line_ids:
                raise UserError(_('You can not generate summary report without summary lines because the invoices do not exist for this customer or it has already been generated.'))
            date = fields.Date.from_string(fields.Date.today())
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('payment.summary')    
            summary.write({
                'number': 'SUMMARY' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })         

    
class PremiumReportLine(models.Model):
    '''
    Bank premium report Lines
    '''
    _name = 'premium.report.line'
    _description = 'Premium Report Lines'
    
    premium_report_id = fields.Many2one('premium.report', string='Premium report', ondelete="cascade")
    name_policy = fields.Char(string='Name of policy')
    # amount = fields.Float(string='Amount', digits='Payroll')
    # credit_note = fields.Float(string='Credit Note', digits='Payroll')
    net_invoice = fields.Float(string='Net Invoice', digits='Payroll')
    invoice_month = fields.Char(string='Invoice Month')
    jan_pay = fields.Float(string='Jan Payment')
    feb_pay = fields.Float(string='Feb Payment')
    march_pay = fields.Float(string='March Payment')
    april_pay = fields.Float(string='April Payment')
    may_pay = fields.Float(string='May Payment')
    june_pay = fields.Float(string='June Payment')
    july_pay = fields.Float(string='July Payment')
    aug_pay = fields.Float(string='Aug Payment')
    sept_pay = fields.Float(string='Sept Payment')
    oct_pay = fields.Float(string='Oct Payment')
    nov_pay = fields.Float(string='Nov Payment')
    dec_pay = fields.Float(string='Dec Payment')
    bal_pay = fields.Float(string='Balance')

    prem_r = fields.Float(string='Premium Received')
    written_prem = fields.Float(string='Written Prem./quotes')
    ind_enr = fields.Integer(string='Individual Enrol')
    exclude_from_premium_tab = fields.Boolean(help="Technical field used to exclude some lines from the line_ids tab in the form view.")
    exclude_from_sum_tab = fields.Boolean(help="Technical field used to exclude some lines from the sum_line_ids tab in the form view.")
    move = fields.Many2one('account.move', string='move', required=True)



class Premiumrepo(models.AbstractModel):
    _name = "report.client_pi.report_premium"
    _template = 'client_pi.report_premium'
    _description = "premium Report"

    # def get_total_amount(self):
    #     return self.total_amount
    # def get_total_credit_note(self):
    #     return self.total_credit_note
    def get_total_net_invoice(self):
        return self.total_net_invoice 
    def get_total_jan_pay(self):
        return self.total_jan_pay
    def get_total_feb_pay(self):
        return self.total_feb_pay
    def get_total_march_pay(self):
        return self.total_march_pay 
    def get_total_april_pay(self):
        return self.total_april_pay
    def get_total_may_pay(self):
        return self.total_may_pay
    def get_total_june_pay(self):
        return self.total_june_pay 
    def get_total_july_pay(self):
        return self.total_july_pay
    def get_total_aug_pay(self):
        return self.total_aug_pay
    def get_total_sept_pay(self):
        return self.total_sept_pay  
    def get_total_oct_pay(self):
        return self.total_oct_pay
    def get_total_nov_pay(self):
        return self.total_nov_pay
    def get_total_dec_pay(self):
        return self.total_dec_pay 
    def get_total_bal_pay(self):
        return self.total_bal_pay                              

    def get_detail(self, line_ids):
        result = []
        # self.total_amount = 0.00
        # self.total_credit_note = 0.00
        self.total_net_invoice = 0.00
        self.total_jan_pay = 0.00
        self.total_feb_pay = 0.00
        self.total_march_pay = 0.00
        self.total_april_pay = 0.00
        self.total_may_pay = 0.00
        self.total_june_pay = 0.00
        self.total_july_pay = 0.00
        self.total_aug_pay = 0.00
        self.total_sept_pay = 0.00
        self.total_oct_pay = 0.00
        self.total_nov_pay = 0.00
        self.total_dec_pay = 0.00
        self.total_bal_pay = 0.00
        for l in line_ids:
            res = {}
            res.update({
                    'name_policy': l.name_policy,  
                    # 'amount': l.amount, 
                    # 'credit_note': l.credit_note,
                    'net_invoice': l.net_invoice,
                    'invoice_month': l.invoice_month,
                    'jan_pay': l.jan_pay,
                    'feb_pay': l.feb_pay,
                    'march_pay': l.march_pay,
                    'april_pay': l.april_pay,
                    'may_pay': l.may_pay,
                    'june_pay': l.june_pay,
                    'july_pay': l.july_pay,
                    'aug_pay': l.aug_pay,
                    'sept_pay': l.sept_pay,
                    'oct_pay': l.oct_pay,
                    'nov_pay': l.nov_pay,
                    'dec_pay': l.dec_pay,
                    'bal_pay': l.bal_pay
                    })
            # self.total_amount += l.amount
            # self.total_credit_note += l.credit_note
            self.total_net_invoice += l.net_invoice
            self.total_jan_pay += l.jan_pay
            self.total_feb_pay += l.feb_pay
            self.total_march_pay += l.march_pay
            self.total_april_pay += l.april_pay
            self.total_may_pay += l.may_pay
            self.total_june_pay += l.june_pay
            self.total_july_pay += l.july_pay
            self.total_aug_pay += l.aug_pay
            self.total_sept_pay += l.sept_pay
            self.total_oct_pay += l.oct_pay
            self.total_nov_pay += l.nov_pay
            self.total_dec_pay += l.dec_pay
            self.total_bal_pay += l.bal_pay
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        premium = self.env['premium.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'premium.report',
            'data': data,
            'docs': premium,
            'time': time,
            'get_detail': self.get_detail,
            # 'get_total_amount': self.get_total_amount,
            # 'get_total_credit_note': self.get_total_credit_note,
            'get_total_net_invoice': self.get_total_net_invoice,
            'get_total_jan_pay': self.get_total_jan_pay,
            'get_total_feb_pay': self.get_total_feb_pay,
            'get_total_march_pay': self.get_total_march_pay,
            'get_total_april_pay': self.get_total_april_pay,
            'get_total_may_pay': self.get_total_may_pay,
            'get_total_june_pay': self.get_total_june_pay,
            'get_total_july_pay': self.get_total_july_pay,
            'get_total_aug_pay': self.get_total_aug_pay,
            'get_total_sept_pay': self.get_total_sept_pay, 
            'get_total_oct_pay': self.get_total_oct_pay,
            'get_total_nov_pay': self.get_total_nov_pay,
            'get_total_dec_pay': self.get_total_dec_pay,
            'get_total_bal_pay': self.get_total_bal_pay,
        }


class Summaryrepo(models.AbstractModel):
    _name = "report.client_pi.report_summary"
    _template = 'client_pi.report_summary'
    _description = "summary Report"

    def get_total_pr(self):
        return self.total_pr
    def get_total_ind(self):
        return self.total_ind
    def get_total_w(self):
        return self.total_w                         

    def get_detail(self, sum_line_ids):
        result = []
        self.total_pr = 0.00
        self.total_ind = 0
        self.total_w = 0.00
        for l in sum_line_ids:
            res = {}
            res.update({
                    'name_policy': l.name_policy,  
                    'prem_r': l.prem_r, 
                    'ind_enr': l.ind_enr,
                    'written_prem': l.written_prem
                    })
            self.total_pr += l.prem_r
            self.total_ind += l.ind_enr
            self.total_w += l.written_prem
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        summary = self.env['premium.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'premium.report',
            'data': data,
            'docs': summary,
            'time': time,
            'get_detail': self.get_detail,
            'get_total_pr': self.get_total_pr,
            'get_total_ind': self.get_total_ind,
            'get_total_w': self.get_total_w,
        }        
