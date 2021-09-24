# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime
#from datetime import date, datetime, timedelta
from itertools import groupby
from itertools import zip_longest
from hashlib import sha256
import json
from json import dumps
import requests
import time
import logging
_logger = logging.getLogger(__name__)


import json
import re

class ResPartnerSusc(models.Model):
    _inherit = 'res.partner'

    def get_bene(self):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi           
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid  
        test = 0   
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlSub for fetch line of invoice in PI
        urlSub = url+'/ghi/reg/ws/'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/reg/ws/'
        if connid:
            startd = datetime.datetime.now().date()
            endd = datetime.datetime.now().date()
            resSub = requests.get(urlSub, params={'op': 'qben4prin', 'connid':connid, 'startd': startd, 'endd': endd })
            dataSub = resSub.json()
            if dataSub["error"]==False :
                subscribers = dataSub["result"]["value"][0]
                for bene in subscribers:
                    policyNo = bene['policyNo']
                    benid = bene['benid']
                    extbenid = bene['extbenid']
                    enrolleeid = bene['enrolleeid']
                    principal = ''
                    relationid = ''
                    if principal != None:
                        principal = bene['principal']
                    if relationid != None:
                        relationid = bene['relationid']
                        relationid = self.env['res.relation'].search([('relation_id', '=', relationid)], limit=1).id
                    subscriberId = bene['subscriberId']
                    surname = bene['surname']
                    lastname = bene['lastname']
                    email = bene['email']
                    sex = bene['sex']
                    dob = bene['dob']
                    bloodgroup = bene['bloodgroup']
                    city = ''
                    if city != None:
                        city = bene['city']
                    beness = True
                    is_company = False
                    startDate = bene['startDate']
                    status = bene['status']
                    name = str(surname) + " " + str(lastname)
                    parent_id = self.env['res.partner'].search([('subscrID', '=', subscriberId)], limit=1)
                    id_bene = self.env['res.partner'].search([('beneid', '=', benid)], limit=1)
                    if id_bene: 
                        print("i")
                    else:
                        ben = []
                        ben = [
                            {
                                "name" : name ,
                                "poli_num" : policyNo ,
                                "beneid" : benid ,
                                "extbenid" : extbenid ,
                                "enrolleeid" : enrolleeid ,
                                "principal" : principal ,
                                "relation_id" : relationid ,
                                "parent_id" : parent_id.id ,
                                "sex" : sex ,
                                "dob" : dob ,
                                "email" : email ,
                                "bloodgroup" : bloodgroup ,
                                "startDate" : startDate ,
                                "city" : city ,
                                "status_pol" : status ,
                                "is_company" : is_company ,
                                "bene" : beness , 
                                "customer_rank" : "0", 
                                'supplier_rank': '0' 
                            }
                            ]
                        self.env['res.partner'].create(ben)
            else: 
                raise ValidationError("Internal error, contact you adminstrator")
        else: 
            raise ValidationError("Connection PI Fail, contact you adminstrator")
                  
    def get_suscribers(self):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi           
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid     
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlSub for fetch line of invoice in PI
        urlSub = url+'/ghi/reg/ws/'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/reg/ws/'
        if connid:
            resSub = requests.get(urlSub, params={'op': 'qe', 'connid':connid})
            dataSub = resSub.json()
            if dataSub["error"]==False :
                subscribers = dataSub["result"]["value"]
                for sub in subscribers:
                    name = sub['fullname']
                    idsubr = sub['subscriberId']
                    city = sub['city']
                    # email_tab = requests.get(urlSub, params={'op': 'qseaddrusable', 'connid':connid, 'e': idsubr})
                    # email_tab_json = email_tab.json()
                    # email = email_tab_json["result"]["value"]
                    # if len(email) == 0:
                    #     mail =  ""
                    # else:
                    #     mail= email[0]["email"] 
                    id_partner = self.env['res.partner'].search([('subscrID', '=', idsubr)], limit=1)
                    if id_partner :
                        for part in id_partner:
                            part.state_id = 1189
                            part.name = name
                            part.city = city
                            # id_partner.email= mail
                    else: 
                        partner_row = [
                            {
                                "name" : name
                                , "city" : city
                                , "subscrID" : idsubr
                                , "is_company":"True"
                                , "customer_rank" : "1"
                                , 'supplier_rank': '0'
                                , 'state_id' : 1189
                                #, "email" : mail
                            }
                        ]
                        id_part = self.env['res.partner'].create(partner_row)
                self.env['res.policy'].fetch_policy()
        else: 
            raise ValidationError("Connection PI Fail, contact you adminstrator")
                             
                
    def get_sp(self):
        # user = self.env['res.users'].search([('id', '=',2)], limit=1).userPI
        # passe = self.env['res.users'].search([('id', '=',2)], limit=1).passe
        # orgid = self.env['res.company'].search([('id', '=',1)], limit=1).orgid
        # remHost = self.env['res.company'].search([('id', '=',1)], limit=1).remHost
        # magik = self.env['res.company'].search([('id', '=',1)], limit=1).magik
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid        
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlSub for fetch line of invoice in PI
        urlSub = url+'/ghi/c/ws/'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/c/ws/'
        if connid:
            resSub = requests.get(urlSub, params={'op': 'qinaff', 'connid':connid})
            dataSub = resSub.json()
            if dataSub["error"]==False :
                vendors = dataSub["result"]["value"]
                for sub in vendors:
                    idsp = sub['spcode']
                    name = sub['name']
                    ville = sub['city']
                    id_partner = self.env['res.partner'].search([('spcode', '=', idsp)], limit=1)
                    id_par = self.env['res.partner'].search([('spcode', '=', idsp)], limit=1)
                    #state = self.env['res.country.state'].search([('name', '=', 'Accra')])
                    if id_partner :
                        for part in id_partner:
                            id_partner.state_id = 1189
                            id_partner.name = name
                            id_partner.city = ville
                        #partner_row = [{"name" : name, "city" : ville, "spcode" : idsp, "is_company":"True", "customer_rank" : "0", 'supplier_rank': '1', 'state_id' : 1189}]
                        #id_part = id_par.write(partner_row)
                        #r = requests.post(urlInv, data={'user':connid, 'op': 'logout', 'remoteHost': remHost})
                    else: 
                        partner_row = [
                            {
                                "name" : name
                                , "city" : ville
                                , "spcode" : idsp
                                , "is_company":"True"
                                , "customer_rank" : "0"
                                , 'supplier_rank': '1'
                                , 'state_id' : 1189
                                #, "email" : mail
                            }
                        ]
                        id_part = self.env['res.partner'].create(partner_row)
                #r = requests.post(url_login, data={'user':connid, 'op': 'logout', 'remoteHost': '154.72.167.161'}) 
            else:
                raise ValidationError("No SP")
        else:
            raise ValidationError("Connection PI Fail, contact you adminstrator")



