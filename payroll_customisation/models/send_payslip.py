# -*- coding: utf-8 -*-

from odoo import api, fields, models,tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class SendPayslips(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread']

    em = fields.Boolean(string ="send by email", default=False)

    def send_email_from(self):
        outmails = self.env['ir.mail_server'].search([])
        for outmail in outmails:
            smtpuser = outmail.smtp_user

        return smtpuser  
    
    def send_payslip(self):

        self.ensure_one()
        template = self.env.ref('payroll_customisation.payslip_mail_template', False)
        ctx = dict(self.env.context) or {}
        for payslip in self:
            email_to = ''
            if payslip.employee_id.work_email:
                email_to = payslip.employee_id.work_email
            elif payslip.employee_id.user_id and payslip.employee_id.user_id.partner_id and payslip.employee_id.user_id.partner_id.email:
                email_to = payslip.employee_id.user_id.partner_id.email
            if email_to:
                start_date = payslip.date_from
                start_date = datetime.strptime(str(payslip.date_from), DF).date()
                start_date_format = start_date.strftime("%m/%d/%Y")
                end_date = datetime.strptime(str(payslip.date_to), DF).date()
                end_date_format = end_date.strftime("%m/%d/%Y")
                ctx.update({'email_to': email_to, 'start_date': start_date_format, 'end_date': end_date_format})
                template.with_context(ctx).send_mail(payslip.id, force_send=True, raise_exception=True)
            if self.em == False:
                self.write({'em': True})
                self.write({'state' : 'done'})

        ok=self.id_activity.action_done() 

        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': (' Send mail Payroll ! '),
                'message': ' The mail is sent ',
                'type':'success',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
            },
        }
        return notification

    
class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    em = fields.Boolean(string ="send by email", default=False)

    def action_send_payslips(self):
        self.ensure_one()
        template = self.env.ref('payroll_customisation.payslip_mail_template', False)
        ctx = dict(self.env.context) or {}
        for payslip in self.slip_ids:
            email_to = ''
            if payslip.employee_id.work_email:
                email_to = payslip.employee_id.work_email
            elif payslip.employee_id.user_id and payslip.employee_id.user_id.partner_id and payslip.employee_id.user_id.partner_id.email:
                email_to = payslip.employee_id.user_id.partner_id.email
            if email_to:
                start_date = payslip.date_from
                start_date = datetime.strptime(str(payslip.date_from), DF).date()
                start_date_format = start_date.strftime("%m/%d/%Y")
                end_date = datetime.strptime(str(payslip.date_to), DF).date()
                end_date_format = end_date.strftime("%m/%d/%Y")
                ctx.update({'email_to': email_to, 'start_date': start_date_format, 'end_date': end_date_format})
                template.with_context(ctx).send_mail(payslip.id, force_send=True, raise_exception=True)
            if self.em == False:
                self.write({'em': True})
                self.write({'state' : 'close1'})

        ok=self.id_activity.action_done()        
