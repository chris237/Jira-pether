# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMovePAdvi(models.Model):
    '''
    Bank Advice
    '''
    _name = 'account.move.advi'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = " Account Move Cheque Advice"
    _order = "id desc, date desc"

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())

    name = fields.Char(readonly=True, required=True, tracking=True, index=True, states={'draft': [('readonly', False)]})
    note = fields.Text(string='Description', tracking=True, index=True, 
                       default='Please find below details of cheques that have been released today for payment from our account no xxxxxx held with you.')
    date = fields.Date(readonly=True, required=True, tracking=True, index=True, states={'draft': [('readonly', False)]}, default=_get_default_date,
        help='Advice Date is used to search Payslips')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, index=True, readonly=True)
    number = fields.Char(string='Reference', readonly=True, tracking=True, index=True)
    line_ids = fields.One2many('account.move.advi.line', 'advice_id', string='Vendors Pay',
        states={'draft': [('readonly', False)]}, tracking=True, index=True, readonly=True, copy=True)
    neft = fields.Boolean(string='NEFT Transaction', tracking=True, index=True, help='Check this box if your company use online transfer for salary')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
        states={'draft': [('readonly', False)]},tracking=True, index=True, default=lambda self: self.env.company)
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
            number = self.env['ir.sequence'].next_by_code('payment.check')
            advice.write({
                'number': 'PA/C' + '/' + advice_year + '/' + number,
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
 
class AccountMoveAdviLine(models.Model):
    '''
    Bank Advice Lines
    '''
    _name = 'account.move.advi.line'
    _description = 'Bank Cheque Advice Lines'

    advice_id = fields.Many2one('account.move.advi', string='Bank Advice')
    pay = fields.Many2one('account.payment', string='Payment', required=True)
    partner_id = fields.Many2one('res.partner', string='Payee', required=True)
    chequ = fields.Char(string='Cheque No')
    comm = fields.Char(string='REMARKS', default='.')
    bysal = fields.Float(string='Amount', digits='Payroll')
    company_id = fields.Many2one('res.company', related='advice_id.company_id', string='Company', store=True, readonly=False)
    
    @api.onchange('pay')
    def onchange_pay_id(self):
        self.partner_id = self.pay.partner_id
        self.bysal = self.pay.amount
        self.chequ = self.pay.check_number

class AccountPaymentabc(models.Model):
    _inherit = "account.payment"

    available_advice = fields.Boolean(string='Payment Advice Generated ?',
                                help='If this box is checked which means that Payment Advice exists for current batch',
                                readonly=True, copy=False)
