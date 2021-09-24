from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
import datetime
import time
from datetime import date
import json
import requests
from operator import itemgetter
from itertools import groupby

class IndividualClaims(models.Model):
    _name = 'account.move.ind'
    _order = 'start_date desc'

    name = fields.Char(string = 'Name')
    start_date = fields.Date(string ='Start Date')
    end_date = fields.Date(string='End Date')
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('closed', 'Closed')
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    def action_post(self):
        self.ensure_one()
        # user = self.env['res.users'].search([('id', '=',2)], limit=1).userPI
        # passe = self.env['res.users'].search([('id', '=',2)], limit=1).passe
        # orgid = self.env['res.company'].search([('id', '=',1)], limit=1).orgid
        # remHost = self.env['res.company'].search([('id', '=',1)], limit=1).remHost
        # magik = self.env['res.company'].search([('id', '=',1)], limit=1).magik
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi    
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        url_login =url+'/ghi/c/ws/ws-login.php'
        urlInv = url+'/ghi/c/ws/'
        invoice_line_ids = []
        startd = self.env['clientpi.indiclaims'].search([('id', '=',self.id)], limit=1).start_date
        endd = self.env['clientpi.indiclaims'].search([('id', '=',self.id)], limit=1).end_date
        if connid :
            resbill = requests.get(urlInv, params={'source':'I','op': 'qclaims','submitted':0, 'connid':connid,'startd':startd,'endd':endd})
            databill = resbill.json()
            if databill["error"]==False :
                claims = databill["result"]["value"]
                sorted(claims, key = itemgetter('benid'))
                for benid in groupby(claims, key=itemgetter('benid','surname','lastname')):
                    benids = benid[0][0]
                    f_name = benid[0][1]
                    l_name = benid[0][2]
                    invoice_line_ids.append({'name': f_name + "  "+ l_name, 'benid':benids, 'claims_id' : self.id})
                if invoice_line_ids:
                    iclaims_id = self.env['clientpi.indiclaims.line'].create(invoice_line_ids)
                    self.state = 'posted'
        else: 
            raise ValidationError("Connection PI Fail, contact you adminstrator")
    
    def iclaims_cancel(self):
        self.ensure_one()
        startd = self.env['clientpi.indiclaims'].search([('id', '=',self.id)], limit=1).start_date
        endd = self.env['clientpi.indiclaims'].search([('id', '=',self.id)], limit=1).end_date
        benids = self.env['clientpi.indiclaims'].search([('id', '=',self.id)], limit=1).claims_line_id
        benids = int(benids)
        benid = self.env['clientpi.indiclaims.line'].search([('id', '=',benids)], limit=1).benid
        invoice_line_ids = []
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi  
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        url_login =url+'/ghi/c/ws/ws-login.php'
        urlInv = url+'/ghi/c/ws/'
        if connid:
            resbill = requests.get(urlInv, params={'benid':benid,'op': 'qoclaims','submitted':0, 'connid':connid,'startd':startd,'endd':endd})
            databill = resbill.json()
            if databill["error"]==False :
                claims = databill["result"]["value"]
                n= len(claims)
                if n > 0:
                    nom = claims[0]['surname']
                    prenom = claims[0]['lastname']
                    name_ven = nom +"  "+prenom
                    id_partner = self.env['res.partner'].search([('name', '=', name_ven)], limit=1).id
                    if id_partner:
                        id_part = id_partner
                    else:
                        partner_row = [
                                {
                                    "name" : name_ven
                                    , "state_id" : 10
                                    #, "spcode" : benid
                                    , "is_company":"True"
                                    , "customer_rank" : "0"
                                    , 'supplier_rank': '1'
                                    #, "email" : mail
                                }
                            ]
                        id_part = self.env['res.partner'].create(partner_row)
                for product in claims:
                    qte = product['qty']
                    cost = product['icost'] 
                    productName = product['productName']
                    pid = product['claimid']   
                    invoice_line_ids.append({'name': productName, 'quantity': qte, 'price_unit':cost, 'claimid': pid})
                    #r = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': pid, 's': "et"}) 
                if len(invoice_line_ids) == 0:
                        raise ValidationError("you have nothing to bill for this customer, please contact de Sale")
                else:
                    movebill = self.env['account.move'].with_context(default_type='in_invoice').create({
                        'type': 'in_invoice',
                        'partner_id':id_part,
                        'invoice_date': date.today(),
                        'date': date.today(),
                        #'currency_id': self.currency_usd_id,
                        #'currency_id': self.currency_usd_id,
                        'invoice_line_ids': invoice_line_ids,
                    })
                    movebill.post()
                    self.state = 'closed'
                    action = self.env.ref('account.action_move_in_invoice_type').read()[0]
                    action['domain'] = [
                        ('type', 'in', ('in_invoice', 'out_refund')),
                        ('state', '=', 'posted'),]
                    action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'sale','search_default_unpaid': 1}
                    return action
            else:
                raise ValidationError("fail fecthing line Bill")
        else :
            raise ValidationError("Connection PI Fail, contact you adminstrator")
                

class AccountMoveLine(models.Model):
    _name = "account.move.ind.line"
    _description = 'Individual Claims'
    
    name = fields.Char(string = 'Beneficiary Name')
    benid = fields.Char(string = 'Beneficiary ID')
    claims_id = fields.Many2one('clientpi.indiclaims', string='Individual Claims',
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade",
        help="The move of this entry line.")