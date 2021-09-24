# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from werkzeug import DispatcherMiddleware, url_encode
import logging
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
_logger = logging.getLogger(__name__)


class HrFetchClaimWizard(models.TransientModel):
    _name = "hr.register.claim.wizard"
    _description = "Feth Claims"

    @api.model
    def default_get(self, fields):
        result = super(HrFetchClaimWizard, self).default_get(fields)

        active_model = self._context.get('active_model')
        if active_model != 'res.partner':
            raise UserError(_('You can only apply this action from an contribution report.'))

        active_id = self._context.get('active_id')
        if 'partner_id' in fields and active_id:
            result['partner_id'] = active_id
        return result

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    def fetch_claim(self):
        partner = self.partner_id 
        spcode = self.partner_id.spcode
        startd = self.start_date
        endd = self.end_date
        _logger.info("mail=== '" + str(spcode) + "' ok !")
        movebill = self.get_bill(spcode, partner, startd, endd)
        movebill_id = movebill.id
        action = self.env.ref('account.action_move_in_invoice_type').read()[0]
        action['domain'] = [
                            ('type', 'in', ('in_invoice', 'out_refund')),
                            ('state', '=', 'posted'),
                            ('id', '=', movebill_id),
                            ('partner_id', 'child_of', partner.id),
                            ('Pi_from', '=', True)
                            ]
        action['context'] = {'default_type':'in_invoice', 'type':'in_invoice', 'journal_type': 'sale','search_default_unpaid': 1}
        # return {'type': 'ir.actions.act_window_close'}
        return action

    def get_bill(self, spcode, partner, startd, endd):
        self.ensure_one()
        if spcode == 1 : 
            movebill = self.get_indi_claims(startd, endd )
            return movebill
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
                resbill = requests.get(urlInv, params={'sp':spcode,'op': 'qoclaims','submitted':0, 'startd':startd, 'endd':endd, 'status':'ok', 'connid':connid, 'source':'S'})
                databill = resbill.json()
                if databill["error"]==False :
                    claim = ""
                    test = 0
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
                            if partner.tax_appl == True:
                                tax = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).supplier_taxes_id 
                                tax1 = self.env['product.template'].search([('idprod', '=', idprod)], limit=1).supplier_taxes_id1 
                                if partner.withtax == True:
                                    invoice_line_ids.append(
                                        {
                                            'name': productName
                                            , 'product_id': pro_id
                                            , 'quantity': qte
                                            , 'price_unit': u_price
                                            , 'claimid1': pid
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
                                            , 'claimid1': pid
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
                                    , 'claimid1': pid
                                    })
                            if test == 0:
                                claim = str(pid)
                                test = test + 1
                            else:
                                claim = claim + "," + str(pid)
                                test = test + 1
                            _logger.info("mail=== '" + str(invoice_line_ids) + "' ok !" + str(len(invoice_line_ids)))
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

                        acc = self.env['account.account'].search([('code', '=' ,'400217')], limit=1).id 
                        '''invoice_line_ids.append({
                            'name': "Discount"
                            , 'account_id': acc
                            , 'price_unit': 0.0
                            , 'quantity': 1
                            , 'exclude_from_invoice_tab': "True"
                            # , 'disc' : True
                            })'''

                        movebill = self.env['account.move'].with_context(default_type='in_invoice').create({
                            'type': 'in_invoice',
                            'partner_id': partner.id,
                            'invoice_date': dateclaim,
                            'ref1' : "Claims from : " + str(startd.strftime("%Y-%b-%d")) + " to " + str(endd.strftime("%Y-%b-%d")),
                            'invoice_payment_term_id': 2,
                            'date': dateclaim,
                            'Pi_from':True,
                            #'currency_id': self.currency_usd_id,
                            #'currency_id': self.currency_usd_id,
                            'invoice_line_ids': invoice_line_ids,
                        })
                        movebill.post()
                        rsd = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': claim, 's': ","}) 
                        _logger.info(str(rsd))

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
                        return movebill
                else:
                    self.env['res.company'].search([('id', '=',1)], limit=1).connect()
                    notification = {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': (' Connexion fail, Try again please later ! '),
                            'message': 'Connexion fail, Try again please later !',
                            'type':'info',  #types: success,warning,danger,info
                            'sticky': True,  #True/False will display for few seconds if false
                        },
                    }
                    return notification

    def get_indi_claims(self, startd, endd):
        invoice_line_ids = []
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'
        dateclaim = "2018-09-28"
        dateclaim = datetime.datetime.strptime(dateclaim,'%Y-%m-%d')
        if connid:
            resbill = requests.get(urlInv, params={'source':'I','op': 'qoclaims','submitted':0, 'startd':startd, 'endd':endd, 'status':'ok','connid':connid})
            databill = resbill.json()
            if databill["error"]==False :
                claim = ""
                test = 0
                claims = databill["result"]["value"]
                # ranger et regroupper par SP
                sorted(claims, key = itemgetter('extbenid'))
                for group, products in groupby(claims, key=itemgetter('extbenid')):
                    extbenid = group[0]
                    spClaims = group[1]
                    
                    lines = []
                    for product in products:
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
                        dateclaim0 = product['transdate']
                        dateclaim0 = datetime.datetime.strptime(dateclaim0, '%Y-%m-%d')
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
                                , 'claimid1': pid
                                }
                        lines.append(line)
                        if test == 0:
                            claim = str(pid)
                            test = test + 1
                        else:
                            claim = claim + "," + str(pid)
                            test = test + 1
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
                        'ref1' : "Claims from : " + str(startd.strftime("%Y-%b-%d")) + " to " + str(endd.strftime("%Y-%b-%d")),
                        'invoice_date': date.today(),
                        'date': dateclaim,
                        'invoice_payment_term_id': 2,
                        'Pi_from':True,
                        'invoice_line_ids': invoice_line_ids,
                    })
                    movebill.post()
                    rsd = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': claim, 's': ","})
                    return movebill

class PremiumTags(models.TransientModel):
    _name = "premium.tags"
    _description = "Premuin Tags"
    _order = "id desc, create_date desc"
    _rec_name ='name'

    tags = fields.Char(string='Tags')
    tagsid = fields.Integer(string='Tag ID')
    name = fields.Char(string='Name')

class HrFetchPremiumWizard(models.TransientModel):
    _name = "hr.register.premium.wizard"
    _description = "Feth premium"

    @api.model
    def default_get(self, fields):
        result = super(HrFetchPremiumWizard, self).default_get(fields)

        active_model = self._context.get('active_model')
        if active_model != 'res.partner':
            raise UserError(_('You can only apply this action from an contribution report.'))

        active_id = self._context.get('active_id')
        if 'partner_id' in fields and active_id:
            result['partner_id'] = active_id
        return result

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    policy_id = fields.Many2one('res.policy', string='Policy', compute='_poly')
    poli_id = fields.Many2one('res.policy.line',string='Policy ID ', domain="[('policy_id', '=', policy_id)]")
    tags = fields.Many2one('premium.tags',string='Tags ', help="Use this filter to create the invoice for a group of beneficiary with this tags, or leave blank to invoice all beneficiaries of this Suscriber")

    @api.depends('partner_id')
    def _poly(self):
        for line in self:
            if line.partner_id:
                polnu = self.env['res.policy'].search([('partner_id', '=', line.partner_id.id)])
                for polnum in polnu:
                        if len(polnum) == 1:
                            line.policy_id = polnum.id
                        elif len(polnum) > 1 :
                            for pol in polnum:
                                line.policy_id = pol.id


    def fetch_premium(self):
        partner = self.partner_id 
        suscrID = self.partner_id.subscrID
        polno = self.policy_id
        polno_id = self.poli_id
        tags = self.tags.tagsid
        
        movebill = self.get_invoices(polno, polno_id, partner, tags)
        movebill_id = movebill.id
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [
                            ('type', 'in', ('out_invoice', 'out_refund')),
                            ('state', '=', 'draft'),
                            ('id', '=', movebill_id),
                            ('partner_id', 'child_of', partner.id),
                            ('Pi_from', '=', True)
                            ]
        action['context'] = {'default_type':'out_invoice', 'type':'out_invoice', 'journal_type': 'sale'}
        # return {'type': 'ir.actions.act_window_close'}
        return action

    def get_invoices(self, polno, polno_id, partner, tags):
        self.ensure_one()
        if polno: 
            invoice_line_ids = []
            invoice_line_ids1 = []
            nbr = 0.0
            url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
            connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
            # url_login to connect to PI
            url_login =url+'/ghi/c/ws/ws-login.php'
            # urlInv for fetch line of invoice in PI
            urlInv = url+'/ghi/c/ws/'
            preexisting = 0
            nombre = 0
            child = 0

            if connid:
                if tags == 0:
                    resInv = requests.get(urlInv, params={'id':polno_id.poli_id,'op': 'qpolpremi', 'connid':connid})
                    resInv1 = requests.get(urlInv, params={'id':polno_id.poli_id,'op': 'qpolpremi', 'connid':connid, 'fgid': 'preexist'})
                else:
                    resInv = requests.get(urlInv, params={'id':polno_id.poli_id,'op': 'qpolpremi', 'connid':connid, 'tagid':tags})
                    resInv1 = requests.get(urlInv, params={'id':polno_id.poli_id,'op': 'qpolpremi', 'connid':connid, 'tagid':tags, 'fgid': 'preexist'})
                dataInv = resInv.json()
                dataInv1 = resInv1.json()
                if dataInv["error"] == False :
                    premiums = dataInv["result"]["value"]
                    n = len(premiums)
                    try :
                        def key_func(k):
                            return k['package']
                    except ValueError:
                        raise ValidationError("Please contact the administrator")
                    premiums = sorted(premiums, key=key_func)
                    for package, products in groupby(premiums, key_func):
                        name_packs = package
                        pro_i = self.env['product.template'].search([('name', '=', name_packs)], limit=1).id 
                        pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_i)], limit=1).id
                        invoice_line_ids.append({'name':"Package : " + name_packs, 'display_type':"line_section",'quantity':0})
                        child = 0
                        principal = 0 
                        spouse = 0
                        adult_dep = 0 
                        _logger.info("mail=== '" + str(name_packs) + "' ok !")
                        for prem in products:
                            factors = prem['factors']
                            age = prem['age']
                            premi = prem['premium']
                            factors_id = prem['rate_factor_names']
                            exten_id = prem['extbenid']
                            benId = prem['benid']
                            ben_id = self.env['res.partner'].search([('beneid', '=', benId)], limit=1)
                            bene_id = self.env['res.partner'].search([('extbenid', '=', exten_id)], limit=1)

                            if factors_id == "ages":
                                if age < "18" :
                                    typ = 'child'
                                    child_premium = premi
                                    name_child = factors
                                    invoice_line_ids1.append({'name':factors, 'product_id': pro_id,'price_unit':premi,'quantity':1, 'typ':typ})
                                    child = child + 1
                                else:
                                    typ = 'principal'
                                    adultd_premium = premi
                                    name_aduld = factors
                                    invoice_line_ids1.append({'name':factors, 'product_id': pro_id,'price_unit':premi,'quantity':1, 'typ':typ})
                                    if ben_id:
                                        if not ben_id.relation_id:
                                            principal = principal + 1
                                        else:
                                            if ben_id.relation_id.name == "spouse":
                                                spouse = spouse + 1
                                            else:
                                                adult_dep = adult_dep + 1
                            else:
                                typ = 'preexising'
                                # invoice_line_ids.append({'name':"Preexisting Conditions",'account_id':632,'price_unit': premi,'quantity': 1, 'typ':typ, 'exclude_from_invoice_tab':"True"})
                                preexisting = float(preexisting) + float(premi)
                        if principal != 0:
                            invoice_line_ids.append({'name':name_aduld, 'product_id': pro_id,'price_unit':adultd_premium,'quantity':principal, 'typ':'principal'})
                        if child != 0:
                            invoice_line_ids.append({'name':name_child, 'product_id': pro_id,'price_unit':child_premium,'quantity':child, 'typ':'child'})
                        if spouse != 0 :
                            invoice_line_ids.append({'name':name_aduld, 'product_id': pro_id,'price_unit':adultd_premium,'quantity':spouse, 'typ':'spouses'})
                        if adult_dep != 0:
                            invoice_line_ids.append({'name':name_aduld, 'product_id': pro_id,'price_unit':adultd_premium,'quantity':adult_dep, 'typ':'dep_a'})
                    if len(invoice_line_ids) == 0:
                        raise ValidationError("you have nothing to bill for this customer, please contact the Sale")
                    else:
                        if dataInv1["error"] == False:
                            premiums1 = dataInv1["result"]["value"]
                            def key_func1(z):
                                return z['benid']
                            premiums1 = sorted(premiums1, key=key_func1)
                            for package1 in groupby(premiums1, key_func1):
                                nombre = nombre + 1
                                _logger.info("product=== '" + str(package1[0]) + "' ok !")
                        acc = self.env['account.account'].search([('code', '=' ,'400217')], limit=1).id 
                        '''invoice_line_ids.append({
                            'name': "Discount"
                            , 'account_id': acc
                            , 'price_unit': 0.0
                            , 'quantity': 1
                            , 'exclude_from_invoice_tab': "True"
                            # , 'disc' : True
                            })'''
                        date = polno.startDate
                        invoice_line_ids.append({'name':"Preexisting Conditions",'account_id':632,'price_unit': preexisting,'quantity': 1, 'typ':'preexising', 'exclude_from_invoice_tab':"True"})
                        date1 = datetime.datetime.now().date()
                        move = self.env['account.move'].with_context(default_type='out_invoice').create({
                            'type': 'out_invoice',
                            'partner_id': partner.id,
                            'invoice_date': date,
                            'date': date1,
                            'nbr': nombre,
                            'policy': polno.id,
                            'policy_id': polno_id.id,
                            'preexisting': preexisting,
                            'Pi_from':True,
                            #'currency_id': self.currency_usd_id,
                            'invoice_line_ids': invoice_line_ids,
                        })
                        return move
                 