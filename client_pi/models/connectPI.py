# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
import json
import requests

class Companie(models.Model):
    _inherit = 'res.company'

    userPI = fields.Char("User Name ")
    passe = fields.Char("Password")
    footer_logo = fields.Binary(string="Footer Logo")
    remHost = fields.Char("RemHost ")
    magik = fields.Char("Magik")
    orgid = fields.Char("Organisation Id ")
    url_pi  = fields.Char("URL")
    connid = fields.Char("Connection ID")
    
    def connect(self):
        # user = self.env['res.users'].search([('id', '=',2)], limit=1).userPI
        # passe = self.env['res.users'].search([('id', '=',2)], limit=1).passe
        # orgid = self.env['res.company'].search([('id', '=',1)], limit=1).orgid
        # remHost = self.env['res.company'].search([('id', '=',1)], limit=1).remHost
        # magik = self.env['res.company'].search([('id', '=',1)], limit=1).magik
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        # url_login to connect to PI
        url_login =self.url_pi +'/ghi/c/ws/ws-login.php'
        payload = {'op':'login' 
                , 'user':self.userPI
                , 'pass' : self.passe
                , 'orgid' : self.orgid
                , 'mid' : 'undefined' 
                , 'midtype' : 'host' 
                , 'remHost' : self.remHost  
                , 'magik' : self.magik
                }
        r = requests.post(url_login, data=payload)
        data = r.json()
        if data["error"]==False :
            user = data["result"]["value"][0]
            self.connid = user[0]["appId"]
        else:
            print("Connection Fail")