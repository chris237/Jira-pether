# -*- coding: utf-8 -*-
# Copyright 2020 Pether Solutions - Christian Ferdinand FOTIE <christian.ferdinand@pethersolutions.com>
# send de claims for POS

from odoo import api, fields, models, _, tools
import requests
import xmlrpc.client
import json
import datetime
import time
from datetime import date
from odoo.exceptions import ValidationError, UserError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceInherit(models.Model):
    _inherit = "account.move"

    def button_cancel(self):
        self.mapped('line_ids').remove_move_reconcile()
        self.write({'state': 'cancel'})
        Lines = self.env['account.move'].search([('id', '=', self.id)])
        for Line in Lines :
            if Line.type == 'in_invoice' and Line.state == 'posted' and Line.invoice_payment_state == 'not_paid' and Line.Pi_from == True:
                # user = self.env['res.users'].search([('id', '=',2)], limit=1).userPI
                # passe = self.env['res.users'].search([('id', '=',2)], limit=1).passe
                # orgid = self.env['res.company'].search([('id', '=',1)], limit=1).orgid
                # remHost = self.env['res.company'].search([('id', '=',1)], limit=1).remHost
                # magik = self.env['res.company'].search([('id', '=',1)], limit=1).magik
                url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
                connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
                url_login =url+'/ghi/c/ws/ws-login.php'
                urlInv = url+'/ghi/c/ws/'
                if connid:
                    Lines = self.env['account.move.line'].search([('move_id', '=', self.id)])
                    for line in Lines:
                        if line.claimid1 :
                            cl = line.claimid1 
                            urlInv = url+'/ghi/c/ws/'
                            r = requests.delete(urlInv, data={'connid':connid, 'op': 'revsettled', 'id':cl})
                            r = requests.delete(urlInv, data={'connid':connid, 'op': 'revfetched', 'id':cl})

    def bill_processed(self):
        move = self.env['account.move'].search([('type', '=', 'in_invoice')])
        for move_id in move:
            if move_id.invoice_payment_state == "paid":
                #_logger.info("This is my debug message blugggggggggggggg ! ")
                if move_id.Pi_from ==True:
                    self.action_confirm_paid_bill(move_id.id)

    def action_confirm_paid_claim(self):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi    
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'
        if connid:
            Lines = self.env['account.move.line'].search([('move_id', '=', self.id)])
            for line in Lines:
                if line.claimid1:
                    if line.paym == False:
                        r = requests.post(urlInv, data={'connid':connid, 'id':int(line.claimid1), 'amount':line.price_subtotal, 'date':line.date, 'op': 'marksettled'})
                        line.paym = True
                    #print(r.status_code, r.reason)
        else :
            raise ValidationError("Connection PI Fail, contact you adminstrator")


    def action_confirm_paid_bill(self, move_id):
        i = 0
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi    
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'
        if connid:
            Lines = self.env['account.move.line'].search([('move_id', '=', move_id)])
            for line in Lines:
                if line.claimid1:
                    if line.paid_claim != True and line.fecth == False:
                        r = requests.post(urlInv, data={'connid':connid, 'id':int(line.claimid1), 'amount':line.price_subtotal, 'date':line.date, 'op': 'marksettled', 'settled': 1})
                        line.paid_claim = True
                        print(r.status_code, r.reason) 
                        i += 1
                if i == 500:
                    break
        else :
            raise ValidationError("Connection PI Fail, contact you adminstrator")        

    def claimid(self):
        moves = self.env['account.move'].search([('type', '=', 'in_invoice'),('Pi_from','=',True)])
        _logger.info(str(moves))
        for move in moves:
            #_logger.debug(rsd, line_id.fecth)
            lines = self.env['account.move.line'].search([('move_id', '=', move.id)])
            for line in lines:
                if line.claimid:
                    if line.claimid1 != 0.0:
                        claim = line.claimid
                        line.claimid1 = claim

    def claims_processed(self):
        test = i = 0
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi    
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        urlInv = url+'/ghi/c/ws/'
        moves = self.env['account.move'].search([('type', '=', 'in_invoice'),('Pi_from','=',True),('state', '=', 'posted')])
        claim = ""
        for move in moves:
            #_logger.debug(rsd, line_id.fecth)
            line = self.env['account.move.line'].search([('move_id', '=', move.id)])
            for line_id in line:
                # if line_id.parent_state == "posted":
                # _logger.info("This is my debug message blugggggggggggggg ! ")
                if (line_id.claimid1 > 0.0) and (line_id.fecth == False or not line_id.fecth):
                    # rsd = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': line_id.claimid1, 's': "et"}) 
                    if test == 0:
                        claim = str(line_id.claimid1)
                    else:
                        claim = claim + "," + str(line_id.fecth)
                    line.fecth = True
            test = test + 1
            if test > 300:
                break
            
        rsd = requests.post(urlInv, data={'connid':connid, 'op': 'markfetched', 'id': claim, 's': ","}) 
        _logger.info(str(rsd))
        

