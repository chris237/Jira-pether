# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime
import time
from datetime import date
import json
import requests
from operator import itemgetter
import itertools
from itertools import groupby
from json import dumps
from itertools import zip_longest
from hashlib import sha256
from datetime import date, timedelta
import re

from collections import defaultdict
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
 
class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    # Souscriber data 
    subscrID = fields.Integer("ID du souscribe")
    branch = fields.Char("Branch")
    bank_name = fields.Char("Bank Name")
    account_n = fields.Char("Account Number")
    spcode = fields.Integer("ID du service provider")
    is_pro = fields.Boolean(string ="Is Prospect ?", default=False)

    # Services Provider data 
    tax_appl = fields.Boolean(string ="Tax Apply", default=True)
    withtax = fields.Boolean(string ="Withholding Tax", default=True)


    # Beneficiary  data 
    extbenid = fields.Char("Beneficiary Id")
    paka = fields.Char("Package")
    beneid = fields.Char("ID Beneficiary")
    bene = fields.Boolean( string="Benefiary", default=False, help="Check this field if the partner is a Beneficiary.")
    poli_num = fields.Char("Policy Number")
    principal1 = fields.Boolean("Principal", default = False, compute='_onchange_princ')
    principal = fields.Char("Principal")
    startDate = fields.Date("Start Date")
    status_pol = fields.Char("Policy Satus")
    enrolleeid = fields.Char(string="Enrollee ID ")
    relation_id = fields.Many2one('res.relation', string='Relation' )
    sex = fields.Char("Sex")
    dob = fields.Date("Date of Birht")
    bloodgroup = fields.Char("bloodgroup")
    
    def quatity(self):
        i = 0 
        with open("/home/test/data-quantity.json") as f:
            data = json.load(f)
            for line in data:
                id_line = line['id']
                quantity = line['quantity_moved3']
                lines = self.env['account.move.line'].search([('id','=', id_line)], limit=1)
                lines.quantity = quantity
                _logger.info("mail=== '" + str(i) + "' ok !")
                i += 1

    @api.depends('principal')
    def _onchange_princ(self):
        for line in self:
            if line.principal == "None":
                line.principal1 = True
            else: 
                line.principal1 = False

    def get_package(self):
        #user = self.env['res.users'].search([('id', '=',2)], limit=1).userPI
        #passe = self.env['res.users'].search([('id', '=',2)], limit=1).passe
        #orgid = self.env['res.company'].search([('id', '=',1)], limit=1).orgid
        #remHost = self.env['res.company'].search([('id', '=',1)], limit=1).remHost
        #magik = self.env['res.company'].search([('id', '=',1)], limit=1).magik
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        # urlSub for fetch line of invoice in PI
        urlSub = url+'/ghi/c/ws/'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/reg/ws/'
        if connid: 
            resSub = requests.get(urlSub, params={'op': 'qpkgs', 'connid':connid})
            dataSub = resSub.json()
            if dataSub["error"]==False :
                cate = dataSub["result"]["value"]
                for sub in cate:
                    pack_Id = sub['packageId']
                    name = sub['name']
                    default_code = sub['descr']
                    id_cat = self.env['product.template'].search([('idpack', '=', pack_Id)], limit=1).id
                    if id_cat :
                        print("test")
                        #id_part = self.env['res.partner'].write(id_partner, partner_row)
                    else: 
                        cat_row = [
                            {
                                "name" : name
                                , "idpack" : pack_Id
                                , 'type' : "consu"
                                , 'default_code' : default_code
                                , 'sale_ok' : True
                                , 'purchase_ok' : False
                            }
                        ]
                        id_categ = self.env['product.template'].create(cat_row)
        else: 
            raise ValidationError("Connection PI Fail, contact you adminstrator")
 
    def get_productcat(self):
        #user = self.env['res.users'].search([('id', '=',2)], limit=1).userPI
        #passe = self.env['res.users'].search([('id', '=',2)], limit=1).passe
        #orgid = self.env['res.company'].search([('id', '=',1)], limit=1).orgid
        #remHost = self.env['res.company'].search([('id', '=',1)], limit=1).remHost
        #magik = self.env['res.company'].search([('id', '=',1)], limit=1).magik
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        # urlSub for fetch line of invoice in PI
        urlSub = url+'/ghi/c/ws/'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/reg/ws/'
        if connid: 
            resSub = requests.get(urlSub, params={'op': 'qcats', 'connid':connid})
            dataSub = resSub.json()
            if dataSub["error"]==False :
                cate = dataSub["result"]["value"]
                for sub in cate:
                    catId = sub['catId']
                    name = sub['descr']
                    id_cat = self.env['product.template'].search([('idprod', '=', catId)], limit=1).id
                    if id_cat :
                        print("test")
                        #id_part = self.env['res.partner'].write(id_partner, partner_row)
                    else: 
                        cat_row = [
                            {
                                "name" : name
                                , "idprod" : catId
                                , 'type' : "consu"
                                , 'sale_ok' : False
                                , 'purchase_ok' : True
                            }
                        ]
                        id_categ = self.env['product.template'].create(cat_row)
        else: 
            raise ValidationError("Connection PI Fail, contact you adminstrator")

    def get_quote(self):
        self.ensure_one()
        suscrID = self.env['res.partner'].search([('id', '=', self.id)], limit=1).subscrID
        invoice_line_ids = []
        nbr = 0.0
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/c/ws/'
        if connid:
            resInv = requests.get(urlInv, params={'id':suscrID,'op': 'qcovsum', 'connid':connid})
            dataInv = resInv.json()
            if dataInv["error"] == False :
                lineInvoice = dataInv["result"]["value"]
                n = len(lineInvoice)
                pack = 3
                clas = 7
                rang= 9
                preexisting = 0
                nombre = 0
                premuin_adult = 0.0
                child = 0
                descr = ''
                adult = 0
                pro_id = 0
                unit_val = ''
                for i in range(3,n):
                    if i == pack:
                        name = lineInvoice[i][0]['name']
                        package = lineInvoice[i][0]['packageId']
                        pro_i = self.env['product.template'].search([('idpack', '=', package)], limit=1).id 
                        pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_i)], limit=1).id
                        descr = lineInvoice[i][0]['descr']
                        invoice_line_ids.append({'name':"Package : " + descr, 'display_type':"line_section",'quantity':0})
                        pack = pack + 7
                        a = {'name':"Package : " + descr, 'display_type':"line_section",'quantity':0}
                    if i == clas:
                        clas = clas + 7
                        lineIn = lineInvoice[i]
                        for lin in lineIn:
                            unit_value_name =lin['unit_value_name'] 
                            factor_grp_id = lin['factor_grp_id']
                            total = int(lin['total'])
                            premium = lin['premium']
                            total = int(total)
                            if factor_grp_id == "age":
                                # if total != 0:
                                if unit_value_name.count('Child') != 0:
                                    typ = 'child'
                                    invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premium,'product_uom_qty':total, 'typ':typ})
                                    child = total
                                else : 
                                    premuin_adult = premium
                                    adult = total + adult
                                    unit_val = unit_value_name
                            else :
                                if total !=0 :
                                    typ = 'preexising'
                                    invoice_line_ids.append({'name':"Preexisting Conditions",'account_id':83,'price_unit': premium,'product_uom_qty':total, 'typ':typ})
                                    preexisting = float(preexisting) + float(total) * float(premium)
                                    nombre = nombre + total
                    if i == rang:
                        rang = rang + 7
                        lineIn = lineInvoice[i]
                        qte_total = 0
                        for lincount in lineIn:
                            qte_total = qte_total + int(lincount['count'])
                        nbr = nbr + qte_total
                        adult_prin = 0
                        adult_spouse = 0
                        qtew = 0
                        if qte_total != 0:
                            for lin in lineIn:
                                rel = lin['relation']
                                qte = int(lin['count'])
                                if rel is None:
                                    if qte != 0 and premuin_adult != 0:
                                        typ = 'principal'
                                        invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premuin_adult,'product_uom_qty':qte, 'typ':typ})
                                        adult_prin = qte
                                elif rel == 'spouse':
                                    if qte != 0 and premuin_adult != 0:
                                        typ = 'spouses'
                                        invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premuin_adult,'product_uom_qty':qte, 'typ':typ})
                                        adult_spouse = qte
                                else:
                                    qtew = qte_total - adult_prin - adult_spouse - child
                                    typ = 'dep_a'
                            if qtew !=  0 and premuin_adult != 0:
                                invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premuin_adult,'product_uom_qty':qtew, 'typ':typ})

                    #print(invoice_line_ids)
                # if preexisting != 0:
                #     typ = 'preexising'
                #     invoice_line_ids.append({'name':"Preexisting Conditions",'account_id':83,'price_unit': preexisting,'quantity':1, 'typ':typ, 'exclude_from_invoice_tab':"True"})
                print(nombre)
                print(preexisting)
                if len(invoice_line_ids) == 0:
                    raise ValidationError("you have nothing to bill for this customer, please contact the Sale")
                else:
                    move = self.env['sale.order'].create({
                        'partner_id': self.id,
                        'date_order': date.today(),
                        # 'date': date.today(),
                        'nbr': nombre,
                        'preexisting': preexisting,
                        'Pi_from':True,
                        #'currency_id': self.currency_usd_id,
                        'order_line': invoice_line_ids
                    })
                    move.action_confirm()
                    action = self.env.ref('sale.action_quotations_with_onboarding').read()[0]
                    action['domain'] = [
                        ('partner_id', 'child_of', self.id),
                    ]
                    return action
            else:
                raise ValidationError("fail fecthing line Invoices")
        else :
            raise ValidationError("Connection PI Fail, contact you adminstrator")

    def get_invoicesrrrr(self):
        self.ensure_one()
        suscrID = self.env['res.partner'].search([('id', '=', self.id)], limit=1).subscrID
        invoice_line_ids = []
        nbr = 0.0
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlInv for fetch line of invoice in PI
        urlInv = url+'/ghi/c/ws/'
        if connid:
            resInv = requests.get(urlInv, params={'id':suscrID,'op': 'qcovsum', 'connid':connid})
            dataInv = resInv.json()
            if dataInv["error"] == False :
                lineInvoice = dataInv["result"]["value"]
                n = len(lineInvoice)
                pack = 3
                clas = 7
                rang= 9
                preexisting = 0
                nombre = 0
                premuin_adult = 0.0
                child = 0
                descr = ''
                adult = 0
                pro_id = 0
                unit_val = ''
                for i in range(3,n):
                    if i == pack:
                        name = lineInvoice[i][0]['name']
                        package = lineInvoice[i][0]['packageId']
                        pro_i = self.env['product.template'].search([('idpack', '=', package)], limit=1).id 
                        pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_i)], limit=1).id
                        descr = lineInvoice[i][0]['descr']
                        invoice_line_ids.append({'name':"Package : " + descr, 'display_type':"line_section",'quantity':0})
                        pack = pack + 7
                        a = {'name':"Package : " + descr, 'display_type':"line_section",'quantity':0}
                    if i == clas:
                        clas = clas + 7
                        lineIn = lineInvoice[i]
                        for lin in lineIn:
                            unit_value_name =lin['unit_value_name'] 
                            factor_grp_id = lin['factor_grp_id']
                            total = int(lin['total'])
                            premium = lin['premium']
                            total = int(total)
                            if factor_grp_id == "age":
                                if total != 0:
                                    if unit_value_name.count('Child') != 0:
                                        typ = 'child'
                                        invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premium,'quantity':total, 'typ':typ})
                                        child = total
                                else : 
                                    premuin_adult = premium
                                    adult = total + adult
                                    unit_val = unit_value_name
                            else :
                                if total !=0 :
                                    typ = 'preexising'
                                    invoice_line_ids.append({'name':"Preexisting Conditions",'account_id':83,'price_unit': premium,'quantity':total, 'typ':typ, 'exclude_from_invoice_tab':"True"})
                                    preexisting = float(preexisting) + float(total) * float(premium)
                                    nombre = nombre + total
                    if i == rang:
                        rang = rang + 7
                        lineIn = lineInvoice[i]
                        qte_total = 0
                        for lincount in lineIn:
                            qte_total = qte_total + int(lincount['count'])
                        nbr = nbr + qte_total
                        adult_prin = 0
                        adult_spouse = 0
                        qtew = 0
                        if qte_total != 0:
                            for lin in lineIn:
                                rel = lin['relation']
                                qte = int(lin['count'])
                                if rel is None:
                                    if qte != 0 and premuin_adult != 0:
                                        typ = 'principal'
                                        invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premuin_adult,'quantity':qte, 'typ':typ})
                                        adult_prin = qte
                                elif rel == 'spouse':
                                    if qte != 0 and premuin_adult != 0:
                                        typ = 'spouses'
                                        invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premuin_adult,'quantity':qte, 'typ':typ})
                                        adult_spouse = qte
                                else:
                                    qtew = qte_total - adult_prin - adult_spouse - child
                                    typ = 'dep_a'
                            if qtew !=  0 and premuin_adult != 0:
                                invoice_line_ids.append({'name':descr, 'product_id': pro_id,'price_unit':premuin_adult,'quantity':qtew, 'typ':typ})

                    #print(invoice_line_ids)
                # if preexisting != 0:
                #     typ = 'preexising'
                #     invoice_line_ids.append({'name':"Preexisting Conditions",'account_id':83,'price_unit': preexisting,'quantity':1, 'typ':typ, 'exclude_from_invoice_tab':"True"})
                print(nombre)
                print(preexisting)
                if len(invoice_line_ids) == 0:
                    raise ValidationError("you have nothing to bill for this customer, please contact the Sale")
                else:
                    acc = self.env['account.account'].search([('code', '=' ,'400217')], limit=1).id 
                    invoice_line_ids.append({
                        'name': "Discount"
                        , 'account_id': acc
                        , 'price_unit': 0.0
                        , 'quantity': 1
                        , 'exclude_from_invoice_tab': "True"
                        , 'disc' : True
                        })

                    move = self.env['account.move'].with_context(default_type='out_invoice').create({
                        'type': 'out_invoice',
                        'partner_id': self.id,
                        'invoice_date': date.today(),
                        'date': date.today(),
                        'nbr': nombre,
                        'preexisting': preexisting,
                        'Pi_from':True,
                        #'currency_id': self.currency_usd_id,
                        'invoice_line_ids': invoice_line_ids,
                    })
                    move.post()
                    action = self.env.ref('account.action_move_out_invoice_type').read()[0]
                    action['domain'] = [
                        ('type', 'in', ('out_invoice', 'out_refund')),
                        ('state', '=', 'posted'),
                        ('partner_id', 'child_of', self.id),
                    ]
                    action['context'] = {'default_type':'out_invoice', 'type':'out_invoice', 'journal_type': 'sale','search_default_unpaid': 1}
                    return action
            else:
                raise ValidationError("fail fecthing line Invoices")
        else :
            raise ValidationError("Connection PI Fail, contact you adminstrator")

    def get_b(self):
        invoice_line_ids = lines = []
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'
        if connid:
            resbill = requests.get(urlInv, params={'source':'S','op': 'qoclaims','submitted':0, 'connid':connid})
            databill = resbill.json()
            if databill["error"]==False :
                claims = databill["result"]["value"]
                def keyfunc(x):
                    return x['spCode']
                # ranger et regroupper par SP
                claims = sorted(claims, key=keyfunc)
                spGroups = itertools.groupby(claims, keyfunc)
                for group in spGroups:
                    spCode = group[0]
                    idv = self.env['res.partner'].search([('spcode', '=', spCode)], limit=1).id
                    spClaims = group[1]
                    def keyfun(x):
                        return x['batchCode']
                    invoice_line_ids = []
                    batchGroups = itertools.groupby(spClaims, keyfun)
                    for batchGroup in batchGroups:
                        batchCode =batchGroup[0]
                        # sur =batchGroup[1]
                        batchClaims =batchGroup[1]
                        # print(batchCode)
                        t = next(batchClaims)
                        f_name = t['surname']
                        l_name = t['lastname']
                        subscriberId = t['subscriberId']
                        subsp = self.env['res.partner'].search([('subscrID', '=', subscriberId)], limit=1).name
                        # invoice_line_ids.append({'name': "Batch"+ " : " + str(batchCode) + "  " + str(subsp) + "  " + str(f_name) + "  "+ str(l_name), 'display_type':'line_section'})
                        section ={'name': "Batch"+ " : " + str(batchCode) + "  " + str(subsp) + "  " + str(f_name) + "  "+ str(l_name), 'display_type':'line_section'}
                        for product in batchClaims:
                            qte = product['qty']
                            idprod = product['catId']
                            cost = product['icost'] 
                            u_price = float(cost) / float(qte)
                            productName = product['sysProductName']
                            if product['claimid'] != 0:
                                pid = product['claimid']
                            else:
                                pid = product['dispId']  
                            pro_i = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).id 
                            pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_i)], limit=1).id 
                            if self.tax_appl == True:
                                tax = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).supplier_taxes_id 
                                if self.withtax == True:
                                    invoice_line_ids.append(
                                        {
                                            'name': productName
                                            , 'product_id': pro_id
                                            , 'quantity': qte
                                            , 'price_unit': u_price
                                            , 'claimid': pid
                                            , 'tax_ids' : tax
                                            })
                                else:
                                    invoice_line_ids.append(
                                        {
                                            'name': productName
                                            , 'product_id': pro_id
                                            , 'quantity': qte
                                            , 'price_unit': u_price
                                            , 'claimid': pid
                                            , 'tax_ids' : tax[0]
                                            })
                            else:
                                lines.append(
                                    {
                                    'name': productName
                                    , 'product_id': pro_id
                                    , 'quantity': qte
                                    , 'price_unit': u_price
                                    , 'claimid': pid
                                    })
                            # r = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': pid, 's': "et"}) 
                        if len(lines) != 0:
                            invoice_line_ids.append(section)
                            invoice_line_ids = invoice_line_ids + lines
                    if len(invoice_line_ids) != 0:
                        movebill = self.env['account.move'].with_context(default_type='in_invoice').create({
                            'type': 'in_invoice',
                            'partner_id': idv,
                            'invoice_date': date.today(),
                            'date': date.today(),
                            'invoice_payment_term_id': 2,
                            'Pi_from':True,
                            #'currency_id': self.currency_usd_id,
                            #'currency_id': self.currency_usd_id,
                            'invoice_line_ids': invoice_line_ids,
                        })
                        movebill.post()

    # Fetch Invoices - Premium
    def fetch_prem(self):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'

        # self.env['res.policy'].fetch_policy()
        self.env['res.relation'].fetch_relation()
        if connid:
            resInv = requests.get(urlInv, params={'connid':connid,'op': 'qtags'})
            dataTag = resInv.json()
            _logger.info("datatags=== '" + str(dataTag) + "' ok !")
            if dataTag["error"] == False:
                lineTag = dataTag["result"]["value"]
                for tags in lineTag:
                    idtag = tags['tagid']
                    tag = tags['tag']
                    desc = tags['descr']
                    _logger.info("desc=== '" + str(desc) + "' ok !")
                    id_tag = self.env['premium.tags'].search([('tagsid', '=', idtag)], limit=1)
                    if id_tag:
                        for tagi in id_tag:
                            tagi.tags = tag
                            tagi.idtag = idtag
                            tagi.name = desc
                    else:
                        row = [{
                            'tags': tag,
                            'tagsid': idtag,
                            'name': desc
                        }]
                        _logger.info("row=== '" + str(row) + "' ok !")
                        id_part = self.env['premium.tags'].create(row)

        
        action = self.env.ref('client_pi.premium_fetch_wizard_action').read()[0] 
        return action

    # Fetch Bill Claims
    def fetch(self):
        action = self.env.ref('client_pi.claim_fetch_wizard_action').read()[0] 
        return action

    def get_bill(self):
        self.ensure_one()
        if self.spcode == 1 : 
            self.get_indi_claims()
            action = self.env.ref('account.action_move_in_invoice_type').read()[0]
            action['domain'] = [
                ('type', 'in', ('in_invoice', 'out_refund')),
                ('state', '=', 'posted'),
                ('partner_id', 'child_of', self.id),
                ('Pi_from', '=', True)
                ]
            action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'sale','search_default_unpaid': 1}
            return action
        else:
            invoice_line_ids = []
            url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
            connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
            # url_login to connect to PI
            url_login =url+'/ghi/c/ws/ws-login.php'
            # urlInv for fetch line of invoice in PI
            urlInv = url+'/ghi/c/ws/'
            dateclaim = "2018-09-28"
            dateclaim = datetime.datetime.strptime(dateclaim,'%Y-%m-%d')
            if connid:
                resbill = requests.get(urlInv, params={'sp':self.spcode,'op': 'qoclaims','submitted':0, 'connid':connid, 'source':'S'})
                #resbill = requests.get(urlInv, params={'sp':self.spcode,'op': 'qoclaims','submitted':1, 'connid':connid, 'source':'S', 'startd':'2020-11-1', 'endd':'2020-11-30', 'status':'ok','settled':0})
                databill = resbill.json()
                if databill["error"]==False :
                    claims = databill["result"]["value"]
                    sorted(claims, key = itemgetter('batchCode'))
                    for batchCode, products in groupby(claims, key=itemgetter('batchCode','surname','lastname','subscriberId')):
                        f_name = batchCode[1]
                        l_name = batchCode[2]
                        bcode = batchCode[0]
                        subscriberId = batchCode[3]
                        subsp = self.env['res.partner'].search([('subscrID', '=', subscriberId)], limit=1).name
                        invoice_line_ids.append({'name': "Batch"+ " : " + str(bcode) + "  " + str(subsp) + "  " + str(f_name) + "  "+ str(l_name), 'display_type':'line_section'})
                        for product in products:
                            qte = product['qty']
                            idprod = product['catId']
                            cost = product['icost'] 
                            u_price = float(cost) / float(qte)
                            productName = product['sysProductName']
                            dateclaim0 = product['transdate']
                            dateclaim0 = datetime.datetime.strptime(dateclaim0, '%Y-%m-%d')
                            pid = product['claimid']  
                            pro_i = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).id 
                            pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_i)], limit=1).id 
                            if self.tax_appl == True:
                                tax = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).supplier_taxes_id 
                                tax1 = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).supplier_taxes_id1 
                                if self.withtax == True:
                                    invoice_line_ids.append(
                                        {
                                            'name': productName
                                            , 'product_id': pro_id
                                            , 'quantity': qte
                                            , 'price_unit': u_price
                                            , 'claimid': pid
                                            , 'dateclaims' : dateclaim0
                                            , 'tax_ids' : tax1
                                            })
                                else:
                                    invoice_line_ids.append(
                                        {
                                            'name': productName
                                            , 'product_id': pro_id
                                            , 'quantity': qte
                                            , 'price_unit': u_price
                                            , 'claimid': pid
                                            , 'dateclaims' :dateclaim0
                                            , 'tax_ids' : tax
                                            })
                            else:
                                invoice_line_ids.append(
                                    {
                                    'name': productName
                                    , 'product_id': pro_id
                                    , 'quantity': qte
                                    , 'price_unit': u_price
                                    , 'dateclaims' :dateclaim0
                                    , 'claimid': pid
                                    })
                            #rsd = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': pid, 's': "et"}) 
                            dateclaim0 = product['transdate']
                            dateclaim0 = datetime.datetime.strptime(dateclaim0, '%Y-%m-%d')
                            if dateclaim0:
                                if dateclaim0 > dateclaim:
                                    dateclaim = dateclaim0
                    if len(invoice_line_ids) == 0:
                            raise ValidationError("you have nothing to bill for this customer, please contact de Sale")
                    else:
                        dat = dateclaim.month
                        if dat == 1:
                            mois = "BILL MONTH: JANUARY"
                        if dat == 2:
                            mois = "BILL MONTH: FEBUARY"
                        if dat == 3:
                            mois = "BILL MONTH: MARCH"
                        if dat == 4:
                            mois = "BILL MONTH: APRIL"
                        if dat == 5:
                            mois = "BILL MONTH: MAY"
                        if dat == 6:
                            mois = "BILL MONTH: JUNE"
                        if dat == 7:
                            mois = "BILL MONTH: JULY"
                        if dat == 8:
                            mois = "BILL MONTH: AUGUST"
                        if dat == 9:
                            mois = "BILL MONTH: SEPTEMBER"
                        if dat == 10:
                            mois = "BILL MONTH: OCTOBER"
                        if dat == 11:
                            mois = "BILL MONTH: NOVEMBER"
                        if dat == 12:
                            mois = "BILL MONTH:DECEMBER"


                        movebill = self.env['account.move'].with_context(default_type='in_invoice').create({
                            'type': 'in_invoice',
                            'partner_id': self.id,
                            'invoice_date': dateclaim,
                            'ref1' : mois,
                            'invoice_payment_term_id': 2,
                            'date': dateclaim,
                            'Pi_from':True,
                            #'currency_id': self.currency_usd_id,
                            #'currency_id': self.currency_usd_id,
                            'invoice_line_ids': invoice_line_ids,
                        })
                        movebill.post()

                        # create activity
                        date = datetime.datetime.now().date()
                        mail_id = self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id
                        model_id = self.env['ir.model'].search([('model', '=', 'account.move')]).id
                        users = self.env['account.send.notif'].search([], limit=1)
                        for user in users:
                            line = self.env['mail.activity'].create({
                                            'res_model_id': model_id, 
                                            'res_id': movebill.id,
                                            'activity_type_id': mail_id, 
                                            'date_deadline': date, 
                                            'user_id': user.accountant.id,
                                            'note': 'claims has been approved and needs to be paid.'
                                            })
                            movebill.id_activity = line.id


                        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
                        action['domain'] = [
                            ('type', 'in', ('in_invoice', 'out_refund')),
                            ('state', '=', 'posted'),
                            ('partner_id', 'child_of', self.id),
                            ('Pi_from', '=', True)
                            ]
                        action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'sale','search_default_unpaid': 1}
                        return action
                else:
                    raise ValidationError("fail fecthing line Bill")
            else :
                raise ValidationError("Connection PI Fail, contact you adminstrator")

    def get_indi_claims(self):
        invoice_line_ids = []
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'
        dateclaim = "2018-09-28"
        dateclaim = datetime.datetime.strptime(dateclaim,'%Y-%m-%d')
        if connid:
            resbill = requests.get(urlInv, params={'source':'I','op': 'qoclaims','submitted':0, 'connid':connid})
            databill = resbill.json()
            if databill["error"]==False :
                claims = databill["result"]["value"]
                def keyfunc(x):
                    return x['extbenid']
                # ranger et regroupper par SP
                claims = sorted(claims, key=keyfunc)
                spGroups = itertools.groupby(claims, keyfunc)
                for group in spGroups:
                    extbenid = group[0]
                    spClaims = group[1]
                    def keyfun(x):
                        return x['batchCode']
                    batchGroups = itertools.groupby(spClaims, keyfun)
                    for batchGroup in batchGroups:
                        batchCode =batchGroup[0]
                        # sur =batchGroup[1]
                        batchClaims =batchGroup[1]
                        # print(batchCode)
                        # t = next(batchClaims)
                        # f_name = t['surname']
                        # f_name = t['surname']
                        # l_name = t['lastname']
                        # sp = t['spCode']
                        # name = self.env['res.partner'].search([('spcode', '=', sp)], limit=1).name
                        # subscriberId = t['subscriberId']
                        # subsp = self.env['res.partner'].search([('subscrID', '=', subscriberId)], limit=1).name
                        # # invoice_line_ids.append({'name': "Batch"+ " : " + str(batchCode) + "  " + str(subsp) + "  " + str(f_name) + "  "+ str(l_name), 'display_type':'line_section'})
                        # section ={'name': str(f_name) + "  "+ str(l_name) + "(" + str(subsp) + ")" + " from " + str(name), 'display_type':'line_section'}
                        lines = []
                        for product in batchClaims:
                            #_logger.info("product=== '" + str(product) + "' ok !")
                            f_name = product['surname']
                            f_name = product['surname']
                            l_name = product['lastname']
                            sp = product['spCode']
                            name = self.env['res.partner'].search([('spcode', '=', sp)], limit=1).name
                            subscriberId = product['subscriberId']
                            subsp = self.env['res.partner'].search([('subscrID', '=', subscriberId)], limit=1).name
                            qte = product['qty']
                            idprod = product['catId']
                            cost = product['icost'] 
                            u_price = float(cost) / float(qte)
                            productName = str(product['sysProductName']) + str(product['productName'])
                            if product['claimid'] != 0:
                                pid = product['claimid']
                            else:
                                pid = product['dispId']  
                            pro_i = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).id 
                            pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_i)], limit=1).id 
                            line = {
                                    'name': productName
                                    , 'product_id': pro_id
                                    , 'quantity': qte
                                    , 'dateclaims': dateclaim0
                                    , 'price_unit': u_price
                                    , 'claimid': pid
                                    }
                            lines.append(line)
                            # r = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': pid, 's': "et"}) 
                            dateclaim0 = product['transdate']
                            dateclaim0 = datetime.datetime.strptime(dateclaim0, '%Y-%m-%d')
                            if dateclaim0:
                                if dateclaim0 > dateclaim:
                                    dateclaim = dateclaim0
                            _logger.info("bill lines=== '" + str(lines) + "' ok !")
                        if len(lines) != 0:
                            section = {'name': str(f_name) + "  "+ str(l_name) + "(" + str(subsp) + ")" + " from " + str(name), 'display_type':'line_section'}
                            invoice_line_ids.append(section)
                            invoice_line_ids = invoice_line_ids + lines
                idv1 = self.env['res.partner'].search([('spcode', '=', 1)], limit=1).id
                if idv1:
                    idv =idv1
                else: 
                    #partner_row = [{"name" : f_name + l_name, "city" : 'Accra', "beneid" : extbenid, "customer_rank" : "0", 'supplier_rank': '1', 'state_id' : 1189}]
                    partner_row = [
                        {
                            "name" : "DIVINE ASIEDU YEBOAH"
                            , "city" : 'Accra'
                            , "spcode" : 1
                            #, "beneid" : extbenid
                            , "is_company":"True"
                            , "customer_rank" : "0"
                            , 'supplier_rank': '1'
                            , 'state_id' : 1188
                            #, "email" : mail
                        }
                    ]
                    idv = self.env['res.partner'].create(partner_row)
                
                if len(invoice_line_ids) == 0:
                    raise ValidationError("you have nothing to bill for Individuals claims, please contact de Sale")
                else :
                    dat = dateclaim.month
                    if dat == 1:
                        mois = "BILL MONTH: JANUARY"
                    if dat == 2:
                        mois = "BILL MONTH: FEBUARY"
                    if dat == 3:
                        mois = "BILL MONTH: MARCH"
                    if dat == 4:
                        mois = "BILL MONTH: APRIL"
                    if dat == 5:
                        mois = "BILL MONTH: MAY"
                    if dat == 6:
                        mois = "BILL MONTH: JUNE"
                    if dat == 7:
                        mois = "BILL MONTH: JULY"
                    if dat == 8:
                        mois = "BILL MONTH: AUGUST"
                    if dat == 9:
                        mois = "BILL MONTH: SEPTEMBER"
                    if dat == 10:
                        mois = "BILL MONTH: OCTOBER"
                    if dat == 11:
                        mois = "BILL MONTH: NOVEMBER"
                    if dat == 12:
                        mois = "BILL MONTH:DECEMBER"
                    movebill = self.env['account.move'].with_context(default_type='in_invoice').create({
                        'type': 'in_invoice',
                        'partner_id': idv,
                        'ref1' : mois,
                        'invoice_date': date.today(),
                        'date': dateclaim,
                        'invoice_payment_term_id': 2,
                        'Pi_from':True,
                        'invoice_line_ids': invoice_line_ids,
                    })
                    movebill.post()