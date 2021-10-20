# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from werkzeug import url_encode


class HrRegisterPaymentWizard(models.TransientModel):
    _name = "hr.register.payment.wizard"
    _description = "Register Payment Wizard"

    @api.model
    def default_get(self, fields):
        result = super(HrRegisterPaymentWizard, self).default_get(fields)

        active_model = self._context.get('active_model')
        if active_model != 'hr.contribution':
            raise UserError(_('You can only apply this action from an contribution report.'))

        active_id = self._context.get('active_id')
        if 'contribution_id' in fields and active_id:
            result['contribution_id'] = active_id

        if 'partner_id' in fields and active_id and not result.get('partner_id'):
            contib = self.env['hr.contribution'].browse(active_id)
            result['partner_id'] = contib.sudo().partner_id.id
            result['amount'] = contib.sudo().amount
        return result

    contribution_id = fields.Many2one('hr.contribution', string="Contributions Report", required=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    partner_bank_account_id = fields.Many2one('res.partner.bank', string="Recipient Bank Account", domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    journal_id = fields.Many2one('account.journal', string='Payment Institutions', required=True, domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]")
    company_id = fields.Many2one('res.company', related='contribution_id.company_id', string='Company', readonly=True)
    wt_exp_total = fields.Monetary(string='Witholding Tax contribution', compute='_compute_tax_expense', readonly=True, default=0.0)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    amount = fields.Monetary(string='Payment Amount', compute='_compute_tax_expense', required=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.company.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True)
    communication = fields.Char(string='Memo')
    check_amount_in_words = fields.Char(string="Amount in Words")
    check_manual_sequencing = fields.Boolean(related='journal_id.check_manual_sequencing', readonly=False)
    # Note: a check_number == 0 means that it will be attributed when the check is printed
    check_number = fields.Char(string="Check Number", readonly=True, copy=False, default=0,
        help="Number of the check corresponding to this payment. If your pre-printed check are not already numbered, "
             "you can manage the numbering in the journal configuration page.")
    payment_method_code_2 = fields.Char(related='payment_method_id.code',
                                      help="Technical field used to adapt the interface to the payment type selected.",
                                      string="Payment Method Code 2",
                                      readonly=True)

    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
        help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    show_partner_bank_account = fields.Boolean(compute='_compute_show_partner_bank', help='Technical field used to know whether the field `partner_bank_account_id` needs to be displayed or not in the payments form views')
    require_partner_bank_account = fields.Boolean(compute='_compute_show_partner_bank', help='Technical field used to know whether the field `partner_bank_account_id` needs to be required or not in the payments form views')


    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if hasattr(super(HrRegisterPaymentWizard, self), '_onchange_journal_id'):
            super(HrRegisterPaymentWizard, self)._onchange_journal_id()
        if self.journal_id.check_manual_sequencing:
            self.check_number = self.journal_id.check_sequence_id.number_next_actual

    @api.onchange('amount')
    def _onchange_amount(self):
        if hasattr(super(HrRegisterPaymentWizard, self), '_onchange_amount'):
            super(HrRegisterPaymentWizard, self)._onchange_amount()
        self.check_amount_in_words = self.currency_id.amount_to_text(self.amount)

    def _compute_tax_expense(self):
        contribu = self.contribution_id
        self.amount = contribu.amount
        self.wt_exp_total = 0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        expense_sheet = self.contribution_id
        if self.partner_id and len(self.partner_id.bank_ids) > 0:
            self.partner_bank_account_id = self.partner_id.bank_ids[0]
        else:
            self.partner_bank_account_id = False

    @api.constrains('amount')
    def _check_amount(self):
        for wizard in self:
            if not wizard.amount > 0.0:
                raise ValidationError(_('The payment amount must be strictly positive.'))

    @api.depends('payment_method_id')
    def _compute_show_partner_bank(self):
        """ Computes if the destination bank account must be displayed in the payment form view. By default, it
        won't be displayed but some modules might change that, depending on the payment type."""
        for payment in self:
            payment.show_partner_bank_account = payment.payment_method_id.code in self.env['account.payment']._get_method_codes_using_bank_account()
            payment.require_partner_bank_account = payment.payment_method_id.code in self.env['account.payment']._get_method_codes_needing_bank_account()

    @api.depends('journal_id')
    def _compute_hide_payment_method(self):
        for wizard in self:
            if not wizard.journal_id:
                wizard.hide_payment_method = True
            else:
                journal_payment_methods = wizard.journal_id.outbound_payment_method_ids
                wizard.hide_payment_method = (len(journal_payment_methods) == 1
                    and journal_payment_methods[0].code == 'manual')

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            return {'domain': {'payment_method_id': [('payment_type', '=', 'outbound'), ('id', 'in', payment_methods.ids)]}}
        return {}

    @api.onchange('partner_id')
    def _onchange_partner_id1(self):
        self.communication = self.contribution_id.title_r + ' ' + str(self.contribution_id.date)

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
            'contribution_id':self.contribution_id and self.contribution_id.id or False,
            # 'wt_exp_total': self.wt_exp_total,
            'withtax': self.wt_exp_total,
            'check_amount_in_words': self.check_amount_in_words,
            'check_manual_sequencing': self.check_manual_sequencing,
            'account_move_id': self.contribution_id.account_move_id.id
        }

    def expense_post_payment(self):
        self.ensure_one()
        company = self.company_id
        self = self.with_context(force_company=company.id, company_id=company.id)
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        expense_sheet = self.env['hr.contribution'].browse(active_ids)

        # Create payment and post it
        payment = self.env['account.payment'].create(self._get_payment_vals())
        payment.post()
        expense_sheet.set_to_paid(payment)

        # Log the payment in the chatter
        body = (_("A payment of %s %s with the reference <a href='/mail/view?%s'>%s</a> related to your expense %s has been made.") % (payment.amount, payment.currency_id.symbol, url_encode({'model': 'account.payment', 'res_id': payment.id}), payment.name, expense_sheet.title_r))
        expense_sheet.message_post(body=body)

        # Reconcile the payment and the expense, i.e. lookup on the payable account move lines
        '''account_move_lines_to_reconcile = self.env['account.move.line']
        for line in payment.move_line_ids + expense_sheet.account_move_id.line_ids:
            if line.account_id.internal_type == 'payable' and not line.reconciled:
                account_move_lines_to_reconcile |= line
        account_move_lines_to_reconcile.reconcile()'''

        return {'type': 'ir.actions.act_window_close'}

