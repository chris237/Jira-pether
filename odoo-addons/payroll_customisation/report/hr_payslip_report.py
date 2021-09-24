from odoo import fields, api, models, tools, _
from datetime import date
import time
import base64
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from calendar import monthrange
from operator import itemgetter
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)

class SubmitSheet(models.Model):
    _name = 'clientpi.submitsheet'
    _description = 'Submit Sheet Report'
    _inherit = ['portal.mixin', 'mail.thread']
    _order = "id desc, create_date desc"
    _rec_name ='name_sub'
    
    name_sub = fields.Many2one('hr.payslip.run', string = 'Name' , tracking=True, ondelete="cascade")
    name_sub1 = fields.Many2one('hr.payslip', string = 'Name' , tracking=True)
    start_date = fields.Date(string ='Date From', tracking=True)
    # slip_ids = fields.One2many('hr.contribution', 'sheet', string='contributions', readonly=True,
    #     states={'draft': [('readonly', False)]})
    end_date = fields.Date(string='Date To', tracking=True)
    payslip_count = fields.Integer(compute='_compute_payslip_count')
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('closed', 'Closed')
    ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    line_ids = fields.One2many('clientpi.submitsheet.line', 'submitsheet_id', 
                               string='Unbmitshett Line',
                               copy=False, readonly=True)
    
    def total_summary(self):
        res = {}
        for move in self:
            cr_basic = 0.0
            cr_ssf = 0.0
            cr_pf = 0.0
            cr_allow = 0.0
            cr_to_cas_emo = 0.0
            cr_tax_in = 0.0
            cr_paye = 0.0
            cr_other_deduc = 0.0
            cr_to_deduc = 0.0
            cr_net_sal = 0.0
            ssf_13 = 0.0
            cr_tier_1 = 0.0
            cr_tier_2 = 0.0
            cr_tier_3 = 0.0
            for line in move.line_ids:
                cr_basic += line.basic12
                cr_ssf += line.ssf
                cr_pf += line.pf
                cr_allow += line.allow
                cr_to_cas_emo += line.to_cas_emo
                cr_tax_in += line.tax_in
                cr_paye += line.paye
                cr_other_deduc += line.other_deduc
                cr_to_deduc += line.to_deduc
                cr_net_sal += line.net_sal
                ssf_13 += line.ssf_13
                cr_tier_1 += line.tier_1
                cr_tier_2 += line.tier_2
                cr_tier_3 += line.tier_3
                cr_basic = round(cr_basic, 2)
                cr_ssf = round(cr_ssf, 2)
                cr_pf = round(cr_pf, 2)
                cr_allow = round(cr_allow, 2)
                cr_to_cas_emo = round(cr_to_cas_emo, 2)
                cr_tax_in = round(cr_tax_in, 2)
                cr_paye = round(cr_paye, 2)
                cr_other_deduc = round(cr_other_deduc, 2)
                cr_to_deduc = round(cr_to_deduc, 2)
                cr_net_sal = round(cr_net_sal, 2)
                ssf_13 = round(ssf_13, 2)
                cr_tier_1 = round(cr_tier_1, 2)
                cr_tier_2 = round(cr_tier_2, 2)
                cr_tier_3 = round(cr_tier_3, 2)
            res.update({
                'cr_basic' : cr_basic,
                'cr_ssf' : cr_ssf,
                'cr_pf' : cr_pf,
                'cr_allow' : cr_allow,
                'cr_to_cas_emo' : cr_to_cas_emo,
                'cr_tax_in' : cr_tax_in,
                'cr_paye' : cr_paye,
                'cr_other_deduc' : cr_other_deduc,
                'cr_to_deduc' : cr_to_deduc,
                'cr_net_sal' : cr_net_sal,
                'ssf_13' : ssf_13,
                'cr_tier_1' : cr_tier_1,
                'cr_tier_2' : cr_tier_2,
                'cr_tier_3' : cr_tier_3
                })
        return res    

    def _compute_payslip_count(self):
        for payslip_run in self:
            contr = self.env['hr.contribution'].search([('sheet1', '=', self.id)])
            payslip_run.payslip_count = len(contr)
            
    def action_open_contributions(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.contribution",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['sheet1', '=', self.id]],
            "name": "Contributions",
        }
            

    def action_post(self):   
        lines = self.env['clientpi.submitsheet.line'].search([('submitsheet_id', '=', self.id)])
        tier1 = self.env['hr.contribution'].create({
                            'title_r': 'GLICO HEALTHCARE, SSNIT CONTRIBUTION TIER 1',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'tier_1' ,
                            'stat' : 'draft'
                        })
        tier2 = self.env['hr.contribution'].create({
                            'title_r': 'GLICO MASTER TRUST OCCUPATIONAL PENSION SCHEME TIER 2 ',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'tier_2' ,
                            'stat' : 'draft'
                        })
        tier3 = self.env['hr.contribution'].create({
                            'title_r': 'GLICO MASTER TRUST PROVIDENT FUND SCHEME (TIER 3)',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'tier_3' ,
                            'stat' : 'draft'
                        })
        payee_1 = self.env['hr.contribution'].create({
                            'title_r': 'PAYEE',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'payee' ,
                            'stat' : 'draft'
                        })
        welfare = self.env['hr.contribution'].create({
                            'title_r': 'GLICO STAFF WELFARE FUND',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'gw' ,
                            'stat' : 'draft'
                        })
        sinvest = self.env['hr.contribution'].create({
                            'title_r': 'STAFF INVESTMENT',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'si' ,
                            'stat' : 'draft'
                        })
        staff_lip = self.env['hr.contribution'].create({
                            'title_r': 'STAFF LIFE POLICY PREMIUM ',
                            'date': date.today(),
                            'sheet1': self.id,
                            'type_s' : 'slip' ,
                            'stat' : 'draft'
                        })
        slip100 = 0.0
        gw100 = 0.0
        si100 = 0.0
        payee11 = 0.0
        tier100 = 0.0
        tier200 = 0.0
        tier300 = 0.0
        for line in lines:
            employee = line.names
            # staff = employee.staff_number
            # tin = employee.tit_number
            # ssnit = employee.ssnit
            pf_staff = line.pf
            basic = line.basic12
            pf_empl = line.pf
            add_tier3 = line.adt
            ssf_55 = line.ssf
            pf_6 = (basic * 1) / 100
            per = (basic * 1) / 100
            wel = line.gw
            pfl = line.pfl
            loan = line.gw
            slip = line.slip
            gw = per + wel + pfl
            slip100 += slip
            gw100 += gw
            ta = line.allow
            ti = line.tax_in
            si = line.si
            si100 += si
            payee = line.paye
            payee11 += payee
            tier_3 = line.tier_3
            tier300 += tier_3
            tier_2 = line.tier_2
            tier200 += tier_2
            tier_1 = line.tier_1
            tier100 += tier_1
            si1000000 = self.env['hr.contribution.line'].create({
                'comm_id' : sinvest.id,
                # 'ssnit' : ssnit,
                'basic' : basic,
                # 'staff' : staff,
                'employee' : employee.id,
                'total' : si,
            })
            gwelfare = self.env['hr.contribution.line'].create({
                'comm_id' : welfare.id,
                # 'ssnit' : ssnit,
                'basic' : basic,
                'per' : per,
                'wel' : wel,
                'pfl' : pfl,
                'loan' : loan,
                # 'staff' : staff,
                'employee' : employee.id,
                'total' : gw,
            })
            tier11 = self.env['hr.contribution.line'].create({
                'comm_id' : tier1.id,
                # 'ssnit' : ssnit,
                'basic' : basic,
                # 'staff' : staff,
                'employee' : employee.id,
                'total' : tier_1,
            })
            pay = self.env['hr.contribution.line'].create({
                'comm_id' : payee_1.id,
                # 'tin' : tin,
                # 'ssnit' : ssnit,
                'basic' : basic,
                'ssf_55' : ssf_55,
                'pf_6' : pf_6,
                'ta' : ta,
                'ti' : ti,
                # 'staff' : staff,
                'employee' : employee.id,
                'total' : payee,
            })
            tier22 = self.env['hr.contribution.line'].create({
                'comm_id' : tier2.id,
                # 'ssnit' : ssnit,
                'basic' : basic,
                # 'staff' : staff,
                'employee' : employee.id,
                'total' : tier_2,
            })
            tier11 = self.env['hr.contribution.line'].create({
                'comm_id' : tier3.id,
                # 'ssnit' : ssnit,
                # 'staff' : staff,
                'basic' : basic,
                'pf_staff' : pf_staff,
                'pf_empl' : pf_empl,
                'add_tier3' : add_tier3,
                'employee' : employee.id,
                'total' : tier_3,
            })
            slip1 = self.env['hr.contribution.line'].create({
                'comm_id' : staff_lip.id,
                # 'ssnit' : ssnit,
                # 'staff' : staff,
                'basic' : basic,
                'employee' : employee.id,
                'total' : slip,
            })
        sinvest.amount = si100
        welfare.amount = gw
        staff_lip.amount = slip100
        tier1.amount = tier100
        tier2.amount = tier200
        tier3.amount = tier300
        payee_1.amount = payee11
        self.write({'state': 'posted'})

    def cancel(self):
        self.ensure_one()
        self.write({'state': 'draft'})

class payroll_advice_report(models.AbstractModel):
    _name = 'report.payroll_customisation.report_summary'
    _description = "Report Summary SHeet"
    
    def get_detail(self, line_ids):
        result = []
        for l in line_ids:
            res = {}
            res.update({
                    'code': l.code,
                    'names': l.names.name,
                    'basic': l.basic,
                    'ssf': l.ssf,
                    'pf': l.pf,
                    'allow': l.allow,
                    'to_cas_emo': l.to_cas_emo,
                    'tax_in': l.tax_in,
                    'paye': l.paye,
                    'other_deduc': l.other_deduc,
                    'to_deduc': l.to_deduc,
                    'net_sal': l.net_sal,
                    'ssf_13': l.ssf_13,
                    'tier_1': l.tier_1,
                    'tier_2': l.tier_2,
                    'tier_3': l.tier_3,
                    })
            result.append(res)
        result = sorted(result, key=itemgetter('names'))
        return result
    
    @api.model
    def _get_report_values(self, docids, data=None):
        summary = self.env['clientpi.submitsheet'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'clientpi.submitsheet',
            'data': data,
            'docs': summary,
            'get_detail': self.get_detail,
        }

class SubmitSheetline(models.Model):
    _name = 'clientpi.submitsheet.line'
    _description = 'Submit Sheet Report line'
    
    @api.depends('to_deduc', 'paye')
    def _compute_od(self):
        for line in self:
            if line.to_deduc:
                if line.paye:
                    line.other_deduc = line.to_deduc - line.paye
    
    @api.depends('ssf_13', 'ssf', 'pf')
    def _compute_t1(self):
        for line in self:
            if line.basic:
                line.tier_1 = line.ssf_13 + line.ssf - line.pf
                    
    @api.depends('pf')
    def _compute_t2(self):
        for line in self:
            if line.pf:
                line.tier_2 = line.pf
        
    @api.depends('pf', 'ssf_13', 'adt')
    def _compute_t3(self):
        for line in self:
            if line.pf:
                if line.ssf_13:
                    line.tier_3 = line.pf + line.pf + line.adt

    @api.depends('basic')
    def _basic(self):
        for line in self:
            if line.basic:
                if line.basic > 25000:
                    line.basic12 = 25000
                else :
                    line.basic12 = line.basic


    submitsheet_id = fields.Many2one('clientpi.submitsheet', string='Submit Sheet', auto_join=True, ondelete="cascade")
    names = fields.Many2one('hr.employee', string='Employee', required=True)
    code = fields.Char(string = ' STAFF NUMBER ') 
    basic = fields.Monetary(string = ' BASIC', currency_field='company_currency_id')
    basic12 = fields.Monetary(string = ' BASIC', compute = '_basic', store =True, currency_field='company_currency_id')
    ssf = fields.Monetary(string = "EMPLOYEE'S 5,5% SSF", currency_field='company_currency_id')
    pf = fields.Monetary(string = "EMPLOYEE'S 5% PF", currency_field='company_currency_id')
    pfl = fields.Monetary(string = "PF Loan", currency_field='company_currency_id')
    allow = fields.Monetary(string = 'ALLOWANCES', currency_field='company_currency_id')
    to_cas_emo = fields.Monetary(string = 'TOTAL CASH EMOLUMENT', currency_field='company_currency_id')
    tax_in = fields.Monetary(string = 'TAXABLE INCOME', currency_field='company_currency_id')
    paye = fields.Monetary(string = 'PAYE', currency_field='company_currency_id')
    slip = fields.Monetary(string = 'STAFF LIFE POLICY PREMIUM', currency_field='company_currency_id')
    other_deduc = fields.Monetary(string = 'OTHER DEDUCTION', compute='_compute_od', store=True, currency_field='company_currency_id')
    to_deduc = fields.Monetary(string = 'TOTAL DEDUCTION', currency_field='company_currency_id')
    adt = fields.Monetary(string = 'Additional Tier 3 Deduction', currency_field='company_currency_id')
    gw = fields.Monetary(string = 'Group Welfare', currency_field='company_currency_id')
    gw = fields.Monetary(string = 'Group Welfare', currency_field='company_currency_id')
    si = fields.Monetary(string = 'Staff Invest', currency_field='company_currency_id')
    net_sal = fields.Monetary(string = 'NET SALARY', currency_field='company_currency_id')
    ssf_13 = fields.Monetary(string = "EMPLOYER'S 13% SSF", currency_field='company_currency_id')
    tier_1 = fields.Monetary(string = '1st TIER 13.5%', compute = '_compute_t1', store =True, currency_field='company_currency_id')
    tier_2 = fields.Monetary(string = ' 2ND TIER 5%', compute = '_compute_t2', store =True, currency_field='company_currency_id')
    tier_3 = fields.Monetary(string = '3RD TIER (10% PF)', compute = '_compute_t3', store =True, currency_field='company_currency_id')
    company_id = fields.Many2one(related='names.company_id', store=True, readonly=True)
    company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency',
        readonly=True, store=True,
        help='Utility field to express amount currency')

class HrPayslipRunBCD(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'

    sum_sheet = fields.Boolean(string='Summary Sheet Generated ?',
                                help='If this box is checked which means that Summary sheet exists for current batch',
                                readonly=True, copy=False)


    def create_submitsheet11(self):
        for run in self:
            if run.sum_sheet == False:
                company = self.env.company
                submit = self.env['clientpi.submitsheet'].create({
                            'name_sub': run.id,
                            'start_date': run.date_start,
                            'end_date': run.date_end
                        })
                for slip in run.slip_ids:
                    # TODO is it necessary to interleave the calls ?
                    _logger.info("bill lines=== '" + str(slip.employee_id) + "' ok !")
                    # slip.action_payslip_done()
                    payslip_line = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id)], limit=1)
                    payslip_line_basic = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'BASIC')], limit=1)
                    payslip_line_ssf = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'SSF')], limit=1)
                    payslip_line_pf = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'PFa')], limit=1)
                    payslip_line_allow = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'TA')], limit=1)
                    payslip_line_to_cas_emo = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'GROSS')], limit=1)
                    payslip_line_tax_in = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'TTI')], limit=1)
                    payslip_line_paye = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'IT')], limit=1)
                    slip = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'SLIP')], limit=1)
                    payslip_line_adt = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'ADT')], limit=1)
                    payslip_line_gw = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'GW')], limit=1)
                    payslip_line_si = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'SI')], limit=1)
                    payslip_line_othe_deduc = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'TD')], limit=1)
                    payslip_line_to_deduc = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'DT')], limit=1)
                    payslip_line_net_sal = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
                    payslip_line_ssf_13 = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'ESSF')], limit=1)
                    if float(payslip_line_basic.total) < 25000:
                        basic12 = payslip_line_basic.total
                        _logger.info("mail=== '" + str(payslip_line_basic.total) + "' ok !")
                    else:
                        basic12 = 25000
                        _logger.info("mail=== '" + "montant superieur " + "' ok !")
                    payslip_line_epf5 = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'EPF')], limit=1)
                    if payslip_line:
                        self.env['clientpi.submitsheet.line'].create({
                            'submitsheet_id': submit.id,
                            'code': slip.employee_id.staff_number,
                            'names': slip.employee_id.id,
                            'basic': basic12,
                            'ssf': payslip_line_ssf.total,
                            'adt': payslip_line_adt.total,
                            'slip': slip.total,
                            'gw': payslip_line_gw.total,
                            'si': payslip_line_si.total,
                            'pf': payslip_line_pf.total,
                            'allow': payslip_line_allow.total,
                            'to_cas_emo': payslip_line_to_cas_emo.total,
                            'tax_in': payslip_line_tax_in.total,
                            'paye': payslip_line_paye.total,
                            'to_deduc': payslip_line_to_deduc.total,
                            'net_sal': payslip_line_net_sal.total,
                            'ssf_13': payslip_line_ssf_13.total,
                            'tier_2': payslip_line_epf5.total
                        })
                run.sum_sheet = True
                self.write({'state' : 'verify'})
            else:
                raise ValidationError("You cannot create a summary report for this Payslips Batches, there are already some")


    def create_submitsheet(self):
        for run in self:
            if run.sum_sheet == False:
                company = self.env.company
                submit = self.env['clientpi.submitsheet'].create({
                            'name_sub': run.id,
                            'start_date': run.date_start,
                            'end_date': run.date_end
                        })
                payslips = self.env['hr.payslip'].search([('payslip_run_id', '=', run.id)])
                for slip in payslips:
                     employee = slip.employee_id
                     lines = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id)])
                     if len(lines) > 0:
                        for line in lines:
                            code = line.code
                            total = line.total
                            if code == "BASIC":
                                basic = total
                            elif code == "SSF":
                                ssf = total
                            elif code == "PFa":
                                pf = total
                            elif code == "TA":
                                allow = total
                            elif code == "GROSS":
                                to_cas_emo = total
                            elif code == "TTI":
                                tax_in = total
                            elif code == "IT":
                                paye = total
                            elif code == "SLIP":
                                slip1 = total
                            elif code == "ADT":
                                adt = total
                            elif code == "GW":
                                gw = total
                            elif code == "SI":
                                si = total
                            elif code == "DT":
                                to_deduc = total
                            elif code == "NET":
                                net_sal = total
                            elif code == "ESSF":
                                ssf_13 = total
                            elif code == "PFL":
                                pfl = total
                        self.env['clientpi.submitsheet.line'].create({
                            'submitsheet_id': submit.id,
                            'code': employee.staff_number,
                            'names': employee.id,
                            'basic': basic,
                            'ssf': ssf,
                            'adt': adt,
                            'slip': slip1,
                            'gw': gw,
                            'si': si,
                            'pf': pf,
                            'pfl': pfl,
                            'allow': allow,
                            'to_cas_emo': to_cas_emo,
                            'tax_in': tax_in,
                            'paye': paye,
                            'to_deduc': to_deduc,
                            'net_sal': net_sal,
                            'ssf_13': ssf_13
                        })  
                run.sum_sheet = True
                self.write({'state' : 'verify'})
            else:
                raise ValidationError("You cannot create a summary report for this Payslips Batches, there are already some")


class HrPayslipBCD(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Payslip Pay'

    sum_sheet = fields.Boolean(string='Summary Sheet Generated ?',
                                help='If this box is checked which means that Summary sheet exists for current batch',
                                readonly=True, copy=False)
   
    def create_submitsheet(self):
        for run in self:
            if run.sum_sheet == False:
                company = self.env.company
                submit = self.env['clientpi.submitsheet'].create({
                            'name_sub1': run.id,
                            'start_date': run.date_from,
                            'end_date': run.date_to
                        })
                # TODO is it necessary to interleave the calls ?
                # run.action_payslip_done()
                payslip_line_id = self.env['hr.payslip.line'].search([('slip_id', '=', self.id)]).slip_id
                for slip in payslip_line_id:
                    payslip_line_basic = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'BASIC')], limit=1)
                    payslip_line_ssf = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'SSF')], limit=1)
                    payslip_line_pf = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'PFa')], limit=1)
                    payslip_line_allow = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'TA')], limit=1)
                    payslip_line_to_cas_emo = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'GROSS')], limit=1)
                    payslip_line_tax_in = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'TTI')], limit=1)
                    payslip_line_paye = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'IT')], limit=1)
                    adt = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'ADT')], limit=1)
                    payslip_line_to_deduc = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'DT')], limit=1)
                    payslip_line_net_sal = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'NET')], limit=1)
                    payslip_line_ssf_13 = self.env['hr.payslip.line'].search([('slip_id', '=', slip.id), ('code', '=', 'ESSF')], limit=1)
                    if payslip_line_id:
                        self.env['clientpi.submitsheet.line'].create({
                            'submitsheet_id': submit.id,
                            'code': slip.employee_id.staff_number,
                            'names': slip.employee_id.id,
                            'basic': payslip_line_basic.total,
                            'ssf': payslip_line_ssf.total,
                            'pf': payslip_line_pf.total,
                            'adt': adt.total,
                            'allow': payslip_line_allow.total,
                            'to_cas_emo': payslip_line_to_cas_emo.total,
                            'tax_in': payslip_line_tax_in.total,
                            'paye': payslip_line_paye.total,
                            'to_deduc': payslip_line_to_deduc.total,
                            'net_sal': payslip_line_net_sal.total,
                            'ssf_13': payslip_line_ssf_13.total
                        })
                run.sum_sheet = True
                self.write({'state' : 'voucher'})
            else:
                raise ValidationError("You cannot create a summary report for this Individual Payslips, there are already some")