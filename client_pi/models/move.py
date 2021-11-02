# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models,_, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
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
class AccountJournalCheque(models.Model):
    _inherit = "account.journal"
    
    check_manual_sequencing = fields.Boolean('Manual Numbering', default=False,
        help="Cheque this option if your pre-printed cheques are not numbered.")
    check_sequence_id = fields.Many2one('ir.sequence', 'Cheque Sequence', readonly=True, copy=False,
        help="Cheques numbering sequence.")
    check_next_number = fields.Char('Next Cheque Number', compute='_get_check_next_number', inverse='_set_check_next_number',
        help="Sequence number of the next printed cheque.")
    # check_printing_payment_method_selected = fields.Boolean(compute='_compute_check_printing_payment_method_selected',
    #     help="Technical feature used to know whether check printing was enabled as payment method.")    

    def _create_check_sequence(self):
        """ Create a check sequence for the journal """
        for journal in self:
            journal.check_sequence_id = self.env['ir.sequence'].sudo().create({
                'name': journal.name + _(" : Check Number Sequence"),
                'implementation': 'no_gap',
                'padding': 6,
                'number_increment': 1,
                'company_id': journal.company_id.id,
            })

    # @api.depends('inbound_payment_method_ids')
    # def _compute_check_printing_payment_method_selected(self):
    #     for journal in self:
    #         journal.check_printing_payment_method_selected = any(pm.code == 'check_printing' for pm in journal.inbound_payment_method_ids)  

    # def _default_inbound_payment_methods(self):
    #     methods = super(AccountJournalCheque, self)._default_inbound_payment_methods()
    #     return methods + self.env.ref('client_pi.account_payment_method_cheque')

    # @api.model
    # def _enable_check_printing_on_bank_journals1(self):
    #     """ Enables check printing payment method and add a check sequence on bank journals.
    #         Called upon module installation via data file.
    #     """
    #     check_printing = self.env.ref('client_pi.account_payment_method_cheque')
    #     bank_journals = self.search([('type', '=', 'bank')])
    #     for bank_journal in bank_journals:
    #         bank_journal._create_check_sequence()
    #         bank_journal.write({
    #             'inbound_payment_method_ids': [(4, check_printing.id, None)],
    #         })  

    # def action_checks_to_print1(self):
    #     return {
    #         'name': _('Checks to Print'),
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'list,form,graph',
    #         'res_model': 'account.payment',
    #         'context': dict(
    #             self.env.context,
    #             search_default_checks_to_send=1,
    #             journal_id=self.id,
    #             default_journal_id=self.id,
    #             default_payment_type='inbound',
    #             default_payment_method_id=self.env.ref('client_pi.account_payment_method_cheque').id,
    #         ),
    #     }                    

class AccountMovepi(models.Model):
    _inherit = "account.move"
    
    Pi_from = fields.Boolean(string ="Invoices / Bill from PI", default=False)
    Pi_ind = fields.Boolean(string =" Individual claims Bill from PI", default=False)
    ref = fields.Char(string='Narration', copy=False)
    ref2 = fields.Integer(string='Number', copy=False)
    ref1 = fields.Char(string='BILL :', copy=False, states={'draft': [('readonly', False)]}) 
    che = fields.Char(string='Cheque Number', copy=False)
    claimr = fields.Boolean(string ="Claim Report ?", default=False)
    verifyiud = fields.Char(string="verify user", tracking=True)
    approveiud = fields.Char(string="approver user" , tracking=True)
    sign_approv = fields.Binary(string="approve signature doctor")
    amount_discount = fields.Float(string='Discount', readonly=True, tracking=True)
    nbr = fields.Integer(string='Number of Person Loaded', states={'draft': [('readonly', False)]}, tracking=True)
    preexisting = fields.Monetary(string='Pre-existing Condition', states={'draft': [('readonly', False)]}, tracking=True)
    id_activity = fields.Many2one('mail.activity', string='activity')
    policy = fields.Many2one('res.policy', string='Policy', domain="[('partner_id', '=', partner_id)]")
    policy_id = fields.Many2one('res.policy.line', string='Policy id', domain="[('policy_id', '=', policy_id)]")
    
    invoice_payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Processed')],
        string='Payment', store=True, readonly=True, copy=False, tracking=True,
        compute='_compute_amount')

    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('approve', 'Posted'),
            ('posted', 'Approved'),
            ('verify', 'Verify'),
            ('cancel', 'Cancelled')
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft') 

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        missing_fields = set(['asset_id', 'move_ref', 'move_ref1', 'amount', 'asset_remaining_value', 'asset_depreciated_value']) - set(vals)
        if missing_fields:
            raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
        asset = vals['asset_id']
        account_analytic_id = asset.account_analytic_id
        analytic_tag_ids = asset.analytic_tag_ids
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount = current_currency._convert(vals['amount'], company_currency, asset.company_id, depreciation_date)
        move_line_1 = {
            'name': asset.name,
            'account_id': asset.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type == 'sale' else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type == 'sale' else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and - 1.0 * vals['amount_total'] or 0.0,
        }
        move_line_2 = {
            'name': asset.name,
            'account_id': asset.account_depreciation_expense_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_account_id': account_analytic_id.id if asset.asset_type in ('purchase', 'expense') else False,
            'analytic_tag_ids': [(6, 0, analytic_tag_ids.ids)] if asset.asset_type in ('purchase', 'expense') else False,
            'currency_id': company_currency != current_currency and current_currency.id or False,
            'amount_currency': company_currency != current_currency and vals['amount_total'] or 0.0,
        }
        move_vals = {
            'ref': vals['move_ref'],
            'ref2': vals['move_ref1'],
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'auto_post': asset.state == 'open',
            'asset_id': asset.id,
            'asset_remaining_value': vals['asset_remaining_value'],
            'asset_depreciated_value': vals['asset_depreciated_value'],
            'amount_total': amount,
            'name': '/',
            'asset_value_change': vals.get('asset_value_change', False),
            'type': 'entry',
        }
        return move_vals


    def send_email_from(self):
        outmails = self.env['ir.mail_server'].search([])
        for outmail in outmails:
            smtpuser = outmail.smtp_user

        return smtpuser 

    def action_approve(self):
        self.write({'state': 'posted'})
        self.write({'approveiud': self.env.user.name}) 
        if self.env.user.is_sign == True:
            self.write({'sign_approv': self.env.user.sign})   

    def action_post(self):
        res = super(AccountMovepi, self).action_post()
        journal_posted = self.env['hr.payslip'].sudo().search([('move_id', '=', self.id)], limit=1)
        payslip_run_id = self.env['hr.payslip'].sudo().search([('move_id', '=', self.id)], limit=1).payslip_run_id.id
        id_journal_posted = self.env['hr.payslip.run'].sudo().search([('id', '=', payslip_run_id)], limit=1)
        if id_journal_posted :
            for jp in id_journal_posted:
                if jp.journal_posted != True:
                    jp.journal_posted = True

                    date = datetime.datetime.now().date()
                    mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
                    model_id = self.env['ir.model'].search([('model', '=', 'hr.payslip.run')]).id
                    users = self.env['account.send.notif'].search([], limit=1)    
                    for mov in self:
                        compte = 0
                        payslips = self.env['hr.payslip'].sudo().search([('move_id', '=', mov.id)])
                        for payslip in payslips:
                            payslip.state = "voucher"
                            run_pay = payslip.payslip_run_id
                        compte += 1
                        _logger.info("compte=== '" + str(compte) + "' ok !")
                    if compte == 1:  
                        for user in users:
                            if user.finance_officer.id:
                                    line = self.env['mail.activity'].create({
                                                    'res_model_id': model_id, 
                                                    'res_id': run_pay,
                                                    'activity_type_id': mail_id, 
                                                    'date_deadline': date, 
                                                    'user_id': user.finance_officer.id,
                                                    'note': 'Draf entry has been posted and needs to create voucher.'
                                                    })   
                                    runs = self.env['hr.payslip.run'].sudo().search([('id', '=', run_pay.id)])                
                                    for run in runs:
                                        run.id_activity = line.id                              
                                    ok=self.id_activity.action_done()  
                else:
                    raise ValidationError(" The journal entries is already posteddddddddddd !")
        
        elif journal_posted:
            for jpd in journal_posted:
                if jpd.journal_posted != True:
                    jpd.journal_posted = True
                    jpd.state = "voucher"
                    date = datetime.datetime.now().date()
                    mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
                    model_id = self.env['ir.model'].search([('model', '=', 'hr.payslip')]).id
                    users = self.env['account.send.notif'].search([], limit=1)    
                    for mov in self:
                        for user in users:
                            if user.finance_officer.id:
                                line = self.env['mail.activity'].create({
                                                'res_model_id': model_id, 
                                                'res_id': jpd.id,
                                                'activity_type_id': mail_id, 
                                                'date_deadline': date, 
                                                'user_id': user.finance_officer.id,
                                                'note': 'Draf entry has been posted and needs to create voucher.'
                                                })   
                                jpd.id_activity = line.id                              
                                ok=self.id_activity.action_done()   

                else:         
                    raise ValidationError(" The journal entries is already posted !!!!!!!!!!!!!!!!!!")

        if self.type not in ("entry","in_invoice","in_refund"):
            self.write({'state': 'approve'})

        if self.type == "in_invoice":
            date = datetime.datetime.now().date()
            mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')]).id
            users = self.env['account.send.notif'].search([], limit=1)    
            for mov in self:
                for user in users:
                    if user.accountant.id:
                        line = self.env['mail.activity'].create({
                                        'res_model_id': model_id, 
                                        'res_id': mov.id,
                                        'activity_type_id': mail_id, 
                                        'date_deadline': date, 
                                        'user_id': user.accountant.id,
                                        'note': 'claims has been approved and needs to be paid.'
                                        })                 
                        self.id_activity = line.id
            

        return res

    def action_validate(self):
        self.write({'verifyiud': self.env.user.name})    
        self.write({'state': 'verify'})
        if self.type == "entry":
            date = datetime.datetime.now().date()
            mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
            model_id = self.env['ir.model'].search([('model', '=', 'account.move')]).id
            users = self.env['account.send.notif'].search([], limit=1)    
            for mov in self:
                for user in users:
                    if user.cfo.id:
                        line = self.env['mail.activity'].create({
                                        'res_model_id': model_id, 
                                        'res_id': mov.id,
                                        'activity_type_id': mail_id, 
                                        'date_deadline': date, 
                                        'user_id': user.cfo.id,
                                        'note': 'Draft entry has been validated and needs to be post.'
                                        })                              
                        self.id_activity = line.id
                    
                    payslips = self.env['hr.payslip'].search([])   
                    for pay in payslips: 
                        activity_id = self.env['mail.activity'].search([('id', '=', pay.id_activity.id ),('res_id', '=', pay.move_id.id)])
                        activity_id.action_done()    

class AccountMoveLineB(models.Model):
    _inherit = 'account.move.line'
    
    claimid = fields.Integer("claimid")
    claimid1 = fields.Float("claimid", default = 0.0)
    taxr = fields.Boolean(string ="Tax Report ?", default=False)
    paym = fields.Boolean(string ="mark pay on PI", default=False)
    fecth = fields.Boolean(string ="mark fetch on PI obselette", default=False)
    fecth12 = fields.Boolean(string ="mark fetch on PI tru", default=False)
    claim_paid = fields.Boolean(string ="Claim Paid ?", default=False)
    paid_claim = fields.Boolean(string ="Paid Claim?", default=False)
    dateclaims = fields.Date(string='Date')
    balance = fields.Monetary(string='Balance', readonly=True, tracking=True)
    tax_amount = fields.Monetary(string='Tax Amount', tracking=True, compute='_onchange_tax'
    , currency_field='always_set_currency_id')
    typ = fields.Selection(selection=[
        ('principal', 'Principal'),
        ('spouses', 'Spouses'),
        ('dep_a', 'Adult Dependant'),
        ('child', 'Child'),
        ('preexising', 'Preexisting')],
        default='principal', string='Type',tracking=True)
    # quantity = fields.Integer(
    #     string='Quantity',
    #     default=1, digits='Product Unit of Measure',
    #     help="The optional quantity expressed by this line, eg: number of product sold. "
    #     "The quantity is not a legal requirement but is very useful for some reports.")

    def claimid(self):
        moves = self.env['account.move'].search([('type', '=', 'in_invoice'),('Pi_from','=',True)])
        for move in moves:
            #_logger.debug(rsd, line_id.fecth)
            line = self.env['account.move.line'].search([('move_id', '=', move.id)])
            for ids in line:
                if ids.claimid > 0:
                    ids.claimid1 = float(ids.claimid)

    @api.depends('quantity','price_unit','tax_ids','price_subtotal')
    def _onchange_tax(self):
        for line in self:
            line.tax_amount = 0
            qt = line.quantity 
            pu = line.price_unit
            price = line.price_subtotal
            if qt and pu and price:
                for tax in line.tax_ids:
                    if tax.price_include == True: 
                        line.tax_amount = abs((qt * pu) - price)
                    elif tax.price_include == False:
                        line.tax_amount = abs((tax.amount * price) / 100)


class MailThreadA(models.AbstractModel):
    _inherit = 'mail.thread'

    def send_email_from(self):
        outmails = self.env['ir.mail_server'].sudo().search([])
        for outmail in outmails:
            smtpuser = outmail.smtp_user

        return smtpuser  

    def _message_compute_author(self, author_id=None, email_from=None, raise_exception=True):
        """ Tool method computing author information for messages. Purpose is
        to ensure maximum coherence between author / current user / email_from
        when sending emails. """
        if author_id is None:
            if email_from:
                author = self._mail_find_partner_from_emails([email_from])[0]
            else:
                author = self.env.user.partner_id
                email_from = self.sudo().send_email_from()
            author_id = author.id

        if email_from is None:
            if author_id:
                author = self.env['res.partner'].browse(author_id)
                email_from = self.sudo().send_email_from()

        # superuser mode without author email -> probably public user; anyway we don't want to crash
        if not email_from and not self.env.su and raise_exception:
            raise exceptions.UserError(_("Unable to log message, please configure the sender's email address."))

        return {
            'author_id': author_id,
            'email_from': email_from,
        }

