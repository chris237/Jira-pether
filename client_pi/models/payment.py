# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models, tools, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
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

class AccountPaymentabc(models.Model):
    _inherit = "account.payment"
    
    amount = fields.Monetary(string='Total', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    withtax = fields.Monetary(string='Withholding Tax', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    disc = fields.Monetary(string='Discount', required=True, readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    tclaims = fields.Monetary(string='Net Amount', required=True, readonly=True, tracking=True)
    communication = fields.Char(string='Reference', readonly=True, states={'draft': [('readonly', False)]})
    typ_payment = fields.Boolean(string='Type of Payment', default=False)
    expense_sheet_id = fields.Many2one('hr.expense.sheet', string="Expense Report")
    contribution_id = fields.Many2one('hr.contribution', string="contribution Report")
    wt_exp_total = fields.Monetary(string='Witholding Tax expenses', readonly=True)
    account_move_id = fields.Many2one('account.move', string='Journal Entry')
    id_activity = fields.Many2one('mail.activity', string='activity')
    check_number1 = fields.Char(string="Check Number")
    
    # tclaims_amount_in_words = fields.Char(string="Amount in Words")
    check_number = fields.Char(string="Cheque Number", readonly=True, copy=False,
        help="The selected journal is configured to print check numbers. If your pre-printed check paper already has numbers "
             "or if the current numbering is wrong, you can change it in the journal configuration page.")
    prepa = fields.Char(string="prepare user" , default=' ISHMAEL AHINSAH' , tracking=True)
    approveiud = fields.Char(string="approver user" , tracking=True)
    verifyiud = fields.Char(string="verify user", default=' ERNEST', tracking=True)
    available_advice = fields.Boolean(string='Payment Advice Generated ?',
                                help='If this box is checked which means that Payment Advice exists for current batch',
                                readonly=True, copy=False)
    gros = fields.Monetary(string='Gross Amount', tracking=True, compute='_onchange_gros_amount')
    sign_prep = fields.Binary(string="Prepare signature")
    sign_appro = fields.Binary(string="approve signature")
    sign_verif = fields.Binary(string="verify signature")
    state = fields.Selection(
        [('draft', 'Draft'), 
         ('posted', 'Submitted'), 
         ('done', 'Verified'), 
         ('approve', 'Approved'), 
         ('sent', 'sent'), 
         ('reconciled', 'Reconciled'), 
         ('cancelled', 'Cancelled')
         ], readonly=True, default='draft', copy=False, string="Status", tracking=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')

    def _check_fill_line(self, amount_str):
        return amount_str and (amount_str + ' Only') or ''

    # def _check_communication(self, payment_method_id, communication):
    #     super(AccountPaymentabc, self)._check_communication(payment_method_id, communication)
    #     if payment_method_id == self.env.ref('account_check_printing.account_payment_method_check').id:
    #         if not communication:
    #             return
    #         if len(communication) > 60:
    #             raise ValidationError(_("A check memo cannot exceed 60 characters."))
    #     elif payment_method_id == self.env.ref('client_pi.account_payment_method_cheque').id:
    #         if not communication:
    #             return
    #         if len(communication) > 60:
    #             raise ValidationError(_("A check memo cannot exceed 60 characters."))
    

    @api.depends('withtax','amount')
    def _onchange_gros_amount(self):
        for line in self:
            line.gros = line.amount
            if line.withtax:
                line.gros += line.withtax
                line.gros += line.disc
                # line.gros += line.disc

    @api.constrains('amount','tclaims')
    def _check_amount(self):
        for payment in self:
            if payment.amount < 0:
                raise ValidationError(_('The payment amount cannot be negative.'))
            if payment.amount > payment.tclaims:
                raise Warning(_('The Amount Being Paid cannot be greater than the Net Amount'))

    def _compute_attachment_number(self):
        self.attachment_number = self.expense_sheet_id.attachment_number
        # for sheet in self.expense_sheet_id.id:
        #     sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))
        # sheet_id = self.expense_sheet_id
        # for lines in sheet_id:
        #     for line in lines:
        #         expense_sheet_id = self.env['hr.expense.sheet'].search([('id', '=', line)])
        #         if expense_sheet_id:
        #             for sheet in expense_sheet_id:
        #                 sheet.attachment_number = sum(sheet.expense_line_ids.mapped('attachment_number'))

    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.expense'), ('res_id', 'in', self.expense_sheet_id.expense_line_ids.ids)]
        res['context'] = {
            'default_res_model': 'hr.expense.sheet',
            'default_res_id': self.expense_sheet_id.id,
            'create': False,
            'edit': False,
        }
        return res

    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        res = super(AccountPaymentabc, self).post()
        
        

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'account.payment')]).id
        users = self.env['account.send.notif'].search([], limit=1)
        # _logger.info("mail=== '" + str(mail_id) + "' ok !")
        for payment in self:
            if payment.partner_type == "supplier":
                for user in users:
                    if user.auditor.id:
                        line = self.env['mail.activity'].create({
                                        'res_model_id': model_id, 
                                        'res_id': payment.id,
                                        'activity_type_id': mail_id, 
                                        'date_deadline': date, 
                                        'user_id': user.auditor.id,
                                        'note': 'Payment needs to be verified.'
                                        })
                        self.id_activity = line.id 
                        activity_id = self.env['mail.activity'].search([('res_id', '=', payment.account_move_id.id ),('user_id', '=', user.accountant.id)])
                        activity_id.action_done()               
                        # ok=self.id_activity.action_done()
            # else:
            #     payment_method_cheq = self.env.ref('client_pi.account_payment_method_cheque')
            #     for payment in self.filtered(lambda p: p.payment_method_id == payment_method_cheq and p.check_manual_sequencing):
            #         sequence = payment.journal_id.check_sequence_id
            #         payment.check_number = sequence.next_by_id()
                    
        self.write({'prepa': self.env.user.name})
        if self.env.user.is_sign == True:
            self.write({'sign_prep': self.env.user.sign})

        return res

    '''@api.onchange('tclaims', 'currency_id')
    def _onchange_tclaims(self):
        res = super(AccountPaymentabc, self)._onchange_tclaims()
        self.tclaims_amount_in_words = self.currency_id.amount_to_text(self.tclaims) if self.currency_id else ''
        return res  '''

    def approve(self):
        self.write({'state': 'approve'})
        if self.env.user.is_sign == True:
            self.write({'sign_appro': self.env.user.sign})

        ok=self.id_activity.action_done()    

        # users = self.env['account.send.notif'].search([], limit=1)
        # for payment in self:
        #     if payment.partner_type == "supplier":
        #         for user in users:
        #             activity_id = self.env['mail.activity'].search([('res_id', '=', payment.id ),('user_id', '=', user.ceo.id)])
        #             activity_id.action_done()     

    def verify(self):
        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'account.payment')]).id
        users = self.env['account.send.notif'].search([], limit=1)
        for payment in self:
            if payment.partner_type == "supplier":
                for user in users:
                    if user.ceo.id:
                        line = self.env['mail.activity'].create({
                                        'res_model_id': model_id, 
                                        'res_id': payment.id,
                                        'activity_type_id': mail_id, 
                                        'date_deadline': date, 
                                        'user_id': user.ceo.id,
                                        'note': 'claims are pending for them to be approved.'
                                        })
                        ok=self.id_activity.action_done()                
                        self.id_activity = line.id                
                    # activity_id = self.env['mail.activity'].search([('res_id', '=', payment.id ),('user_id', '=', user.auditor.id)])
                    # activity_id.action_done()

        self.write({'state': 'done'})
        self.write({'verifyiud': self.env.user.name})
        if self.env.user.is_sign == True:
            self.write({'sign_verif': self.env.user.sign})
        
    def unmark_sent(self):
        self.write({'state': 'approve'})
        # self.unlink({'sign_appro': 'approve'})

    @api.onchange('invoice_ids')
    def _onchange_tax_discount(self):
        discount = 0.0
        tax = 0.0
        montant = 0.0
        for line in self.invoice_ids:
            self.id_activity = line.id_activity.id
            discount += line.amount_discount 
            tax += line.amount_tax
            if tax < 0:
                tax = tax
            else:
                tax = 0    
            montant += line.amount_total 
        self.disc = discount
        self.withtax = abs(tax)
        self.tclaims = montant
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.bank_id = self.company_id.partner_id.bank_ids and self.company_id.partner_id.bank_ids[0].bank_id.id or False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.partner_bank_id = self.partner_id.bank_ids and self.partner_id.bank_ids[0].bank_id.id or False
        if self.invoice_ids and self.invoice_ids[0].invoice_partner_bank_id:
            self.partner_bank_account_id = self.invoice_ids[0].invoice_partner_bank_id
        elif self.partner_id != self.partner_bank_account_id.partner_id:
            # This condition ensures we use the default value provided into
            # context for partner_bank_account_id properly when provided with a
            # default partner_id. Without it, the onchange recomputes the bank account
            # uselessly and might assign a different value to it.
            if self.partner_id and len(self.partner_id.bank_ids) > 0:
                self.partner_bank_account_id = self.partner_id.bank_ids[0]
            elif self.partner_id and len(self.partner_id.commercial_partner_id.bank_ids) > 0:
                self.partner_bank_account_id = self.partner_id.commercial_partner_id.bank_ids[0]
            else:
                self.partner_bank_account_id = False
        return {'domain': {'partner_bank_account_id': [('partner_id', 'in', [self.partner_id.id, self.partner_id.commercial_partner_id.id])]}}
 
    # Affiche du journal lorsqu'on debit account payable et credit bank sur 1 ligne 
    def get_journal_itemss(self):
        result = []
        service_type=acc_deb=acc_cred=product_name=False
        am_deb=am_cred=0.0
        for j in self.move_line_ids:
            # for l in self.expense_sheet_id.expense_line_ids:
            #     if l.name:
            #         product_name = l.name
            # service_type = product_name and product_name or j.move_name
            if j.debit!=0.0:
                service_type = j.account_id.name
                am_deb = j.debit
                acc_deb = j.account_id.code
            elif j.credit != 0.0:
                am_cred = j.credit
                acc_cred = j.account_id.code
        if service_type:
            res = ({
                'service_type1': service_type,  
                'account_debited1': acc_deb, 
                'amount_d1': am_deb,
                'account_credited1': acc_cred,
                'amount_c1': am_cred
                })
            result.append(res)
        return result

    # Affiche du journal lorsqu'on debit account expense et credit account payable
    def get_journal_items(self):
        result = []
        service_type=compte=acc_deb=acc_cred=product_name=False
        am_deb=am_cred=0.0
        journal_items = self.env['account.move.line'].search([('move_id', '=', self.account_move_id.id)])
        for l in journal_items:
            product_id = self.env['hr.expense'].search([('id', '=',l.expense_id.id)]).product_id.id
            product_tmpl_id = self.env['product.product'].search([('id', '=',product_id)]).product_tmpl_id
              
            if l.name == "WT 3%":
                product_name = l.name
                # service_type = product_name and product_name or l.move_name
                service_type = l.account_id.name + "  ( " + product_name + "  )" 
                if l.credit != 0.0:
                    am_deb = "-"
                    acc_deb = "-" 
                    am_cred = l.credit
                    acc_cred = l.account_id.code 
                    compte = acc_cred
            elif l.name == "WT 3% -ADMIN":
                product_name = l.name
                # service_type = product_name and product_name or l.move_name
                service_type = l.account_id.name + "  ( " + product_name + "  )"
                if l.credit != 0.0:
                    am_deb = "-"
                    acc_deb = "-" 
                    am_cred = l.credit
                    acc_cred = l.account_id.code 
                    compte = acc_cred
            elif l.name == "WT 7.5% -ADMIN":
                product_name = l.name
                # service_type = product_name and product_name or l.move_name
                service_type = l.account_id.name + "  ( " + product_name + "  )"
                if l.credit != 0.0:
                    am_deb = "-"
                    acc_deb = "-" 
                    am_cred = l.credit
                    acc_cred = l.account_id.code 
                    compte = acc_cred 
            elif l.name == "WT 20%":
                product_name = l.name
                # service_type = product_name and product_name or l.move_name
                service_type = l.account_id.name + "  ( " + product_name + "  )"
                if l.credit != 0.0:
                    am_deb = "-"
                    acc_deb = "-" 
                    am_cred = l.credit
                    acc_cred = l.account_id.code 
                    compte = acc_cred               
            else:    
                product_name = product_tmpl_id.name
                if l.debit!=0.0:
                    # service_type = product_name and product_name or l.move_name
                    service_type = l.account_id.name
                    am_deb = l.debit
                    acc_deb = l.account_id.code
                    am_cred = "-"
                    acc_cred = "-" 
                    compte = acc_deb
                elif l.credit != 0.0:
                    service_type = l.account_id.name
                    am_deb = "-"
                    acc_deb = "-" 
                    am_cred = l.credit
                    acc_cred = l.account_id.code 
                    compte = acc_cred   
            res = ({
                'service_type': str(compte) +"  "+ str(service_type),  
                'account_debited': acc_deb, 
                'amount_d': am_deb,
                'account_credited': acc_cred,
                'amount_c': am_cred
                })
            if res not in result:
                result.append(res)        
        return result

    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPaymentabc, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))

        # Check all invoices are open
        if not invoices or any(invoice.state != 'posted' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # Check if, in batch payments, there are not negative invoices and positive invoices
        dtype = invoices[0].type
        for inv in invoices[1:]:
            if inv.type != dtype:
                if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
                        (dtype == 'in_invoice' and inv.type == 'in_refund')):
                    raise UserError(_("You cannot register payments for vendor bills and supplier refunds at the same time."))
                if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
                        (dtype == 'out_invoice' and inv.type == 'out_refund')):
                    raise UserError(_("You cannot register payments for customer invoices and credit notes at the same time."))

        amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id, rec.get('payment_date') or fields.Date.today())
        amount1 = self._compute_payment_amount1(invoices, invoices[0].currency_id, invoices[0].journal_id, rec.get('payment_date') or fields.Date.today())
        tclaims = self._compute_payment_tclaims(invoices, invoices[0].currency_id, invoices[0].journal_id, rec.get('payment_date') or fields.Date.today())
        rec.update({
            'currency_id': invoices[0].currency_id.id,
            'payment_type': ('inbound' if amount1 > 0 else 'outbound'),
            'amount': abs(amount),
            'tclaims': abs(tclaims),
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
            'account_move_id': invoices[0].id,
            'invoice_ids': [(6, 0, invoices.ids)],
        })
        return rec

    @api.model
    def _compute_payment_discount(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.

        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['discount', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
            SELECT
                move.type AS type,
                move.currency_id AS currency_id,
                SUM(line.discount) AS discount,
                SUM(line.amount_residual_currency) AS residual_currency
            FROM account_move move
            LEFT JOIN account_move_line line ON line.move_id = move.id
            LEFT JOIN account_account account ON account.id = line.account_id
            LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
            WHERE move.id IN %s
            AND account_type.type IN ('receivable', 'payable')
            GROUP BY move.id, move.type
        ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        for res in query_res:
            move_currency = self.env['res.currency'].browse(res['currency_id'])
            if move_currency == currency and move_currency != company.currency_id:
                total += res['residual_currency']
            else:
                total += company.currency_id._convert(res['discount'], currency, company, date)
        return total
    
    @api.model
    def _compute_payment_tclaims(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.

        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['amount_total', 'type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
            SELECT
                move.type AS type,
                move.currency_id AS currency_id,
                SUM(move.amount_total) AS amount_total,
                SUM(line.amount_residual_currency) AS residual_currency
            FROM account_move move
            LEFT JOIN account_move_line line ON line.move_id = move.id
            LEFT JOIN account_account account ON account.id = line.account_id
            LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
            WHERE move.id IN %s
            AND account_type.type IN ('receivable', 'payable')
            GROUP BY move.id, move.type
        ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        for res in query_res:
            move_currency = self.env['res.currency'].browse(res['currency_id'])
            if move_currency == currency and move_currency != company.currency_id:
                total += res['residual_currency']
            else:
                total += company.currency_id._convert(res['amount_total'], currency, company, date)
        return total

    @api.model
    def _compute_payment_amount1(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.

        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
            SELECT
                move.type AS type,
                move.currency_id AS currency_id,
                SUM(line.amount_residual) AS amount_residual,
                SUM(line.amount_residual_currency) AS residual_currency
            FROM account_move move
            LEFT JOIN account_move_line line ON line.move_id = move.id
            LEFT JOIN account_account account ON account.id = line.account_id
            LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
            WHERE move.id IN %s
            AND account_type.type IN ('receivable', 'payable')
            GROUP BY move.id, move.type
        ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        discount = 0.0
        for res in query_res:
            move_currency = self.env['res.currency'].browse(res['currency_id'])
            if move_currency == currency and move_currency != company.currency_id:
                total += res['residual_currency']
            else:
                total += company.currency_id._convert(res['amount_residual'], currency, company, date)
        return total


    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        '''Compute the total amount for the payment wizard.

        :param invoices:    Invoices on which compute the total as an account.invoice recordset.
        :param currency:    The payment's currency as a res.currency record.
        :param journal:     The payment's journal as an account.journal record.
        :param date:        The payment's date as a datetime.date object.
        :return:            The total amount to pay the invoices.
        '''
        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        if not invoices:
            return 0.0

        self.env['account.move'].flush(['type', 'currency_id'])
        self.env['account.move.line'].flush(['amount_residual', 'amount_residual_currency', 'move_id', 'account_id'])
        self.env['account.account'].flush(['user_type_id'])
        self.env['account.account.type'].flush(['type'])
        self._cr.execute('''
            SELECT
                move.type AS type,
                move.currency_id AS currency_id,
                SUM(move.amount_residual) AS amount_residual,
                SUM(line.amount_residual_currency) AS residual_currency
            FROM account_move move
            LEFT JOIN account_move_line line ON line.move_id = move.id
            LEFT JOIN account_account account ON account.id = line.account_id
            LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
            WHERE move.id IN %s
            AND account_type.type IN ('receivable', 'payable')
            GROUP BY move.id, move.type
        ''', [tuple(invoices.ids)])
        query_res = self._cr.dictfetchall()

        total = 0.0
        discount = 0.0
        for res in query_res:
            if res['type'] == 'in_invoice':
                move_currency = self.env['res.currency'].browse(res['currency_id'])
                if move_currency == currency and move_currency != company.currency_id:
                    total -= res['residual_currency']
                else:
                    total -= company.currency_id._convert(res['amount_residual'], currency, company, date)
            else:
                move_currency = self.env['res.currency'].browse(res['currency_id'])
                if move_currency == currency and move_currency != company.currency_id:
                    total += res['residual_currency']
                else:
                    total += company.currency_id._convert(res['amount_residual'], currency, company, date)
        return total



class payment_registerabc(models.TransientModel):
    _inherit = 'account.payment.register'
    
    # def _prepare_payment_vals(self, invoices):
    #     res = super(payment_registerabc, self)._prepare_payment_vals(invoices)
    #     if self.payment_method_id == self.env.ref('client_pi.account_payment_method_cheque'):
    #         currency_id = self.env['res.currency'].browse(res['currency_id'])
    #         res.update({
    #             'check_amount_in_words': currency_id.amount_to_text(res['amount']),
    #         })
    #     return res
    
    
    def _prepare_payment_vals(self, invoices):
        '''Create the payment values.

        :param invoices: The invoices/bills to pay. In case of multiple
            documents, they need to be grouped by partner, bank, journal and
            currency.
        :return: The payment values as a dictionary.
        '''
        amount = self.env['account.payment']._compute_payment_amount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
        amount1 = self.env['account.payment']._compute_payment_amount1(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
        tclaims = self.env['account.payment']._compute_payment_tclaims(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
        disc = self.env['account.payment']._compute_payment_discount(invoices, invoices[0].currency_id, self.journal_id, self.payment_date)
        values = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': " ".join(i.invoice_payment_ref or i.ref or i.name for i in invoices),
            'account_move_id': invoices[0].id,
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_type': ('inbound' if amount1 > 0 else 'outbound'),
            'amount': abs(amount),
            #taxes': abs(taxes),
            'tclaims': abs(tclaims),
            'disc': abs(disc),
            'currency_id': invoices[0].currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'partner_bank_account_id': invoices[0].invoice_partner_bank_id.id,
        }
        return values    
  
class Currency1(models.Model):
    _inherit = "res.currency"     

    def amount_to_text(self, amount):
        self.ensure_one()
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        formatted = "%.{0}f".format(self.decimal_places) % amount
        parts = formatted.partition('.')
        integer_value = int(parts[0])
        fractional_value = int(parts[2] or 0)

        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].with_context(active_test=False).search([('code', '=', lang_code)])
        if amount > 1:
            amount_words = tools.ustr('{amt_value} {amt_word}').format(
                            amt_value=_num2words(integer_value, lang=lang.iso_code),
                            amt_word='Ghana ' + self.currency_unit_label+'s',
                            )
        else :
            amount_words = tools.ustr('{amt_value} {amt_word}').format(
                            amt_value=_num2words(integer_value, lang=lang.iso_code),
                            amt_word=self.currency_unit_label,
                            )                    
        if not self.is_zero(amount - integer_value):
            amount_words += ' ' + _('and') + tools.ustr(' {amt_value} {amt_word}').format(
                        amt_value=_num2words(fractional_value, lang=lang.iso_code),
                        amt_word=self.currency_subunit_label,
                        )
        return amount_words