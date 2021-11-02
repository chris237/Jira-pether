# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import requests
import datetime
import time
from datetime import date
from operator import itemgetter
import logging
_logger = logging.getLogger(__name__)


class HrEmployeeA(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'
    
    Bank_name = fields.Char(string ='Bank Name')
    account_number = fields.Char(string ='Account Number')
    Bank_branch = fields.Char(string ='Branch')
    tit_number = fields.Char(string ='TIN Number')
    staff_number = fields.Char(string ='Staff Number')
    ssnit = fields.Char(string ='SSNIT number')

class HrPayslipbcd(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Payslip Pay'
    
    journal_posted = fields.Boolean(string ="journal posted?", default=False)
    available_advice = fields.Boolean(string ="Made Payment Advice?", default=False)
    id_activity = fields.Many2one('mail.activity', string='activity')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('summary_sheet', 'Summary Sheet'),
        ('verify', 'Verify'),
        ('voucher', 'Voucher'),
        ('advice', 'Advice'),
        ('done', 'Done'),
        ('done1', 'Done'),
        ('cancel', 'Rejected'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")  

    # def compute_sheet(self):
    #     res = super(HrPayslipbcd, self).compute_sheet()
    #     for payslip in self:
    #         payslip.sum_sheet = True

    #     return res    

   
    def action_payslip_done(self):
        res = super(HrPayslipbcd, self).action_payslip_done()
        self.write({'state' : 'verify'})

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'account.move')]).id
        users = self.env['account.send.notif'].search([], limit=1)
        pay_runs = self.env['hr.payslip.run'].search([])
        for payslip in self:
            compte = 0
            for pay_run in pay_runs:
                pays = self.env['hr.payslip'].search([('id', '=', payslip.id),('payslip_run_id', '=', pay_run.id)], limit=1)
                if pays:
                    for pay in pays:
                        id_move = pay.move_id
                        run_pay = pay.payslip_run_id
                    compte += 1
                    _logger.info("compte=== '" + str(compte) + "' ok !")
        if compte == 1:
            for user in users:
                if user.auditor.id:
                        line = self.env['mail.activity'].create({
                                        'res_model_id': model_id, 
                                        'res_id': id_move,
                                        'activity_type_id': mail_id, 
                                        'date_deadline': date, 
                                        'user_id': user.auditor.id,
                                        'note': 'Draft entry are pending for them to be validate.'
                                        })
                        self.id_activity = line.id   
        elif compte == 0:
            for payslip in self:
                for user in users:
                    if user.auditor.id:
                        line = self.env['mail.activity'].create({
                                        'res_model_id': model_id, 
                                        'res_id': payslip.move_id,
                                        'activity_type_id': mail_id, 
                                        'date_deadline': date, 
                                        'user_id': user.auditor.id,
                                        'note': 'Draft entry are pending for them to be validate.'
                                        })
                        self.id_activity = line.id    

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': (' Draft entry Payroll ! '),
                'message': ' Draft entry created ',
                'type':'success',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
            },
        }
        return notification                        
        
        return res


    def create_payment_voucher(self):
        if self.journal_posted == True:
            self.write({'state' : 'advice'}) 

            amount = 0.00
            partner = "Prudential Bank"
            journal = "PBL-1"
            narrat = self.name
            date = datetime.datetime.now().date()

            for run in self:
                payslip_line_id = self.env['hr.payslip.line'].search([('slip_id', '=', self.id)]).slip_id
                for slip in payslip_line_id:
                    payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
                    if payslip_line:
                        amount = amount + payslip_line.total

            
            payment = self.env['hr.pv'].create({
                'payement_mode': "manual",
                'payee': partner,
                'bank': journal,
                'narration': narrat,
                'payment_date': date.today(),
                'state': 'draft',
                'amount': amount,
                'id_payslip': self.id,
            })
            
            mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
            model_id = self.env['ir.model'].search([('model', '=', 'hr.pv')]).id
            users = self.env['account.send.notif'].search([], limit=1)  
            for user in users:
                if user.finance_officer.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': payment.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.finance_officer.id,
                                    'note': 'voucher has been created and needs to be submit..',
                                    })        
                    ok=self.id_activity.action_done() 
                    pvs = self.env['hr.pv'].search([('id', '=', payment.id)]) 
                    for pv in pvs:
                        pv.id_activity = line.id


            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': (' Payment voucher Payroll ! '),
                    'message': ' Payment voucher created ',
                    'type':'success',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                },
            }
            return notification
        else:    
            raise ValidationError("You can't create a payment voucher without posting the journal entries")

               
    
    def create_advice(self):
        for pay in self:
            if pay.available_advice:
                raise UserError(_("Payment advice already exists for %s, 'Set to Draft' to create a new advice.") % (run.name,))
            company = self.env.company
            advice = self.env['hr.payroll.advice'].create({
                        'payslip_id': pay.id,
                        'company_id': company.id,
                        'name': pay.name,
                        'date': pay.date_to,
                        'bank_id': company.partner_id.bank_ids and company.partner_id.bank_ids[0].bank_id.id or False
                    })
            payslip_line_id = self.env['hr.payslip.line'].search([('slip_id', '=', self.id)]).slip_id
            for slip in payslip_line_id:
                # TODO is it necessary to interleave the calls ?
                # run.action_payslip_done()
                if not slip.employee_id.bank_account_id or not slip.employee_id.bank_account_id.acc_number:
                    raise UserError(_('Please define bank account for the %s employee') % (slip.employee_id.name))
                payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
                if payslip_line:
                    self.env['hr.payroll.advice.line'].create({
                        'advice_id': advice.id,
                        'name': slip.employee_id.bank_account_id.acc_number,
                        'bank_name': slip.employee_id.Bank_name,
                        'ifsc_code': slip.employee_id.Bank_branch or '',
                        'employee_id': slip.employee_id.id,
                        'bysal': payslip_line.total
                    })
            date = datetime.datetime.now().date()
            mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
            model_id = self.env['ir.model'].search([('model', '=', 'hr.payslip')]).id
            users = self.env['account.send.notif'].search([], limit=1)
            for user in users:
                if user.finance_officer.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': pay.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.finance_officer.id,
                                    'note': 'voucher are approved for needs to be send by email.'
                                    })
                    ok=self.id_activity.action_done()                 
                    pays = self.env['hr.payslip'].search([('id', '=', pay.id)]) 
                    for paysl in pays:
                        paysl.id_activity = line.id         
        self.write({'available_advice': True})
        self.write({'state' : 'done'})


class HrPayslipRunbcd(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']
    _description = 'Payslip Batches'

    journal_posted = fields.Boolean(string ="journal posted?", default=False)
    id_activity = fields.Many2one('mail.activity', string='activity')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('summary_sheet', 'Summary Sheet'),
        ('verify', 'Verify'),
        ('voucher', 'Voucher'),
        ('advice', 'Advice'),
        ('close', 'Done'),
        ('close1', 'Done'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft')


    def action_close(self):
        if self._are_payslips_ready():
            self.write({'state' : 'voucher'})

    # def create_notification(self):
    #     notification = {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': (' info ! '),
    #             'message': ' Ta grosse tete DG ',
    #             'sticky': False,
    #             'type': 'success'
    #         },
    #     }
    #     return notification
    def create_payment_voucher(self):
        if self.journal_posted == True:
            self.write({'state' : 'advice'}) 

            amount = 0.00
            partner = "Prudential Bank"
            journal = "PBL-1"
            narrat = self.name

            date = datetime.datetime.now().date()


            for run in self:
                for slip in run.slip_ids:
                    payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
                    if payslip_line:
                        amount = amount + payslip_line.total

            payment = self.env['hr.pv'].create({
                    'payement_mode': "manual",
                    'payee': partner,
                    'bank': journal,
                    'narration': narrat,
                    'payment_date': date.today(),
                    'state': 'draft',
                    'amount': amount,
                    'id_payslip_run': self.id,
                })


            mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
            model_id = self.env['ir.model'].search([('model', '=', 'hr.pv')]).id
            users = self.env['account.send.notif'].search([], limit=1)    
            for user in users:
                if user.finance_officer.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': payment.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.finance_officer.id,
                                    'note': 'voucher has been created and needs to be submit..'
                                    })        
                    ok=self.id_activity.action_done() 
                    pvs = self.env['hr.pv'].search([('id', '=', payment.id)]) 
                    for pv in pvs:
                        pv.id_activity = line.id 


            notification = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': (' Payment voucher Payroll ! '),
                    'message': ' Payment voucher created ',
                    'type':'success',  #types: success,warning,danger,info
                    'sticky': False,  #True/False will display for few seconds if false
                },
            }
            return notification
        else:    
            raise ValidationError("You can't create a payment voucher without posting the journal entries")       
    
    def create_advice(self):
        for run in self:
            if run.available_advice:
                raise UserError(_("Payment advice already exists for %s, 'Set to Draft' to create a new advice.") % (run.name,))
            company = self.env.company
            advice = self.env['hr.payroll.advice'].create({
                        'batch_id': run.id,
                        'company_id': company.id,
                        'name': run.name,
                        'date': run.date_end,
                        'bank_id': company.partner_id.bank_ids and company.partner_id.bank_ids[0].bank_id.id or False
                    })
            for slip in run.slip_ids:
                # TODO is it necessary to interleave the calls ?
                # slip.action_payslip_done()
                if not slip.employee_id.bank_account_id or not slip.employee_id.bank_account_id.acc_number:
                    raise UserError(_('Please define bank account for the %s employee') % (slip.employee_id.name))
                payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
                if payslip_line:
                    self.env['hr.payroll.advice.line'].create({
                        'advice_id': advice.id,
                        'name': slip.employee_id.bank_account_id.acc_number,
                        'bank_name': slip.employee_id.Bank_name,
                        'ifsc_code': slip.employee_id.Bank_branch or '',
                        'employee_id': slip.employee_id.id,
                        'bysal': payslip_line.total
                    })

            date = datetime.datetime.now().date()
            mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
            model_id = self.env['ir.model'].search([('model', '=', 'hr.payslip.run')]).id
            users = self.env['account.send.notif'].search([], limit=1)
            for user in users:
                if user.finance_officer.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': run.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.finance_officer.id,
                                    'note': 'voucher are approved for needs to be send by email.'
                                    })
                    ok=self.id_activity.action_done()                 
                    runs = self.env['hr.payslip.run'].search([('id', '=', run.id)]) 
                    for run in runs:
                        run.id_activity = line.id         
        self.write({'available_advice': True})
        self.write({'state' : 'close'})

class payroll_advice_report(models.AbstractModel):
    _inherit = 'report.l10n_in_hr_payroll.report_payrolladvice'
    _description = "Indian Payroll Advice Report"
    
    def get_detail(self, line_ids):
        result = []
        self.total_bysal = 0.00
        for l in line_ids:
            res = {}
            res.update({
                    'name': l.employee_id.name,
                    'acc_no': l.name,
                    'bank_name': l.bank_name,
                    'ifsc_code': l.ifsc_code,
                    'bysal': l.bysal,
                    'debit_credit': l.debit_credit,
                    })
            self.total_bysal += l.bysal
            result.append(res)
        result = sorted(result, key=itemgetter('name'))
        return result

class HrPayrollAdviceLinebcd(models.Model):
    '''
    Bank Advice Lines
    '''
    _inherit = 'hr.payroll.advice.line'
    _description = 'Bank Advice Lines'
    
    bank_name = fields.Char(string = 'Bank Name ', required=True)
    ifsc_code = fields.Char(string='Bank Branch')

class HrPayrollAdvicebcd(models.Model):
    '''
    Bank Advice
    '''
    _inherit = 'hr.payroll.advice'
    _description = 'Bank Advice'
    
    payslip_id = fields.Many2one('hr.payslip', string='payslip', readonly=True)

    
class HrcontractA(models.Model):
    _inherit = 'hr.contract'
    
    struct_id = fields.Many2one('hr.payroll.structure', string='Structure')
    wage_type = fields.Selection([('monthly', 'Monthly Fixed Wage'), ('hourly', 'Hourly Wage')], related='structure_type_id.wage_type', string='Salary type')
    wage = fields.Monetary('Basic Salary', required=True, tracking=True, help="Employee's monthly gross wage.")
    
class HrPayslipEmployeesA(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    
    defaut_structu = fields.Boolean(string=' Do you want to use a generic salary structure?',
        help="If its checked, indicates that all payslips generated Whit same salary structure.")
    
    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        if not self.employee_ids:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']

        contracts = self.employee_ids._get_contracts(payslip_run.date_start, payslip_run.date_end, states=['open', 'close'])
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', self.employee_ids.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        # validated = work_entries.action_validate()
        # if not validated:
        #     raise UserError(_("Some work entries could not be validated."))

        default_values = Payslip.default_get(Payslip.fields_get())
        for contract in contracts:
            values = dict(default_values, **{
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.struct_id.id,
            })
            payslip = self.env['hr.payslip'].new(values)
            payslip._onchange_employee()
            values = payslip._convert_to_write(payslip._cache)
            payslips += Payslip.create(values)
        payslips.compute_sheet()
        payslips.sum_sheet = True
        payslip_run.state = 'summary_sheet'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
        
class HrSalaryRuleabcv(models.Model):
    _inherit = 'hr.salary.rule'
    
