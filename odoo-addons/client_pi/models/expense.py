# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models, tools, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from werkzeug import url_encode
import datetime
import time
from datetime import date
import json
import requests
from operator import itemgetter
from itertools import groupby
from json import dumps
from itertools import zip_longest
from hashlib import sha256
from datetime import date, timedelta

from collections import defaultdict
import re, num2words
import logging
_logger = logging.getLogger(__name__)
try:
    from num2words import num2words
except ImportError:
    _logger.warning("The num2words python library is not installed, amount-to-text features won't be fully available.")
    num2words = None

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class HrExpenseup(models.Model):
    
    _inherit = "hr.expense"

    payment_mode = fields.Selection([
        ("own_account", "Employee"),
        ("company_account", "Company")
    ], default='own_account', states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")

    # def action_move_create(self):
    #     '''
    #     main function that is called when trying to create the accounting entries related to an expense
    #     '''
    #     move_group_by_sheet = self._get_account_move_by_sheet()

    #     move_line_values_by_expense = self._get_account_move_line_values()

    #     move_to_keep_draft = self.env['account.move']

    #     company_payments = self.env['account.payment']
        
    #     for expense in self:
    #         company_currency = expense.company_id.currency_id
    #         different_currency = expense.currency_id != company_currency

    #         # get the account move of the related sheet
    #         move = move_group_by_sheet[expense.sheet_id.id]

    #         # get move line values
    #         move_line_values = move_line_values_by_expense.get(expense.id)
    #         move_line_dst = move_line_values[-1]
    #         total_amount = move_line_dst['debit'] or -move_line_dst['credit']
    #         total_amount_currency = move_line_dst['amount_currency']

    #         # create one more move line, a counterline for the total on payable account
    #         if expense.payment_mode == 'company_account':
    #             if not expense.sheet_id.bank_journal_id.default_credit_account_id:
    #                 raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
    #             journal = expense.sheet_id.bank_journal_id
    #             # create payment
    #             payment_methods = journal.outbound_payment_method_ids if total_amount < 0 else journal.inbound_payment_method_ids
    #             journal_currency = journal.currency_id or journal.company_id.currency_id
    #             payment = self.env['account.payment'].create({
    #                 'payment_method_id': payment_methods and payment_methods[0].id or False,
    #                 'payment_type': 'outbound' if total_amount < 0 else 'inbound',
    #                 'partner_id': expense.partner_id1,
    #                 'partner_type': 'supplier',
    #                 'journal_id': journal.id,
    #                 'payment_date': expense.date,
    #                 'state': 'reconciled',
    #                 'currency_id': expense.currency_id.id if different_currency else journal_currency.id,
    #                 'amount': abs(total_amount_currency) if different_currency else abs(total_amount),
    #                 'disc' : 0.0,
    #                 'tclaims': abs(total_amount_currency) if different_currency else abs(total_amount),
    #                 'name': expense.name,
    #             })
    #             move_line_dst['payment_id'] = payment.id  

    #         # link move lines to move, and move to expense sheet
    #         move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
    #         expense.sheet_id.write({'account_move_id': move.id})

    #         if expense.payment_mode == 'company_account':
    #             expense.sheet_id.paid_expense_sheets()

    #     # post the moves
    #     for move in move_group_by_sheet.values():
    #         move.post()

    #     return move_group_by_sheet

class HrExpenseSheetup(models.Model):
    _inherit = "hr.expense.sheet"

    partner19  = fields.Boolean(string = "Partner ?")
    partner_id1 = fields.Many2one('res.partner', string="Partner")
    id_activity = fields.Many2one('mail.activity', string='activity')
    
    def action_submit_sheet(self):
        res = super(HrExpenseSheetup, self).action_submit_sheet()

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'hr.expense.sheet')]).id
        users = self.env['account.send.notif'].search([], limit=1)    
        for sheet in self:
            for user in users:
                if user.cfo.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': sheet.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.cfo.id,
                                    'note': 'Expenses has been submited and needs to be approve.'
                                    })                              
                    self.id_activity = line.id
                user.accountant_exp = self.env.user.id    

        return res            

    def approve_expense_sheets(self):   
        res = super(HrExpenseSheetup, self).approve_expense_sheets()   

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'hr.expense.sheet')]).id
        users = self.env['account.send.notif'].search([], limit=1)    
        for sheet in self:
            for user in users:
                _logger.info("user.accountant_exp.id=== '" + str(user.accountant_exp.id) + "' ok !")
                if user.accountant_exp.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': sheet.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.accountant_exp.id,
                                    'note': 'Expenses has been approved and needs to be post.'
                                    })                    
                    ok=self.id_activity.action_done()   
                    self.id_activity = line.id    
        return res 


    def action_sheet_move_create(self):
        if any(sheet.state != 'approve' for sheet in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not sheet.journal_id for sheet in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        expense_line_ids = self.mapped('expense_line_ids')\
            .filtered(lambda r: not float_is_zero(r.total_amount, precision_rounding=(r.currency_id or self.env.company.currency_id).rounding))
        res = expense_line_ids.action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode == 'own_account' and expense_line_ids:
            self.write({'state': 'post'})
        else:
            self.write({'state': 'post'})
            #self.write({'state': 'done'})
        self.activity_update()

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'hr.expense.sheet')]).id
        users = self.env['account.send.notif'].search([], limit=1)    
        for sheet in self:
            for user in users:
                if user.accountant_exp.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': sheet.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.accountant_exp.id,
                                    'note': 'Expenses has been posted and needs to be paid.'
                                    })                 
                    ok=self.id_activity.action_done()                                
                    self.id_activity = line.id 

        return res





class HrExpenseSheetRegisterPaymentWizardup(models.TransientModel):
    _name = 'hr.expense.sheet.register.payment.wizard'
    _inherit = ['hr.expense.sheet.register.payment.wizard', 'mail.thread', 'mail.activity.mixin']

    amount = fields.Monetary(string='Payment Amount', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Payee', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    journal_id = fields.Many2one('account.journal', string='Payment Institutions', required=True, domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
    wt_exp_total = fields.Monetary(string='Witholding Tax expenses', compute='_compute_tax_expense', readonly=True)


    @api.onchange('partner_id')
    def _onchange_partner_id1(self):
        self.communication = self.expense_sheet_id.name

    @api.onchange('expense_sheet_id')
    def _onchange_partner_id2(self):
        expense_sheet = self.expense_sheet_id
        if expense_sheet.partner19 == True:
            self.partner_id = expense_sheet.partner_id1.id
        else:
            self.partner_id = expense_sheet.address_id.id or expense_sheet.employee_id.id and expense_sheet.employee_id.address_home_id.id  
    
    
    def _compute_tax_expense(self):
        expense = self.env['hr.expense'].search([('sheet_id', '=', self.expense_sheet_id.id)])
        for exp in expense:
            wt_exp = 0.0
            wt_exp = exp.untaxed_amount - exp.total_amount
            if wt_exp > 0:
                wt_exp = wt_exp
            else :
                wt_exp = 0         
            self.wt_exp_total += wt_exp

    def _get_payment_vals(self):
        """ Hook for extension """
        return {
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'partner_id': self.partner_id.id,
            'partner_bank_account_id': self.partner_bank_account_id.id,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'payment_method_id': self.payment_method_id.id,
            'amount': self.amount,
            'tclaims': self.amount,
            'disc' : 0.0,
            'typ_payment' : True,
            'check_amount_in_words' : self.check_amount_in_words,
            'currency_id': self.currency_id.id,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'expense_sheet_id':self.expense_sheet_id and self.expense_sheet_id.id or False,
            # 'wt_exp_total': self.wt_exp_total,
            'withtax': self.wt_exp_total,
            'account_move_id': self.expense_sheet_id.account_move_id.id
        }

    def expense_post_payment(self):
        self.ensure_one()
        company = self.company_id
        self = self.with_context(force_company=company.id, company_id=company.id)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.expense.sheet'].browse(active_ids)

        # Delete activity   
        activity_id = self.env['mail.activity'].search([('res_id', '=', expense_sheet.id )])
        activity_id.action_done() 

        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals())
        payment.post()

        # Log the payment in the chatter
        body = (_("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.name))
        expense_sheet.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()

        return {'type': 'ir.actions.act_window_close'}
        
        