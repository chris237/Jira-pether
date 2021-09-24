# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"


    discount_type = fields.Selection(
        [('percent', 'Percentage'), 
        ('amount', 'Amount')], 
        string='Discount Type',
        readonly=True, 
        states={'draft': [('readonly', False)]}, 
        default='percent')
    discount_rate = fields.Float('Discount Amount', 
                                    digits=(16, 2), 
                                    readonly=True,
                                    states={'draft': [('readonly', False)]})
    amount_discount = fields.Monetary(string='Discount', 
                                        store=True, 
                                        readonly=True, 
                                        compute='_compute_amount',
                                        track_visibility='always')

    ks_enable_discount = fields.Boolean(compute='ks_verify_discount')
    ks_preexisting_account = fields.Integer(compute='ks_verify_discount')
    ks_sales_discount_account_id = fields.Integer(compute='ks_verify_discount')
    ks_purchase_discount_account_id = fields.Integer(compute='ks_verify_discount')


    @api.depends('company_id.ks_enable_discount')
    def ks_verify_discount(self):
        for rec in self:
            rec.ks_enable_discount = rec.company_id.ks_enable_discount
            rec.ks_preexisting_account = rec.company_id.ks_preexisting_account.id
            rec.ks_sales_discount_account_id = rec.company_id.ks_sales_discount_account.id
            rec.ks_purchase_discount_account_id = rec.company_id.ks_purchase_discount_account.id


    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'discount_type',
        'preexisting',
        'discount_rate')
    def _compute_amount(self):
        super(AccountInvoice, self)._compute_amount()
        for rec in self:
            if not ('ks_global_tax_rate' in rec):
                rec.ks_calculate_discount()
            sign = rec.type in ['in_refund', 'out_refund'] and -1 or 1
            rec.amount_total_company_signed = rec.amount_total * sign
            rec.amount_total_signed = rec.amount_total * sign

    # @api.multi
    def ks_calculate_discount(self):
        for rec in self:
            if rec.discount_type == "amount":
                rec.amount_discount = rec.discount_rate if rec.amount_untaxed > 0 else 0
            elif rec.discount_type == "percent":
                if rec.discount_rate != 0.0:
                    rec.amount_discount = (rec.amount_untaxed + rec.amount_tax) * rec.discount_rate / 100
                else:
                    rec.amount_discount = 0
            elif not rec.discount_type:
                rec.discount_rate = 0
                rec.amount_discount = 0
            for line in rec.line_ids:
                if line.typ == 'preexising' :
                    line.price_unit = rec.preexisting
                    line.credit = rec.preexisting
                '''for line in rec.invoice_line_ids:
                    if line.name == "Preexisting Conditions" :
                        line.price_unit = rec.preexisting
                        line.credit = rec.preexisting'''
            if rec.type in ('in_invoice', 'out_invoice'):
                rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.amount_discount + rec.preexisting
            rec.ks_update_universal_discount()

    @api.constrains('discount_rate')
    def ks_check_discount_value(self):
        if self.discount_type == "percent":
            if self.discount_rate > 100 or self.discount_rate < 0:
                raise ValidationError('You cannot enter percentage value greater than 100.')
        else:
            if self.discount_rate < 0 or self.amount_untaxed < 0:
                raise ValidationError(
                    'You cannot enter discount amount greater than actual cost or value lower than 0.')

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
        ks_res = super(AccountInvoice, self)._prepare_refund(invoice, date_invoice=None, date=None,
                                                                      description=None, journal_id=None)
        ks_res['discount_rate'] = self.discount_rate
        ks_res['discount_type'] = self.discount_type
        ks_res['preexisting'] = self.preexisting
        return ks_res

    def ks_update_universal_discount(self):
        """This Function Updates the Universal Discount through Sale Order"""
        for rec in self:

            already_exists = self.line_ids.filtered(
                lambda line: line.name and line.name.find('Universal Discount') == 0)
            terms_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            other_lines = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))

            '''already_exists1 = self.line_ids.filtered(
                lambda line: line.name and line.name.find('Pre-existing Conditions') == 0)
            terms_lines1 = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            other_lines1 = self.line_ids.filtered(
                lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))'''

            if already_exists:
                amount = rec.amount_discount
                if rec.ks_sales_discount_account_id \
                        and (rec.type == "out_invoice"
                             or rec.type == "out_refund") \
                        and amount > 0:
                    if rec.type == "out_invoice":
                        already_exists.update({
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        })
                    else:
                        already_exists.update({
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        })
                if rec.ks_purchase_discount_account_id \
                        and (rec.type == "in_invoice"
                             or rec.type == "in_refund") \
                        and amount > 0:
                    if rec.type == "in_invoice":
                        already_exists.update({
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        })
                    else:
                        already_exists.update({
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        })
                total_balance = sum(other_lines.mapped('balance'))
                total_amount_currency = sum(other_lines.mapped('amount_currency'))
                if not sum(terms_lines.mapped('debit')) == rec.amount_total_signed:
                    discount_percent = 0.0
                    total_discount = 0.0
                    for record in range(0, len(terms_lines)):
                        if len(self.invoice_payment_term_id.line_ids) >= len(terms_lines):
                            if self.invoice_payment_term_id.line_ids[record].value_amount:
                                total_discount += self.invoice_payment_term_id.line_ids[record].value_amount
                            else:
                                discount_percent = 100 - total_discount
                            terms_lines[record].update({
                                'amount_currency': -total_amount_currency,
                                'debit': (self.amount_total * (self.invoice_payment_term_id.line_ids[
                                                                   record].value_amount if not discount_percent else discount_percent) / 100) if total_balance < 0.0 else 0.0,
                                'credit': ((self.amount_total * self.invoice_payment_term_id.line_ids[
                                    record].value_amount) / 100) if total_balance > 0.0 else 0.0
                            })
                        else:
                            terms_lines[record].update({
                                'amount_currency': -total_amount_currency,
                                'debit': self.amount_total if total_balance < 0.0 else 0.0,
                                'credit': self.amount_total if total_balance > 0.0 else 0.0
                            })
                else:
                    for record in terms_lines:
                        if rec.discount_type == "percent":
                            record.update({
                                'amount_currency': -total_amount_currency,
                                'debit': (record.debit - ((
                                                                  record.debit * self.discount_rate) / 100)) if total_balance < 0.0 else 0.0,
                                'credit': (record.credit - ((
                                                                    record.credit * self.discount_rate) / 100)) if total_balance > 0.0 else 0.0
                            })
                        else:
                            discount = rec.discount_rate / len(terms_lines)
                            record.update({
                                'amount_currency': -total_amount_currency,
                                'debit': (record.debit - discount) if total_balance < 0.0 else 0.0,
                                'credit': (record.credit - discount) if total_balance > 0.0 else 0.0
                            })
            if not already_exists and rec.discount_rate > 0:
                in_draft_mode = self != self._origin
                if not in_draft_mode and rec.type == 'out_invoice':
                    rec._recompute_universal_discount_lines()
                print()
            
            '''if already_exists1:
                amount = rec.preexisting
                if rec.ks_preexisting_account \
                        and (rec.type == "out_invoice"
                             or rec.type == "out_refund") \
                        and amount > 0:
                    if rec.type == "out_invoice":
                        already_exists1.update({
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        })
                    else:
                        already_exists1.update({
                            'credit': amount < 0.0 and -amount or 0.0,
                            'debit': amount > 0.0 and amount or 0.0,
                        })
                total_balance = sum(other_lines1.mapped('balance'))
                total_amount_currency = sum(other_lines1.mapped('amount_currency'))
                if not sum(terms_lines1.mapped('debit')) == rec.amount_total_signed:
                    discount_percent = 0.0
                    total_discount = 0.0
                    preexist = 0.0
                    for record in range(0, len(terms_lines1)):
                        if len(self.invoice_payment_term_id.line_ids) >= len(terms_lines1):
                            if self.invoice_payment_term_id.line_ids[record].value_amount:
                                total_discount += self.invoice_payment_term_id.line_ids[record].value_amount
                            else:
                                discount_percent = 100 - total_discount
                            terms_lines1[record].update({
                                'amount_currency': -total_amount_currency,
                                'debit': (self.amount_total * (self.invoice_payment_term_id.line_ids[
                                                                   record].value_amount if not discount_percent else discount_percent) / 100) if total_balance < 0.0 else 0.0,
                                'credit': ((self.amount_total * self.invoice_payment_term_id.line_ids[
                                    record].value_amount) / 100) if total_balance > 0.0 else 0.0
                            })
                        else:
                            terms_lines1[record].update({
                                'amount_currency': -total_amount_currency,
                                'debit': self.amount_total if total_balance < 0.0 else 0.0,
                                'credit': self.amount_total if total_balance > 0.0 else 0.0
                            })
                else:
                    for record in terms_lines1:
                        if rec.discount_type == "percent":
                            record.update({
                                'amount_currency': -total_amount_currency,
                                'debit': (record.debit - ((
                                                                  record.debit * self.discount_rate) / 100)) if total_balance < 0.0 else 0.0,
                                'credit': (record.credit - ((
                                                                    record.credit * self.discount_rate) / 100)) if total_balance > 0.0 else 0.0
                            })
                        else:
                            discount = rec.discount_rate / len(terms_lines)
                            record.update({
                                'amount_currency': -total_amount_currency,
                                'debit': (record.debit - discount) if total_balance < 0.0 else 0.0,
                                'credit': (record.credit - discount) if total_balance > 0.0 else 0.0
                            })
            if not already_exists1 and rec.preexisting >= 0:
                in_draft_mode = self != self._origin
                if not in_draft_mode and rec.type == 'out_invoice':
                    rec._recompute_universal_discount_lines1()
                print()'''

    @api.onchange('discount_rate', 'preexisting', 'discount_type', 'line_ids')
    def _recompute_universal_discount_lines(self):
        """This Function Create The General Entries for Universal Discount"""
        for rec in self:
            type_list = ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']
            if rec.discount_rate > 0 and rec.type in type_list:
                if rec.is_invoice(include_receipts=True):
                    in_draft_mode = self != self._origin
                    ks_name = "Universal Discount "
                    if rec.discount_type == "amount":
                        ks_value = "of amount #" + str(self.discount_rate)
                    elif rec.discount_type == "percent":
                        ks_value = " @" + str(self.discount_rate) + "%"
                    else:
                        ks_value = ''
                    ks_name = ks_name + ks_value
                    #           ("Invoice No: " + str(self.ids)
                    #            if self._origin.id
                    #            else (self.display_name))
                    terms_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    already_exists = self.line_ids.filtered(
                        lambda line: line.name and line.name.find('Universal Discount') == 0)
                    if already_exists:
                        amount = self.amount_discount
                        if self.ks_sales_discount_account_id \
                                and (self.type == "out_invoice"
                                     or self.type == "out_refund"):
                            if self.type == "out_invoice":
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            else:
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                        if self.ks_purchase_discount_account_id \
                                and (self.type == "in_invoice"
                                     or self.type == "in_refund"):
                            if self.type == "in_invoice":
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            else:
                                already_exists.update({
                                    'name': ks_name,
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                    else:
                        new_tax_line = self.env['account.move.line']
                        create_method = in_draft_mode and \
                                        self.env['account.move.line'].new or \
                                        self.env['account.move.line'].create

                        if self.ks_sales_discount_account_id \
                                and (self.type == "out_invoice"
                                     or self.type == "out_refund"):
                            amount = self.amount_discount
                            dict = {
                                'move_name': self.name,
                                'name': ks_name,
                                'price_unit': self.amount_discount,
                                'quantity': 1,
                                'debit': amount < 0.0 and -amount or 0.0,
                                'credit': amount > 0.0 and amount or 0.0,
                                'account_id': self.ks_sales_discount_account_id,
                                'move_id': self._origin,
                                'date': self.date,
                                'exclude_from_invoice_tab': True,
                                'partner_id': terms_lines.partner_id.id,
                                'company_id': terms_lines.company_id.id,
                                'company_currency_id': terms_lines.company_currency_id.id,
                            }
                            if self.type == "out_invoice":
                                dict.update({
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            else:
                                dict.update({
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            if in_draft_mode:
                                self.line_ids += create_method(dict)
                                # Updation of Invoice Line Id
                                duplicate_id = self.invoice_line_ids.filtered(
                                    lambda line: line.name and line.name.find('Universal Discount') == 0)
                                self.invoice_line_ids = self.invoice_line_ids - duplicate_id
                            else:
                                dict.update({
                                    'price_unit': 0.0,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                })
                                self.line_ids = [(0, 0, dict)]

                        if self.ks_purchase_discount_account_id \
                                and (self.type == "in_invoice"
                                     or self.type == "in_refund"):
                            amount = self.amount_discount
                            dict = {
                                'move_name': self.name,
                                'name': ks_name,
                                'price_unit': self.amount_discount,
                                'quantity': 1,
                                'debit': amount > 0.0 and amount or 0.0,
                                'credit': amount < 0.0 and -amount or 0.0,
                                'account_id': self.ks_purchase_discount_account_id,
                                'move_id': self.id,
                                'date': self.date,
                                'exclude_from_invoice_tab': True,
                                'partner_id': terms_lines.partner_id.id,
                                'company_id': terms_lines.company_id.id,
                                'company_currency_id': terms_lines.company_currency_id.id,
                            }

                            if self.type == "in_invoice":
                                dict.update({
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            else:
                                dict.update({
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            self.line_ids += create_method(dict)
                            # updation of invoice line id
                            duplicate_id = self.invoice_line_ids.filtered(
                                lambda line: line.name and line.name.find('Universal Discount') == 0)
                            self.invoice_line_ids = self.invoice_line_ids - duplicate_id

                    if in_draft_mode:
                        # Update the payement account amount
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        total_balance = sum(other_lines.mapped('balance'))
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        for record in terms_lines:
                            if rec.discount_type == "percent":
                                record.update({
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(record.price_total - ((
                                                                             record.price_total * rec.discount_rate) / 100)) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total - ((
                                                                            record.price_total * rec.discount_rate) / 100) if total_balance > 0.0 else 0.0
                                })
                            elif rec.discount_type == "amount":
                                discount = rec.discount_rate / len(terms_lines)
                                record.update({
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(record.price_total + discount) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total + discount if total_balance > 0.0 else 0.0
                                })
                    else:
                        terms_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        already_exists = self.line_ids.filtered(
                            lambda line: line.name and line.name.find('Universal Discount') == 0)
                        total_balance = sum(other_lines.mapped('balance')) + amount
                        total_amount_currency = sum(other_lines.mapped('amount_currency'))
                        line_ids = []
                        dict1 = {
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                        }
                        line_ids.append((1, already_exists.id, dict1))
                        dict2 = {
                            'debit': total_balance < 0.0 and -total_balance or 0.0,
                            'credit': total_balance > 0.0 and total_balance or 0.0,
                        }
                        # for records in already_exists:
                        #     records.update(dict1)
                        for record in terms_lines:
                            if rec.discount_type == "percent":
                                dict2 = {
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(record.price_total - ((
                                                                             record.price_total * rec.discount_rate) / 100)) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total - ((
                                                                            record.price_total * rec.discount_rate) / 100) if total_balance > 0.0 else 0.0
                                }
                            elif rec.discount_type == "amount":
                                discount = rec.discount_rate / len(terms_lines)
                                dict2 = {
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(
                                            record.price_total + discount) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total + discount if total_balance > 0.0 else 0.0
                                }
                            line_ids.append((1, record.id, dict2))
                        # self.line_ids = [(1, already_exists.id, dict1), (1, terms_lines.id, dict2)]
                        self.line_ids = line_ids

            elif self.discount_rate <= 0:
                already_exists = self.line_ids.filtered(
                    lambda line: line.name and line.name.find('Universal Discount') == 0)
                if already_exists:
                    self.line_ids -= already_exists
                    terms_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    other_lines = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                    total_balance = sum(other_lines.mapped('balance'))
                    total_amount_currency = sum(other_lines.mapped('amount_currency'))
                    terms_lines.update({
                        'amount_currency': -total_amount_currency,
                        'debit': total_balance < 0.0 and -total_balance or 0.0,
                        'credit': total_balance > 0.0 and total_balance or 0.0,
                    })


    # @api.onchange('preexisting', 'line_ids')
    def _recompute_universal_discount_lines1(self):
        """This Function Create The General Entries for Universal Discount"""
        for rec in self:
            type_list = ['out_invoice', 'out_refund']
            if rec.preexisting >= 0 and rec.type in type_list:
                if rec.is_invoice(include_receipts=True):
                    in_draft_mode = self != self._origin
                    ks_name = "Pre-existing Conditions"
                    ks_name = ks_name 
                    #           ("Invoice No: " + str(self.ids)
                    #            if self._origin.id
                    #            else (self.display_name))
                    terms_lines1 = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    already_exists1 = self.line_ids.filtered(
                        lambda line: line.name and line.name.find('Pre-existing Conditions') == 0)
                    if already_exists1:
                        amount = self.preexisting
                        if self.ks_preexisting_account \
                                and (self.type == "out_invoice"
                                     or self.type == "out_refund"):
                            if self.type == "out_invoice":
                                already_exists1.update({
                                    'name': ks_name,
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            else:
                                already_exists1.update({
                                    'name': ks_name,
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                         
                    else:
                        new_tax_line = self.env['account.move.line']
                        create_method = in_draft_mode and \
                                        self.env['account.move.line'].new or \
                                        self.env['account.move.line'].create

                        if self.ks_preexisting_account \
                                and (self.type == "out_invoice"
                                     or self.type == "out_refund"):
                            amount = self.preexisting
                            dict = {
                                'move_name': self.name,
                                'name': ks_name,
                                'price_unit': self.preexisting,
                                'quantity': 1,
                                'debit': amount > 0.0 and amount or 0.0,
                                'credit': amount < 0.0 and -amount or 0.0,
                                'account_id': self.ks_preexisting_account,
                                'move_id': self._origin,
                                'date': self.date,
                                'exclude_from_invoice_tab': True,
                                'partner_id': terms_lines1.partner_id.id,
                                'company_id': terms_lines1.company_id.id,
                                'company_currency_id': terms_lines1.company_currency_id.id,
                            }
                            if self.type == "out_invoice":
                                dict.update({
                                    'debit': amount < 0.0 and -amount or 0.0,
                                    'credit': amount > 0.0 and amount or 0.0,
                                })
                            else:
                                dict.update({
                                    'debit': amount > 0.0 and amount or 0.0,
                                    'credit': amount < 0.0 and -amount or 0.0,
                                })
                            if in_draft_mode:
                                self.line_ids += create_method(dict)
                                # Updation of Invoice Line Id
                                duplicate_id = self.invoice_line_ids.filtered(
                                    lambda line: line.name and line.name.find('Pre-existing Conditions') == 0)
                                self.invoice_line_ids = self.invoice_line_ids - duplicate_id
                            else:
                                dict.update({
                                    'price_unit': 0.0,
                                    'debit': 0.0,
                                    'credit': 0.0,
                                })
                                self.line_ids = [(0, 0, dict)]

                    if in_draft_mode:
                        # Update the payement account amount
                        terms_lines1 = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines1 = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        total_balance = sum(other_lines1.mapped('balance'))
                        total_amount_currency = sum(other_lines1.mapped('amount_currency'))
                        '''for record in terms_lines1:
                            if rec.discount_type == "percent":
                                record.update({
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(record.price_total - ((
                                                                             record.price_total * rec.discount_rate) / 100)) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total - ((
                                                                            record.price_total * rec.discount_rate) / 100) if total_balance > 0.0 else 0.0
                                })
                            elif rec.discount_type == "amount":
                                discount = rec.discount_rate / len(terms_lines1)
                                record.update({
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(record.price_total + discount) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total + discount if total_balance > 0.0 else 0.0
                                }) '''
                    else:
                        terms_lines1 = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                        other_lines1 = self.line_ids.filtered(
                            lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                        already_exists1 = self.line_ids.filtered(
                            lambda line: line.name and line.name.find('Pre-existing Conditions') == 0)
                        total_balance = sum(other_lines1.mapped('balance')) + amount
                        total_amount_currency = sum(other_lines1.mapped('amount_currency'))
                        line_ids = []
                        dict1 = {
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                        }
                        line_ids.append((1, already_exists1.id, dict1))
                        dict2 = {
                            'debit': total_balance > 0.0 and total_balance or 0.0,
                            'credit': total_balance < 0.0 and -total_balance or 0.0,
                        }
                        # for records in already_exists:
                        #     records.update(dict1)
                        '''for record in terms_lines1:
                            if rec.discount_type == "percent":
                                dict2 = {
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(record.price_total - ((
                                                                             record.price_total * rec.discount_rate) / 100)) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total - ((
                                                                            record.price_total * rec.discount_rate) / 100) if total_balance > 0.0 else 0.0
                                }
                            elif rec.discount_type == "amount":
                                discount = rec.discount_rate / len(terms_lines1)
                                dict2 = {
                                    'amount_currency': -total_amount_currency,
                                    'debit': -(
                                            record.price_total + discount) if total_balance < 0.0 else 0.0,
                                    'credit': record.price_total + discount if total_balance > 0.0 else 0.0
                                }
                            line_ids.append((1, record.id, dict2))
                        # self.line_ids = [(1, already_exists.id, dict1), (1, terms_lines.id, dict2)]'''
                        self.line_ids = line_ids

            elif self.preexisting < 0:
                already_exists1 = self.line_ids.filtered(
                    lambda line: line.name and line.name.find('Pre-existing Conditions') == 0)
                if already_exists1:
                    self.line_ids -= already_exists1
                    terms_lines1 = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
                    other_lines1 = self.line_ids.filtered(
                        lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
                    total_balance = sum(other_lines1.mapped('balance'))
                    total_amount_currency = sum(other_lines1.mapped('amount_currency'))
                    terms_lines1.update({
                        'amount_currency': -total_amount_currency,
                        'debit': total_balance > 0.0 and total_balance or 0.0,
                        'credit': total_balance < 0.0 and -total_balance or 0.0,
                    })
