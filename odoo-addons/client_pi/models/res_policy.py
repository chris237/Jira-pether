# Copyright 2021 Pether Solutions - Elvige MEKONE <elvige.mekone@pether.io>

from odoo import api, fields, models,_, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime
import time
import calendar
from datetime import date
import json
import requests
from operator import itemgetter
import itertools
from itertools import groupby
from json import dumps
from itertools import zip_longest
from hashlib import sha256  
from datetime import date
from datetime import timedelta

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


class ResPolicy(models.Model):
    _name = 'res.policy'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Policy"
    _order = "id desc"
    _rec_name ='partner_id'

    
    partner_id = fields.Many2one('res.partner', string="Partner", tracking=True) 
    subscrID = fields.Integer(string="ID du subscriber", tracking=True)
    poli_num = fields.Char(string="Policy Number", tracking=True)
    startDate = fields.Date(string="Start Date", tracking=True)
    endDate = fields.Date(string="End Date", tracking=True)
    status_pol = fields.Char(string="Policy Status", tracking=True)
    line_ids = fields.One2many('res.policy.line', 'policy_id', 
                               string='Policies Line',
                               copy=False, readonly=True, tracking=True)

    def fetch_policy(self):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        today = fields.Date.today()
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlPol for fetch line of policies in PI
        urlPol = url+'/ghi/reg/ws/'
        if connid:
            respol = requests.get(urlPol, params={'op': 'qpols', 'asof': today, 'connid':connid})
            datapol = respol.json()
            if datapol["error"]==False :
                pols = datapol["result"]["value"][0]

                for policy in pols:
                        subscriberId = policy['subscriberId']
                        status = policy['status']
                        policyNo = policy['policyNo']
                        startdate = policy['startdate']
                        expiryDate = policy['expiryDate']  

                        idpart = self.env['res.partner'].search([('subscrID', '=', subscriberId)], limit=1)
                        polnum = self.env['res.policy'].search([('poli_num', '=', policyNo)], limit=1)
                        
                        if not polnum:
                            line = self.env['res.policy'].create({
                                'partner_id':idpart.id,
                                'subscrID':subscriberId,
                                'poli_num':policyNo,
                                'startDate':startdate,
                                'endDate':expiryDate,
                                'status_pol':status
                                })  
                            self.fetch_policy_line(line) 
                        else:
                            for part in polnum:
                                part.partner_id = idpart.id
                                part.subscrID = subscriberId
                                part.startDate = startdate
                                part.endDate = expiryDate
                                part.status_pol= status
                            self.fetch_policy_line(part) 

    def fetch_policy_line(self, polno):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        today = fields.Date.today()
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlPol for fetch line of policies in PI
        urlPol = url+'/ghi/reg/ws/'
        if connid:
            respol = requests.get(urlPol, params={'op': 'qpolrenews', 'polno': polno.poli_num, 'connid':connid})
            datapol = respol.json()
            if datapol["error"]==False :
                pols = datapol["result"]["value"]

                for policy in pols:
                        policyNo = policy['policyNo']
                        startDate = policy['startDate']
                        duration = policy['duration']
                        dur_unit = policy['dur_unit']
                        expiryDate = policy['expiryDate']  
                        remark = policy['remark']  
                        poli_id = policy['id']  

                        polnum = self.env['res.policy.line'].search([('poli_id', '=', poli_id)], limit=1)
                        
                        if not polnum:
                            line = self.env['res.policy.line'].create({
                                'poli_id':poli_id,
                                'startDate':startDate,
                                'expiryDate':expiryDate,
                                'unit':dur_unit,
                                'duration':duration,
                                'remark':remark,
                                'policy_id':polno.id
                                })  
                        # else:
                        #     for part in polnum:
                        #         part.poli_id = poli_id
                        #         part.startDate = startDate
                        #         part.expiryDate = expiryDate
                        #         part.dur_unit = dur_unit
                        #         part.duration = duration
                        #         part.remark = remark
                        #         part.policy_id = polno.id

class ResPolicyId(models.Model):
    _name = 'res.policy.line'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Policy Line"
    _order = "id desc"
    _rec_name ='startDate'

    
    poli_id = fields.Char(string="Policy ID", tracking=True)
    startDate = fields.Date(string="Start Date", tracking=True)
    expiryDate = fields.Date(string="End Date", tracking=True)
    duration = fields.Char(string="Duration ", tracking=True)
    unit = fields.Char(string="Unit ", tracking=True)
    remark = fields.Char(string="Remark ", tracking=True)
    policy_id = fields.Many2one('res.policy', stricg = "Policy Number", auto_join=True, ondelete="cascade", tracking=True)
