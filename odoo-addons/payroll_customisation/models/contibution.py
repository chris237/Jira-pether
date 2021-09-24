from odoo import fields, api, models, tools, _
from datetime import date
import time
import base64
from odoo.tools import email_split, float_is_zero, float_compare
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from calendar import monthrange
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    conn_id = fields.Many2one('hr.contribution', string='contribution', copy=False, help="Expense where the move line come from")


class ContributionAccount(models.Model):
    _name = 'hr.acc'
    _description = 'Account contribution'
    _rec_name ='type_s'

    account_id = fields.Many2one('account.account', string='Account', required=True)
    company_id = fields.Many2one(related='create_uid.company_id', store=True, readonly=True, default = 1)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    type_s = fields.Selection([
        ('tier_1', 'SSNIT Contribution'),
        ('tier_2', 'GLICO MASTER TRUST OCCUPATIONAL PENSION'),
        ('tier_3', 'GLICO MASTER TRUST PROVIDENT FUND '),
        ('si', 'STAFF INVESTMENT'),
        ('payee', 'PAYEE'),
        ('gw', 'GLICO STAFF WELFARE FUND'),
        ('slip', 'STAFF LIFE POLICY PREMIUM'),
        ('ld', 'LOAN DEDUCTION'),
        ], string="Type", required=True)

class ContributionPayment(models.Model):
    _name = 'hr.contribution'
    _description = 'Employee contribution'
    _inherit = ['portal.mixin', 'mail.thread']
    _order = "id desc, create_date desc"
    _rec_name ='title_r'

    @api.model
    def _default_journal_id(self):
        """ The journal is determining the company of the accounting entries generated from expense. We need to force journal company and expense sheet company to be the same. """
        default_company_id = self.default_get(['company_id'])['company_id']
        journal = self.env['account.journal'].search([('type', '=', 'purchase'), ('company_id', '=', default_company_id)], limit=1)
        return journal.id

    @api.depends('type_s')
    def _default_account_id(self):
        for conn in self:
            account1 = self.env['hr.acc'].search([('type_s', '=', conn.type_s)])
            if account1:
                for acc in account1:
                    account = acc.account_id.id
                    conn.account_id = account
    @api.depends('type_s')
    def _default_partner_id(self):
        for conn in self:
            account1 = self.env['hr.acc'].search([('type_s', '=', conn.type_s)])
            if account1:
                for acc in account1:
                    account = acc.partner_id.id
                    conn.partner_id = account

    @api.model
    def _default_bank_journal_id(self):
        default_company_id = self.default_get(['company_id'])['company_id']
        return self.env['account.journal'].search([('type', 'in', ['cash', 'bank']), ('company_id', '=', default_company_id)], limit=1)

    title_r = fields.Char(string = 'Title ')

    amount = fields.Monetary(string='Amount', compute='_total_summary', currency_field='company_currency_id')
    # date = fields.Date(string = 'Date ')
    date = fields.Date(default=fields.Date.context_today, string="Date")
    # sheet = fields.Many2one('clientpi.submitsheet', string='Summary sheet ', auto_join=True, ondelete="cascade")
    sheet1 = fields.Many2one('clientpi.submitsheet', string='Summary sheet', readonly=True,
        copy=False, stat={'draft': [('readonly', False)]}, ondelete='cascade',
        )
    pv = fields.Many2one('account.payment', string='Payment voucher')
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, required=True, compute='_default_partner_id')
    journal_id = fields.Many2one('account.journal', string='Contribution Journal', stat={'cancel': [('readonly', True)], 'posted': [('readonly', True)]}, check_company=True, domain="[('type', '=', 'purchase'), ('company_id', '=', company_id)]",
        default=_default_journal_id, help="The journal used when the expense is done.")
    account_id = fields.Many2one('account.account', string='Account', compute='_default_account_id', domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', stat={'cancel': [('readonly', True)], 'posted': [('readonly', True)]}, check_company=True, domain="[('type', 'in', ['cash', 'bank']), ('company_id', '=', company_id)]",
        default=_default_bank_journal_id, help="The payment method used when the expense is paid by the company.")
    accounting_date = fields.Date("Date")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='restrict', copy=False, readonly=True)
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True)
    type_s = fields.Selection([
        ('tier_1', 'SSNIT Contribution'),
        ('tier_2', 'GLICO MASTER TRUST OCCUPATIONAL PENSION'),
        ('tier_3', 'GLICO MASTER TRUST PROVIDENT FUND '),
        ('si', 'STAFF INVESTMENT'),
        ('payee', 'PAYE'),
        ('gw', 'GLICO STAFF WELFARE FUND'),
        ('slip', 'STAFF LIFE POLICY PREMIUM'),
        ('ld', 'LOAN DEDUCTION'),
        ], string="Type")
    stat = fields.Selection(
        [('draft', 'Draft'), 
         ('posted', 'Posted'),
         ('paid', 'Paid'),
         ('cancel', 'Canceled')
         ], readonly=True, default='draft', copy=False, string="Status", tracking=True)



    line_ids = fields.One2many('hr.contribution.line', 'comm_id', 
                               string='Commission Line',
                               copy=False, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)
    company_id = fields.Many2one(related='create_uid.company_id', store=True, readonly=True, default = 1)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')    

    def _get_expense_account_source(self):
        self.ensure_one()
        if self.account_id:
            account = self.account_id
        else:
            raise UserError(_('Please configure Default contibution account.'))
        return account
    
    def set_to_paid(self, payment):
        self.write({'stat': 'paid'})
        self.write({'pv' : payment.id})

    def _get_expense_account_destination(self):
        self.ensure_one()
        # account_dest = self.env['account.account']
        partner = self.partner_id
        if not partner.property_account_payable_id:
            raise UserError(_("No credit account found for the %s journal, please configure one.") % (self.partner.name))
        account_dest = partner.property_account_payable_id.id or partner.parent_id.property_account_payable_id.id
        # if not self.comm_id.journal_id.default_credit_account_id:
        #     raise UserError(_("No credit account found for the %s journal, please configure one.") % (self.comm_id.bank_journal_id.name))
        # account_dest = self.comm_id.journal_id.default_credit_account_id.id
        return account_dest

    def _get_account_move_line_values(self):
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.partner_id.name + ': ' + expense.title_r.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id
            different_currency = expense.company_currency_id and expense.company_currency_id != company_currency

            move_line_values = move_line = []
            # taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner_id = expense.partner_id.id 
            # partner_id = expense.employee.address_home_id.commercial_partner_id.id 

            # source move line
            amount = expense.amount
            amount_currency = False
            if different_currency:
                amount = expense.company_currency_id._convert(amount, company_currency, expense.company_id, account_date)
                amount_currency = expense.amount
            move_line_src = {
                'name': move_line_name,
                'quantity': 1,
                'debit': amount if amount > 0 else 0,
                'credit': -amount if amount < 0 else 0,
                'amount_currency': amount_currency if different_currency else 0.0,
                'account_id': account_src.id,
                'price_unit': amount,
                # 'product_id': expense.product_id.id,
                # 'product_uom_id': expense.product_uom_id.id,
                # 'analytic_account_id': expense.analytic_account_id.id,
                # 'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'conn_id': expense.id,
                'partner_id': partner_id,
                'currency_id': expense.company_currency_id.id if different_currency else False,
            }
            # self.env['account.move.line'].sudo().create(move_line_src)
            move_line_values.append(move_line_src)
            total_amount += -move_line_src['debit'] or move_line_src['credit']
            total_amount_currency += -move_line_src['amount_currency'] if move_line_src['currency_id'] else (-move_line_src['debit'] or move_line_src['credit'])

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency if different_currency else 0.0,
                'currency_id': expense.company_currency_id.id if different_currency else False,
                'conn_id': expense.id,
                'partner_id': partner_id,
            }
            # self.env['account.move.line'].sudo().create(move_line_src,move_line_dst)
            move_line_values.append(move_line_dst)
            # move_line.append(move_line_src)
            # move_line.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense
    
    def _prepare_move_values(self):
        """
        This function prepares move values related to an expense
        """
        self.ensure_one()
        journal =  self.journal_id
        account_date = self.accounting_date or self.date
        # move_line = self._get_account_move_line_values()
        # _logger.info("mail=== '" + str(move_line) + "' ok !")
        move_values = {
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            'date': account_date,
            'ref': self.title_r,
            # force the name to the default value, to avoid an eventual 'default_name' in the context
            # to set it to '' which cause no number to be given to the account.move when posted.
            'name': '/',
        }
        return move_values

    basic = fields.Monetary(string='Basic', compute='_total_summary', currency_field='company_currency_id')
    # Staff Welfare
    per = fields.Monetary(string='1%', compute='_total_summary', currency_field='company_currency_id')
    pfl = fields.Monetary(string='PROVIDENT FUND LOAN', compute='_total_summary', currency_field='company_currency_id')
    wel = fields.Monetary(string='WELFARE', compute='_total_summary', currency_field='company_currency_id')
    loan = fields.Monetary(string='LOAN', compute='_total_summary', currency_field='company_currency_id')
    #payee
    ssf_55 = fields.Monetary(string='SSF 5.5%', compute='_total_summary', currency_field='company_currency_id')
    pf_6 = fields.Monetary(string='Provident Fund 6%', compute='_total_summary', currency_field='company_currency_id')
    bsc = fields.Monetary(string='Basic After SSF & PF DED', compute='_total_summary',  currency_field='company_currency_id')
    ta = fields.Monetary(string='Taxable Allowance', compute='_total_summary',  currency_field='company_currency_id')
    ti = fields.Monetary(string='Taxable Income',compute='_total_summary',  currency_field='company_currency_id')
    pf_staff = fields.Monetary(string='PROVIDENT FUND STAFF', compute='_total_summary', currency_field='company_currency_id')
    pf_empl = fields.Monetary(string='PROVIDENT FUND EMPLOYEE',compute='_total_summary', currency_field='company_currency_id')
    add_tier3 = fields.Monetary(string='ADDITIONAL TIER 3',compute='_total_summary', currency_field='company_currency_id')

    @api.depends('line_ids.total')
    def total_summary(self):
        res = {}
        for contrib in self:
            total1 = 0.0
            lines = self.env['hr.contribution.line'].sudo().search([('comm_id', '=', contrib.id)]) 
            for line in lines:
                lin = line.total
                total1 += lin
            if total1 != 0:
                contrib.amount = total1

    @api.depends('line_ids.pf_empl','line_ids.pf_staff','line_ids.ti','line_ids.ta','line_ids.bsc','line_ids.pf_6','line_ids.ssf_55','line_ids.loan','line_ids.wel','line_ids.pfl','line_ids.basic','line_ids.total',)
    def _total_summary(self):
        res = {}
        for move in self:
            basic = per = pfl = add_tier3 = wel = loan = ssf_55 = pf_6 = ta = bsc = ti = pf_staff = pf_empl = total = 0.0
            for line in move.line_ids:
                basic += line.basic
                add_tier3 += line.add_tier3
                total += line.total
                per += line.per
                pfl += line.pfl
                wel += line.wel
                loan += line.loan
                ssf_55 += line.ssf_55
                pf_6 += line.pf_6
                ta += line.ta
                bsc += line.bsc
                ti += line.ti
                pf_staff += line.pf_staff
                pf_empl += line.pf_empl
                basic = round(basic, 2)
                pfl = round(pfl, 2)
                add_tier3 = round(add_tier3, 2)
                per = round(per, 2)
                wel = round(wel, 2)
                loan = round(loan, 2)
                ssf_55 = round(ssf_55, 2)
                pf_6 = round(pf_6, 2)
                ta = round(ta, 2)
                bsc = round(bsc, 2)
                ti = round(ti, 2)
                pf_staff = round(pf_staff, 2)
                pf_empl = round(pf_empl, 2)
                total = round(total, 2)
            res.update({
                'amount' : total,
                })
            move.basic = basic
            move.add_tier3 = add_tier3
            move.per = per
            move.pfl = pfl
            move.wel = wel
            move.loan = loan
            move.ssf_55 = ssf_55
            move.pf_6 = pf_6
            move.ta = ta
            move.bsc = bsc
            move.ti = ti
            move.pf_staff = pf_staff
            move.pf_empl = pf_empl
            move.amount = total
        return res 


    def _get_account_move_by_sheet(self):
        """ Return a mapping between the expense sheet of current expense and its account move
            :returns dict where key is a sheet id, and value is an account move record
        """
        move_grouped_by_sheet = {}
        for conn in self:
            # create the move that will contain the accounting entries
            if conn.id not in move_grouped_by_sheet:
                move_vals = conn._prepare_move_values()
                move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
                move_grouped_by_sheet[conn.id] = move
            else:
                move = move_grouped_by_sheet[conn.id]
        return move_grouped_by_sheet


    def action_move_create(self):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_group_by_sheet = self._get_account_move_by_sheet()

        move_line_values_by_expense = self._get_account_move_line_values()

        move_to_keep_draft = self.env['account.move']

        company_payments = self.env['account.payment']

        for conn in self:
            company_currency = conn.company_id.currency_id
            different_currency = conn.currency_id != company_currency

            # get the account move of the related sheet
            move = move_group_by_sheet[conn.id]

            # get move line values
            move_line_values = move_line_values_by_expense.get(conn.id)
            move_line_dst = move_line_values[-1]
            total_amount = move_line_dst['debit'] or -move_line_dst['credit']
            total_amount_currency = move_line_dst['amount_currency']

            
            # link move lines to move, and move to expense sheet
            move.write({'line_ids': [(0, 0, line) for line in move_line_values]})
            conn.write({'account_move_id': move.id})

        company_payments.filtered(lambda x: x.journal_id.post_at == 'pay_val').write({'state':'reconciled'})
        company_payments.filtered(lambda x: x.journal_id.post_at == 'bank_rec').write({'state':'posted'})

        # post the moves
        for move in move_group_by_sheet.values():
            if move in move_to_keep_draft:
                continue
            move.post()

        return move_group_by_sheet


    def post(self):
        for contribution in self:
            date = fields.Date.from_string(fields.Date.today())
            if self.type_s == 'tier_1':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('tier1.contribution')
                contribution.write(
                    {
                        'number': 'SS. ER NO' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'tier_2':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('tier2.contribution')
                contribution.write(
                    {
                        'number': 'TIER2' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'tier_3':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('tier3.contribution')
                contribution.write(
                    {
                        'number': 'TIER3' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'si':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('si.contribution')
                contribution.write(
                    {
                        'number': 'STAFF_INV' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'payee':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('payee.contribution')
                contribution.write(
                    {
                        'number': 'PAYEE' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'gw':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('gw.contribution')
                contribution.write(
                    {
                        'number': 'WELFARE' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'slip':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('slip.contribution')
                contribution.write(
                    {
                        'number': 'SLIP' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            elif self.type_s == 'ld':
                advice_year = date.strftime('%m') + '-' + date.strftime('%Y')
                number = self.env['ir.sequence'].next_by_code('ld.contribution')
                contribution.write(
                    {
                        'number': 'LOAD_DEDUCTION' + '-' + advice_year + '-' + number,
                        'stat': 'posted',
                    })
            
            # test new methode

            res = self.action_move_create()
            # move = self.move_create()
            # contribution.account_move_id = move.id  
            # End new methode

            if not contribution.accounting_date:
                contribution.accounting_date = contribution.account_move_id.date


class ContributionPaymentLine(models.Model):
    '''
    Contributions Lines
    '''
    _name = 'hr.contribution.line'
    _description = 'Employee contribution Lines'

    @api.depends('comm_id')
    def _default_account_id(self):
        for con in self:
            con.account_id = con.comm_id.account_id.id

    @api.depends('employee')
    def _ssnit(self):
        for line in self:
            if line.employee:
                line.ssnit = line.employee.ssnit
                line.staff = line.employee.staff_number

    comm_id = fields.Many2one('hr.contribution', string='Contribution sheet', auto_join=True, ondelete="cascade")
    type_s = fields.Selection(related='comm_id.type_s', store=True, readonly=True)
    employee = fields.Many2one('hr.employee', string='Employee', required=True)
    staff = fields.Char(related='employee.staff_number', store=True, readonly=True)
    tin = fields.Char(related='employee.tit_number', store=True, readonly=True)
    date = fields.Date(readonly=True, states={'draft': [('readonly', False)], 'reported': [('readonly', False)], 'refused': [('readonly', False)]}, default=fields.Date.context_today, string="Date")
    ssnit = fields.Char(related='employee.ssnit', store=True, readonly=True)
    basic = fields.Monetary(string='Basic', store =True, currency_field='company_currency_id')
    total = fields.Monetary(string='Amount', store =True, currency_field='company_currency_id')
  
    # Staff Welfare
    per = fields.Monetary(string='1%', store =True, currency_field='company_currency_id')
    pfl = fields.Monetary(string='PROVIDENT FUND LOAN', store =True, currency_field='company_currency_id')
    wel = fields.Monetary(string='WELFARE', store =True, currency_field='company_currency_id')
    loan = fields.Monetary(string='LOAN', store =True, currency_field='company_currency_id')

    #payee
    ssf_55 = fields.Monetary(string='SSF 5.5%', store =True, currency_field='company_currency_id')
    pf_6 = fields.Monetary(string='Provident Fund 6%', store =True, currency_field='company_currency_id')
    bsc = fields.Monetary(string='Basic After SSF & PF DED', store =True, currency_field='company_currency_id')
    ta = fields.Monetary(string='Taxable Allowance', store =True, currency_field='company_currency_id')
    ti = fields.Monetary(string='Taxable Income', store =True, currency_field='company_currency_id')
    
    pf_staff = fields.Monetary(string='PROVIDENT FUND STAFF', store =True, currency_field='company_currency_id')
    pf_empl = fields.Monetary(string='PROVIDENT FUND EMPLOYEE', store =True, currency_field='company_currency_id')
    # account_id = fields.Many2one('account.account', string='Account', domain="[('internal_type', '=', 'other'), ('company_id', '=', company_id)]")
    account_id = fields.Many2one('account.account', string='Account', compute='_default_account_id', domain="[('company_id', '=', company_id)]")
    add_tier3 = fields.Monetary(string='ADDITIONAL TIER 3', store =True, currency_field='company_currency_id')
    company_id = fields.Many2one(related='employee.company_id', store=True, readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')

class payroll_contribution_report(models.AbstractModel):
    _name = 'report.payroll_customisation.contri_payroll'
    _description = "Report Contributions"
    
    def get_detail(self, line_ids):
        result = []
        for l in line_ids:
            res = {}
            res.update({
                    'staff': l.staff,
                    'ssnit': l.ssnit,
                    'tin': l.tin,
                    'per': l.per,
                    'wel': l.wel,
                    'pfl': l.pfl,
                    'loan': l.loan,
                    'ssf_55': l.ssf_55,
                    'pf_6': l.pf_6,
                    'bsc': l.bsc,
                    'ta': l.ta,
                    'ti': l.ti,
                    'employee': l.employee.name,
                    'basic': l.basic,
                    'pf_staff': l.pf_staff,
                    'pf_empl': l.pf_empl,
                    'add_tier3': l.add_tier3,
                    'total': l.total,
                    })
            result.append(res)
        result = sorted(result, key=itemgetter('employee'))
        return result
    
    @api.model
    def _get_report_values(self, docids, data=None):
        summary = self.env['hr.contribution'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.contributiont',
            'data': data,
            'docs': summary,
            'get_detail': self.get_detail,
        }
