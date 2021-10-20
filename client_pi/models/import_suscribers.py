# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import datetime
import time
from datetime import date
import json
import requests

class ResPartnerSusc(models.Model):
    _inherit = 'res.partner'
    
    def get_suscribers(self):
        self.ensure_one()
        # url_login to connect to PI
        url_login ='https://api.testing.pethersolutions.com/ghi/c/ws/ws-login.php'
        # urlSub for fetch line of invoice in PI
        urlSub = 'https://api.testing.pethersolutions.com/ghi/reg/ws/'
        # urlInv for fetch line of invoice in PI
        urlInv = 'https://api.testing.pethersolutions.com/ghi/c/ws/'
        payload = {'op':'login' 
                , 'user':'christian'
                , 'pass' : 'christian123'
                , 'orgid' : '1'
                , 'mid' : 'undefined' 
                , 'midtype' : 'host' 
                
                }
        r = requests.post(url_login, data=payload)
        data = r.json()
        if data["error"]==False :
            user = data["result"]["value"][0]
            appId = user[0]["appId"]
            resSub = requests.get(urlSub, params={'op': 'qe', 'connid':appId})
            dataSub = resSub.json()
            if dataSub["error"]==False :
                subscribers = dataSub["result"]["value"]
                for sub in subscribers:
                    name = sub['fullname']
                    idsubr = sub['subscriberId']
                    city = sub['city']
                    email_tab = requests.get(urlSub, params={'op': 'qseaddrusable', 'connid':appId, 'e': idsubr})
                    email_tab_json = email_tab.json()
                    email = email_tab_json["result"]["value"]
                    if len(email) == 0:
                        mail =  ""
                    else:
                        mail= email[0]["email"]
                    id_partner = self.env['res.partner'].search([('subscrID', '=', idsubr)], limit=1).id
                    if id_partner :
                        print("test")
                    else: 
                        partner_row = [
                            {
                                "name" : name
                                , "city" : city
                                , "subscrID" : idsubr
                                , "is_company":"True"
                                , "customer_rank" : "1"
                                , 'supplier_rank': '0'
                                , "email" : mail
                            }
                        ]
                        id_part = self.env['res.partner'].create(partner_row)
                        