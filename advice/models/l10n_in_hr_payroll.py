# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

from collections import defaultdict

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class AccountMovePAdvice(models.Model):
    '''
    Bank Advice
    '''
    _name = 'account.move.advice'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = " Account Move Advice"
    _order = "id desc, date desc"

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())

    name = fields.Char(readonly=True , index=True, tracking=True, required=True, states={'draft': [('readonly', False)]})
    note = fields.Text(string='Description', index=True, tracking=True,
                       default='We request you to kindly credit the accounts of the following service providers of GLICOHEALTHCARE from our bank account no: 002220230007 as claims settlement. The details of their accounts and corresponding amounts are as below.')
    date = fields.Date(readonly=True , index=True, tracking=True, required=True, states={'draft': [('readonly', False)]}, default=_get_default_date,
        help='Advice Date is used to search Payslips')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', index=True, tracking=True, readonly=True)
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True)
    line_ids = fields.One2many('account.move.advice.line', 'advice_id', string='Vendors Pay' , index=True, tracking=True,
        states={'draft': [('readonly', False)]}, readonly=True, copy=True)
    chaque_nos = fields.Char(string='Cheque Numbers' , index=True, tracking=True)
    neft = fields.Boolean(string='NEFT Transaction' , index=True, tracking=True, help='Check this box if your company use online transfer for salary')
    company_id = fields.Many2one('res.company' , index=True, tracking=True, string='Company', required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default=lambda self: self.env.company)
    bank_id = fields.Many2one('account.journal', string='Bank', tracking=True,
        help='Select the Bank from which the salary is going to be paid')
    bank_acc_number = fields.Char(string='Account Number', readonly=True, compute='onchange_acc_number')
    # batch_id = fields.Many2one('hr.payslip.run', string='Batch', readonly=True)

    @api.depends('bank_id')
    def onchange_acc_number(self):
        self.bank_acc_number = self.bank_id.bank_acc_number 

    def confirm_sheet(self):
        """
        confirm Advice - confirmed Advice after computing Advice Lines..
        """
        for advice in self:
            if not advice.line_ids:
                raise UserError(_('You can not confirm Payment advice without advice lines.'))
            date = fields.Date.from_string(fields.Date.today())
            for line in advice.line_ids:
                line.pay.available_advice = True
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('payment.manual')
            advice.write({
                'number': 'PA' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })

    def set_to_draft(self):
        """Resets Advice as draft.
        """
        self.write({'state': 'draft'})
        for advice in self:
            for line in advice.line_ids:
                line.pay.available_advice = False

    def cancel_sheet(self):
        """Marks Advice as cancelled.
        """
        self.write({'state': 'cancel'})
        for advice in self:
            for line in advice.line_ids:
                line.pay.available_advice = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.bank_id = self.company_id.partner_id.bank_ids and self.company_id.partner_id.bank_ids[0].bank_id.id or False


class AccountMoveAdviceLine(models.Model):
    '''
    Bank Advice Lines
    '''
    _name = 'account.move.advice.line'
    _description = 'Bank Advice Lines'

    advice_id = fields.Many2one('account.move.advice', string='Bank Advice')
    name_bank = fields.Char('Bank Name.', required=True)
    pay = fields.Many2one('account.payment', string='Payment', required=True)
    name = fields.Char('Bank Account No.', required=True)
    ifsc_code = fields.Char(string='Branch')
    partner_id = fields.Many2one('res.partner', string='Payee', required=True)
    bysal = fields.Float(string='Amount', digits='Payroll')
    company_id = fields.Many2one('res.company', related='advice_id.company_id', string='Company', store=True, readonly=False)
    ifsc = fields.Boolean(related='advice_id.neft', string='IFSC', readonly=False)

    @api.onchange('pay')
    def onchange_pay_id(self):
        self.partner_id = self.pay.partner_id
        self.bysal = self.pay.amount

    @api.onchange('partner_id')
    def onchange_employee_id(self):
        self.name = self.partner_id.account_n
        self.name_bank = self.partner_id.bank_name
        self.ifsc_code = self.partner_id.branch or ''

class AccountPaymentabc(models.Model):
    _inherit = "account.payment"

    available_advice = fields.Boolean(string='Payment Advice Generated ?',
                                help='If this box is checked which means that Payment Advice exists for current batch',
                                readonly=True, copy=False)
