# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
import time, datetime
import calendar
import json
from odoo.exceptions import UserError, ValidationError
from operator import itemgetter
from itertools import groupby
from json import dumps
from itertools import zip_longest

from collections import defaultdict
import itertools
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

class AccountTaxReport(models.Model):
    '''
    Account Tax Report
    '''
    _name = 'account.tax.r'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = " Account Tax Report"
    _order = "id desc, date desc"
    _rec_name ='name'

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())

    def _get_default_mois(self):
        now = datetime.datetime.now()
        mois = now.month
        return mois

    def _get_default_annee(self):
        now = datetime.datetime.now()
        year = now.year
        return year

    def get_years():
        year_list = []
        for i in range(2016, 2036):
            year_list.append((i, str(i)))
        return year_list

    @api.model
    def year_selection(self):
        now = datetime.datetime.now()
        year = 2018 # replace 2000 with your a start year
        year_list = []
        while year != 2038: # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    year = fields.Selection(
        year_selection,
        string="Year",
        default=_get_default_annee, # as a default value it would be 2019
    )

    type_report = fields.Selection([
        ('claim', 'Withholding Tax Claims'),
        ('expense', 'Withholding Tax Expenses'),
    ], string='Report', default='claim', index=True, tracking=True)
    name = fields.Char(readonly=True , index=True, tracking=True, required=True, states={'draft': [('readonly', False)]})
    month = fields.Selection([
        ('1', 'January'), 
        ('2', 'February'),
        ('3', 'March'), 
        ('4', 'April'),
        ('5', 'May'), 
        ('6', 'June'), 
        ('7', 'July'), 
        ('8', 'August'), 
        ('9', 'September'), 
        ('10', 'October'), 
        ('11', 'November'), 
        ('12', 'December'),
        ], string = "Tax Month", index=True, tracking=True, default=_get_default_mois )
    #year = fields.Selection(get_years(), string='Year',)                      
    #year = fields.Char(string ="Tax Year", readonly=True , index=True, tracking=True )
    date = fields.Date(string = "date Print", readonly=True , index=True, tracking=True, required=True, states={'draft': [('readonly', False)]}, default=_get_default_date,
        help='Tax Report Date is used to search Payslips')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', index=True, tracking=True, readonly=True)
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True)
    line_ids = fields.One2many('account.tax.r.line', 'repor', string='Tax Report' , index=True, tracking=True,
        states={'draft': [('readonly', False)]}, readonly=True, copy=True)

    @api.constrains('month','year','type_report')
    def _check_amount(self):
        for tax in self:
            if tax.month:
                if tax.year:
                    tax_reports = self.env['account.tax.r'].search([('month', '=', self.month), ('year', '=', self.year), ('type_report', '=', self.type_report)])
                    if len(tax_reports) > 1:
                        raise ValidationError(_('You can not create two tax report for one month .'))
                else:
                    raise ValidationError(_('Please add Year.'))
            else:
                raise ValidationError(_('Please add Month.'))

    def confirm_sheet(self):
        """
        confirm Tax report  - confirmed Tax report after computing tax Lines..
        """
        dat = self.month
        if dat == 12:
            mois = "December"
        if dat == 1:
            mois = "January"
        if dat == 2:
            mois = "February"
        if dat == 3:
            mois = "March"
        if dat == 4:
            mois = "April"
        if dat == 5:
            mois = "May"
        if dat == 6:
            mois = "June"
        if dat == 7:
            mois = "July"
        if dat == 8:
            mois = "August"
        if dat == 9:
            mois = "September"
        if dat == 10:
            mois = "October"
        if dat == 11:
            mois = "November"

        for tax in self:
            if not tax.line_ids:
                raise UserError(_('You can not confirm tax report without tax lines.'))
            date = fields.Date.from_string(fields.Date.today())
            # for line in tax.line_ids:
            #     line.move.taxr = True
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('payment.tax')
            tax.write({
                'number': 'TAX' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })

    def compute(self):
        annee = int(self.year)
        mois = int(self.month)
        lastday = calendar.monthrange(annee, mois)[1] 
        date1 = datetime.date(annee, mois, 1)
        date2 = datetime.date(annee, mois, lastday)
        if self.type_report == 'claim':
            moves = self.env['account.move'].search([('invoice_payment_state', '=', 'paid'), ('journal_id.code', '=', "BILL"), ('state', '=', "posted")])
            for move in moves:
                payment_voucher = move.invoice_payments_widget
                payment_voucher = json.loads(payment_voucher)
                if payment_voucher:
                    pv = payment_voucher['content'][0]['account_payment_id']
                    state = self.env['account.payment'].search([('id', '=', pv)], limit=1).state
                    if state != "draft":
                        date_paid = self.env['account.payment'].search([('id', '=', pv)], limit=1).payment_date
                        if date1 <= date_paid <= date2:
                            lines = self.env['account.move.line'].search([('tax_base_amount', '>', '0'),('parent_state','=','posted'),('move_id','=',move.id)])
                            line_tax =[]
                            amout0 = 0.0
                            amout1 = 0.0
                            am_paid0 = 0.0
                            am_paid1 = 0.0
                            for line in lines:
                                partner = line.partner_id.name
                                amout = line.tax_base_amount
                                am_paid = line.price_total
                                move_name = line.move_name
                                tax = line.name
                                if tax == "WT.":
                                    tax = "7.5%"
                                if tax == "WT":
                                    tax = "3%"
                                if tax == "WT 7.5%":
                                    tax0 = "7.5%"
                                    amout0 += amout
                                    am_paid0 +=am_paid
                                if tax == "WT 3%":
                                    tax1 = "3%"
                                    amout1 += amout
                                    am_paid1 +=am_paid
                            if am_paid0 != 0:
                                tax_r = {
                                    'date': date_paid , 
                                    'repor':self.id, 
                                    'move': move_name,
                                    'partner_id':partner, 
                                    'amount_app':amout0,
                                    'tax':tax0,
                                    'amount_paid':(-1)*am_paid0
                                    }
                                line = self.env['account.tax.r.line'].create(tax_r)
                            if am_paid0 != 0:
                                tax_r1 = {
                                    'date': date_paid , 
                                    'repor':self.id, 
                                    'move': move_name,
                                    'partner_id':partner, 
                                    'amount_app':amout1,
                                    'tax':tax1,
                                    'amount_paid':(-1)*am_paid1
                                    }
                                line = self.env['account.tax.r.line'].create(tax_r1)
            self.confirm_sheet()
        elif self.type_report == 'expense':
            payments = self.env['account.payment'].search([('state', '!=', 'draft')])
            for payment in payments:
                date_paid = payment.payment_date
                # _logger.info("mail=== '" + str(date_paid) + "' ok !")
                if date1 < date_paid < date2:
                    sheet = payment.expense_sheet_id
                    partner = payment.partner_id.name
                    sheet_name = sheet.name
                    if sheet:
                        sheet_id = sheet.id
                        expenses = self.env['hr.expense'].search([('sheet_id', '=', sheet_id)])
                        y = 0.0
                        z = 0.0 
                        untaxed_7 = 0.0
                        untaxed_3 = 0.0
                        paid_am3 = 0.0
                        paid_am7 = 0.0
                        tax7 = "7.5%"
                        tax3 = "3%"
                        for expense in expenses:
                            # _logger.info("mail=== '" + str(expense) + "' ok !")
                            y = untaxed_amount = expense.untaxed_amount
                            z = total_amount = expense.total_amount
                            if y == 0.0:
                                tax_pro = 0.0
                            else:
                                tax_pro = abs(((z - y)*100)/y)
                            if 7 < tax_pro < 8 :
                                untaxed_7 = untaxed_7 + untaxed_amount
                                paid_am7 = paid_am7 +(untaxed_amount - total_amount)
                            if 2 < tax_pro < 4 :
                                untaxed_3 = untaxed_3 + untaxed_amount
                                paid_am3 = paid_am3 + (untaxed_amount - total_amount)
                        if paid_am7 != 0:
                            tax_r7 = {
                                'date': date_paid , 
                                'repor':self.id, 
                                'move': sheet_name,
                                'partner_id':partner, 
                                'amount_app':untaxed_7,
                                'tax':tax7,
                                'amount_paid':paid_am7
                                }
                            line = self.env['account.tax.r.line'].create(tax_r7)
                            _logger.info("mail=== '" + str(tax_r7) + "' ok !")
                        if paid_am3 != 0:
                            tax_r3 = {
                                'date': date_paid , 
                                'repor':self.id, 
                                'move': sheet_name,
                                'partner_id':partner, 
                                'amount_app':untaxed_3,
                                'tax':tax3,
                                'amount_paid':paid_am3
                                }
                            line = self.env['account.tax.r.line'].create(tax_r3)
                            _logger.info("mail=== '" + str(tax_r3) + "' ok !")
            self.confirm_sheet()
            
    def set_to_draft(self):
        """Resets Tax report as draft.
        """
        self.write({'state': 'draft'})
        # for tax in self:
        #     for line in tax.line_ids:
        #         line.move.taxr = False

    def cancel_sheet(self):
        """Marks tax report as cancelled.
        """
        self.write({'state': 'cancel'})
        # for tax in self:
        #     for line in tax.line_ids:
        #         line.tax_report.available_tax = False

class AccountTaxReportLines(models.Model):
    '''Bank Tax report Lines
    '''
    _name = 'account.tax.r.line'
    _description = 'Tax Report Lines'

    date = fields.Date(string='date', tracking=True)
    repor = fields.Many2one('account.tax.r', string='Tax report', tracking=True)
    move = fields.Char( string='move', required=True, tracking=True)
    partner_id = fields.Char(string='Payee', tracking=True)
    amount_app = fields.Float(string='Amount Approve', digits='Payroll', tracking=True)
    tax = fields.Char('Tax', required=True, tracking=True)
    amount_paid = fields.Float(string='Amount Paid', digits='Payroll', tracking=True)


class taxrepo(models.AbstractModel):
    _name = "report.client_pi.reporttax"
    _description = "Payement Advice Report"

    def get_bysal_total(self):
        return self.total_bysal

    def get_detail(self, line_ids):
        result = []
        res = {}
        result1 = []
        res1 = {}
        self.total_bysal = 0.00
        for l in line_ids:
            res = {}
            res.update({
                    'date': l.date,
                    'partner_id': l.partner_id,
                    # 'move': l.move.move_name,
                    'amount_app': l.amount_app,
                    'tax': l.tax,
                    'amount_paid': l.amount_paid,
                    })
            self.total_bysal += l.amount_paid
            result.append(res)
        sorted(result, key = itemgetter('partner_id'))
        for gr_part, products in groupby(result, key=itemgetter('partner_id', 'tax')):
            partner_id = gr_part[0]
            tax = gr_part[1]
            amount_paid = 0.00 
            amount_app = 0.00 
            for product in products:
                res1 = {}
                amount_app += product['amount_app']
                amount_paid += product['amount_paid']
                date = product['date']
            res1.update({
                    'date': date,
                    'partner_id': partner_id,
                    'amount_app': amount_app,
                    'tax': tax,
                    'amount_paid': amount_paid,
                    })
            result1.append(res1)
        return result1

    @api.model
    def _get_report_values(self, docids, data=None):
        tax = self.env['account.tax.r'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'account.tax.r',
            'data': data,
            'docs': tax,
            'time': time,
            'get_detail': self.get_detail,
            'get_bysal_total': self.get_bysal_total,
        }

