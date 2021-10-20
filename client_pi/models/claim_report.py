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

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}
class AccountClaimReport(models.Model):
    '''
    Account Claim Report
    '''
    _name = 'account.claim.report'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Claim Report"
    _order = "id desc, date desc"
    _rec_name ='number'

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
    line_ids = fields.One2many('account.claim.report.line', 'claim_report_id', string='Claim Report' , index=True, copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True, default ='/')    
    #partner_id = fields.Many2one('res.partner', string='Partner',required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
 
    def compute(self):
        if self.partner_id:
            moves = self.env['account.move'].search([('invoice_payment_state', '=', 'paid'),('type', '=', 'in_invoice'),('partner_id', '=', self.partner_id.id), ('journal_id.code', '=', "BILL"), ('state', '=', "posted")])
            for move in moves:
                payment_voucher = move.invoice_payments_widget
                payment_voucher = json.loads(payment_voucher)
                if payment_voucher:
                    pv = payment_voucher['content'][0]['account_payment_id']
                    state = self.env['account.payment'].search([('id', '=', pv)], limit=1).state
                    if state != "draft":
                        voucher_no = self.env['account.payment'].search([('id', '=', pv)], limit=1).name
                        check_no = self.env['account.payment'].search([('id', '=', pv)], limit=1).check_number
                        date_paid = self.env['account.payment'].search([('id', '=', pv)], limit=1).payment_date
                        paid_by = self.env['account.payment'].search([('id', '=', pv)], limit=1).prepa
                        bank = self.env['account.payment'].search([('id', '=', pv)], limit=1).journal_id.name
                        
                    else:
                        raise ValidationError("Partner has his payment in draft state")  
                
                    claim_ref0 = move.date
                    claim_ref = claim_ref0.month
                    if claim_ref == 1:
                        mois = "JANUARY"
                    if claim_ref == 2:
                        mois = "FEBUARY"
                    if claim_ref == 3:
                        mois = "MARCH"
                    if claim_ref == 4:
                        mois = "APRIL"
                    if claim_ref == 5:
                        mois = "MAY"
                    if claim_ref == 6:
                        mois = "JUNE"
                    if claim_ref == 7:
                        mois = "JULY"
                    if claim_ref == 8:
                        mois = "AUGUST"
                    if claim_ref == 9:
                        mois = "SEPTEMBER"
                    if claim_ref == 10:
                        mois = "OCTOBER"
                    if claim_ref == 11:
                        mois = "NOVEMBER"
                    if claim_ref == 12:
                        mois = "DECEMBER"   
                    if self.date_from < move.date < self.date_to:    
                        if move.amount_untaxed <= move.amount_total :
                            date_submtd = move.date
                            amount_submtd = move.amount_untaxed
                            amount_apprvd = move.amount_total
                            amount_paid = move.amount_total
                            claim_ref = mois
                            tax_deduct = move.amount_tax_signed
                            if tax_deduct < 0:
                                tax_deduct = (-1)*tax_deduct 

                            line = self.env['account.claim.report.line'].create({
                                'partner_name':move.partner_id.name,
                                'date_submtd':date_submtd, 
                                'amount_submtd':amount_submtd,  
                                'amount_apprvd':amount_apprvd, 
                                'claim_report_id':self.id,
                                'amount_paid':amount_paid,
                                'move': move.id,
                                'claim_ref':claim_ref,
                                'date_paid':date_paid,
                                'voucher_no':voucher_no,
                                'check_no':check_no,
                                'bank':bank,
                                'tax_deduct':tax_deduct,
                                'paid_by':paid_by
                                })
                        else:    
                            date_submtd = move.date
                            amount_submtd = move.amount_untaxed
                            amount_apprvd = move.amount_untaxed
                            amount_paid = move.amount_total
                            claim_ref = mois
                            tax_deduct = move.amount_tax_signed
                            if tax_deduct < 0:
                                tax_deduct = (-1)*tax_deduct 
                        
                            line = self.env['account.claim.report.line'].create({
                                'partner_name':move.partner_id.name,
                                'date_submtd':date_submtd, 
                                'amount_submtd':amount_submtd,   
                                'amount_apprvd':amount_apprvd, 
                                'claim_report_id':self.id,
                                'amount_paid':amount_paid,
                                'move': move.id,
                                'claim_ref':claim_ref,
                                'date_paid':date_paid,
                                'voucher_no':voucher_no,
                                'check_no':check_no,
                                'bank':bank,
                                'tax_deduct':tax_deduct,
                                'paid_by':paid_by
                                })
                    
                
        else:
            moves = self.env['account.move'].search([('invoice_payment_state', '=', 'paid'),('type', '=', 'in_invoice'), ('journal_id.code', '=', "BILL"), ('state', '=', "posted")])    
            for move in moves:
                payment_voucher = move.invoice_payments_widget
                payment_voucher = json.loads(payment_voucher)
                if payment_voucher:
                    pv = payment_voucher['content'][0]['account_payment_id']
                    state = self.env['account.payment'].search([('id', '=', pv)], limit=1).state
                    if state != "draft":
                        voucher_no = self.env['account.payment'].search([('id', '=', pv)], limit=1).name
                        check_no = self.env['account.payment'].search([('id', '=', pv)], limit=1).check_number
                        date_paid = self.env['account.payment'].search([('id', '=', pv)], limit=1).payment_date
                        paid_by = self.env['account.payment'].search([('id', '=', pv)], limit=1).prepa
                        bank = self.env['account.payment'].search([('id', '=', pv)], limit=1).journal_id.name
                        
                    else:
                        raise ValidationError("Partner has his payment in draft state")  
                
                    claim_ref0 = move.date
                    claim_ref = claim_ref0.month
                    if claim_ref == 1:
                        mois = "JANUARY"
                    if claim_ref == 2:
                        mois = "FEBUARY"
                    if claim_ref == 3:
                        mois = "MARCH"
                    if claim_ref == 4:
                        mois = "APRIL"
                    if claim_ref == 5:
                        mois = "MAY"
                    if claim_ref == 6:
                        mois = "JUNE"
                    if claim_ref == 7:
                        mois = "JULY"
                    if claim_ref == 8:
                        mois = "AUGUST"
                    if claim_ref == 9:
                        mois = "SEPTEMBER"
                    if claim_ref == 10:
                        mois = "OCTOBER"
                    if claim_ref == 11:
                        mois = "NOVEMBER"
                    if claim_ref == 12:
                        mois = "DECEMBER"   
                    if self.date_from < move.date < self.date_to:    
                        if move.amount_untaxed <= move.amount_total :
                            date_submtd = move.date
                            amount_submtd = move.amount_untaxed
                            amount_apprvd = move.amount_total
                            amount_paid = move.amount_total
                            claim_ref = mois
                            tax_deduct = move.amount_tax_signed
                            if tax_deduct < 0:
                                tax_deduct = (-1)*tax_deduct 

                            line = self.env['account.claim.report.line'].create({
                                'partner_name':move.partner_id.name,
                                'date_submtd':date_submtd,  
                                'amount_submtd':amount_submtd,  
                                'amount_apprvd':amount_apprvd, 
                                'claim_report_id':self.id,
                                'amount_paid':amount_paid,
                                'move': move.id,
                                'claim_ref':claim_ref,
                                'date_paid':date_paid,
                                'voucher_no':voucher_no,
                                'check_no':check_no,
                                'bank':bank,
                                'tax_deduct':tax_deduct,
                                'paid_by':paid_by
                                })
                        else:    
                            date_submtd = move.date
                            amount_submtd = move.amount_untaxed
                            amount_apprvd = move.amount_untaxed
                            amount_paid = move.amount_total
                            claim_ref = mois
                            tax_deduct = move.amount_tax_signed
                            if tax_deduct < 0:
                                tax_deduct = (-1)*tax_deduct 
                        
                            line = self.env['account.claim.report.line'].create({
                                'partner_name':move.partner_id.name,
                                'date_submtd':date_submtd,  
                                'amount_submtd':amount_submtd,  
                                'amount_apprvd':amount_apprvd, 
                                'claim_report_id':self.id,
                                'amount_paid':amount_paid,
                                'move': move.id,
                                'claim_ref':claim_ref,
                                'date_paid':date_paid,
                                'voucher_no':voucher_no,
                                'check_no':check_no,
                                'bank':bank,
                                'tax_deduct':tax_deduct,
                                'paid_by':paid_by
                                })
                    
                
        self.confirm_sheet()

    def confirm_sheet(self):
        """
        confirm Claim report  - confirmed Claim report after computing claim Lines..
        """
        for claim in self:
            if not claim.line_ids:
                raise UserError(_('You can not generate claim report without claim lines because the invoices do not exist for this customer or it has already been generated.'))
            date = fields.Date.from_string(fields.Date.today())
            for line in claim.line_ids:
                line.move.claimr = True
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('payment.claim')    
            claim.write({
                'number': 'CLAIM' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })  

    def set_to_draft(self):
        """Resets Claim report as draft.
        """
        self.write({'state': 'draft'})
        for claim in self:
            for line in claim.line_ids:
                line.move.claimr = False

    def cancel_sheet(self):
        """Marks Claim report as cancelled.
        """
        self.write({'state': 'cancel'})
        for claim in self:
            for line in claim.line_ids:
                line.move.claimr = False

    
class AccountClaimReportLine(models.Model):
    '''
    Bank claim report Lines
    '''
    _name = 'account.claim.report.line'
    _description = 'Claim Report Lines'
    
    claim_report_id = fields.Many2one('account.claim.report', string='Claim report', ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string='Partner')
    partner_name = fields.Char(string='Name Partner')
    claim_ref = fields.Char(string='Claim Ref')
    date_submtd = fields.Date(string='Date Submited')
    amount_submtd = fields.Float(string='Amount Submited', digits='Payroll')
    amount_apprvd = fields.Float(string='Amount Approved', digits='Payroll')
    amount_paid = fields.Float(string='Amount Paid', digits='Payroll')
    date_paid = fields.Date(string='Date Paid')
    voucher_no = fields.Char(string='Voucher No')
    check_no = fields.Char(string='Cheque No')
    bank = fields.Char(string='Bank') 
    tax_deduct = fields.Float(string='Tax Deduct')
    paid_by = fields.Char(string='Paid By')
    move = fields.Many2one('account.move', string='move', required=True)



class claimrepo(models.AbstractModel):
    _name = "report.client_pi.report_claim"
    _template = 'client_pi.report_claim'
    _description = "claim Report"

    def get_total_amount_smt (self):
        return self.total_amount_smt
    def get_total_amount_app (self):
        return self.total_amount_app
    def get_total_amount_paid(self):
        return self.total_amount_paid
    def get_total_amount_tax(self):
        return self.total_amount_tax            

    def get_detail(self, line_ids):
        result = []
        self.total_amount_smt = 0.00
        self.total_amount_app = 0.00
        self.total_amount_paid = 0.00
        self.total_amount_tax = 0.00
        for l in line_ids:
            res = {}
            res.update({
                    'partner_name': l.partner_name,
                    'date_submtd': l.date_submtd, 
                    'amount_submtd': l.amount_submtd, 
                    'amount_apprvd': l.amount_apprvd, 
                    'amount_paid': l.amount_paid,
                    'claim_ref': l.claim_ref,
                    'date_paid': l.date_paid,
                    'voucher_no': l.voucher_no,
                    'check_no': l.check_no,
                    'bank': l.bank,
                    'tax_deduct': l.tax_deduct,
                    'paid_by': l.paid_by
                    })
            self.total_amount_smt += l.amount_submtd
            self.total_amount_app += l.amount_apprvd
            self.total_amount_paid += l.amount_paid
            self.total_amount_tax += float(l.tax_deduct)
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        claim = self.env['account.claim.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.claim.report',
            'data': data,
            'docs': claim,
            'time': time,
            'get_detail': self.get_detail,
            'get_total_amount_smt': self.get_total_amount_smt,
            'get_total_amount_app': self.get_total_amount_app,
            'get_total_amount_paid': self.get_total_amount_paid,
            'get_total_amount_tax': self.get_total_amount_tax,
        }
