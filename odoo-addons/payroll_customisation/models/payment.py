# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models, tools, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, Warning
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime
import time
from datetime import date
import json
from calendar import monthrange
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

# class AccountPaymentvoucher(models.Model):
#     _inherit = "account.payment"

#     is_pv = fields.Boolean(string='Payment Voucher Payroll', default=False)


class pv_paroll(models.Model):
    _name = 'hr.pv'
    _description = 'Hr Payroll'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = "id desc, create_date desc"
    _rec_name = 'pv_num'
    
    payee = fields.Char("Payee's Name")
    prepa_by = fields.Char("Prepared By")
    currency = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env.company.currency_id)
    pv_num = fields.Char(readonly=True, copy=False) 
    id_activity = fields.Many2one('mail.activity', string='activity')
    id_payslip = fields.Many2one('hr.payslip', string='payslip')
    id_payslip_run = fields.Many2one('hr.payslip.run', string='payslip run')
    payment_date = fields.Date(string='Date', default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False, tracking=True)
    sign_prep = fields.Binary(string="Prepare signature")
    sign_appro = fields.Binary(string="approve signature")
    sign_verif = fields.Binary(string="verify signature")
    prepa = fields.Char(string="prepare user" , default=' ISHMAEL AHINSAH' , tracking=True)
    approveiud = fields.Char(string="approver user" , tracking=True)
    verifyiud = fields.Char(string="verify user", default=' ERNEST', tracking=True)
    # payement_mode = fields.Selection(
    #     [('manual', ' Bank Transfert'),
    #     ('cheque', 'Cheque')]
    # )
    payement_mode = fields.Selection(
        [('manual', ' Bank Transfert')]
    )
    amount = fields.Float("Amount ")
    narration = fields.Char("Narration")
    bank = fields.Char("Bank")
    amount_words = fields.Char(string="Amount in Words")
    cheque = check_number = fields.Char(string="Check Number", readonly=True, copy=False,
        help="The selected journal is configured to print check numbers. If your pre-printed check paper already has numbers "
             "or if the current numbering is wrong, you can change it in the journal configuration page.")
    date_cheque = fields.Date(string='Date')
    state = fields.Selection(
        [('draft', 'Draft'), 
         ('posted', 'Submitted'), 
         ('done', 'Verified'), 
         ('approve', 'Approved'), 
         ('cancelled', 'Cancelled')
         ], readonly=True, default='draft', copy=False, string="Status", tracking=True)

    def post(self):
        
        self.write({'prepa': self.env.user.name})
        sequence_code = 'account.payment.supplier.invoice'
        self.pv_num = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=self.payment_date)
        self.write({'state': 'posted'})
        if self.env.user.is_sign == True:
            self.write({'sign_prep': self.env.user.sign})


        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'hr.pv')]).id
        users = self.env['account.send.notif'].search([], limit=1)
        for pv in self:
            for user in users:
                if user.auditor.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': pv.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.auditor.id,
                                    'note': 'voucher are submited for needs to be verify.'
                                    })
                    ok=self.id_activity.action_done()                 
                    pmvs = self.env['hr.pv'].search([('id', '=', pv.id)]) 
                    for pmv in pmvs:
                        pmv.id_activity = line.id    

    def cancel(self):
        self.write({'state': 'draft'})

    def approve(self):
        self.write({'state': 'approve'})
        if self.env.user.is_sign == True:
            self.write({'sign_appro': self.env.user.sign})

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'hr.payslip')]).id
        model_id1 = self.env['ir.model'].search([('model', '=', 'hr.payslip.run')]).id
        users = self.env['account.send.notif'].search([], limit=1)
        for pv in self:
            for user in users:
                if user.finance_officer.id:
                    pmvs = self.env['hr.pv'].search([('id', '=', pv.id)])                 
                    for pmv in pmvs: 
                        if  pmv.id_payslip.id:
                            line = self.env['mail.activity'].create({
                                            'res_model_id': model_id, 
                                            'res_id': pmv.id_payslip.id,
                                            'activity_type_id': mail_id, 
                                            'date_deadline': date, 
                                            'user_id': user.finance_officer.id,
                                            'note': 'voucher are approved for needs to be send by email.'
                                            })
                            ok=self.id_activity.action_done()
                            pmv.id_activity = line.id 
                            pays = self.env['hr.payslip'].search([('id', '=', pmv.id_payslip.id)])
                            for pay in pays:
                                pay.id_activity = line.id   

                        elif pmv.id_payslip_run.id:  
                            line = self.env['mail.activity'].create({
                                            'res_model_id': model_id1, 
                                            'res_id': pmv.id_payslip_run.id,
                                            'activity_type_id': mail_id, 
                                            'date_deadline': date, 
                                            'user_id': user.finance_officer.id,
                                            'note': 'voucher are approved for needs to be send by email.'
                                            })
                            ok=self.id_activity.action_done()
                            pmv.id_activity = line.id    
                            runs = self.env['hr.payslip.run'].search([('id', '=', pmv.id_payslip_run.id)])
                            for run in runs:
                                run.id_activity = line.id   

    def verify(self):
        self.write({'state': 'done'})
        self.write({'verifyiud': self.env.user.name})
        if self.env.user.is_sign == True:
            self.write({'sign_verif': self.env.user.sign})

        date = datetime.datetime.now().date()
        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
        model_id = self.env['ir.model'].search([('model', '=', 'hr.pv')]).id
        users = self.env['account.send.notif'].search([], limit=1)
        for pv in self:
            for user in users:
                if user.ceo.id:
                    line = self.env['mail.activity'].create({
                                    'res_model_id': model_id, 
                                    'res_id': pv.id,
                                    'activity_type_id': mail_id, 
                                    'date_deadline': date, 
                                    'user_id': user.ceo.id,
                                    'note': 'voucher are verified for needs to be approve.'
                                    })
                    ok=self.id_activity.action_done()                 
                    pmvs = self.env['hr.pv'].search([('id', '=', pv.id)]) 
                    for pmv in pmvs:
                        pmv.id_activity = line.id 