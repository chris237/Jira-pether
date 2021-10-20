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
class DeferredReport(models.Model):
    '''
    Deferred Report
    '''
    _name = 'deferred.report'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Deferred Report"
    _order = "id desc, date desc"
    _rec_name ='number'

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())
    
    date = fields.Date(readonly=True , index=True, tracking=True, required=True, string='Date', states={'draft': [('readonly', False)]}, default=_get_default_date)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft', index=True, tracking=True, readonly=True)
    line_ids = fields.One2many('deferred.report.line', 'deferred_report_id', string='Deferred Report' , index=True, copy=True, readonly=True,
        domain=[('exclude_from_def_tab', '=', False)],
        states={'draft': [('readonly', False)]})
    deferred_line_ids = fields.One2many('deferred.report.line', 'deferred_report_id', string='Revenue Board' , index=True, copy=True, readonly=True,
        domain=[('exclude_from_rev_tab', '=', False)],
        states={'draft': [('readonly', False)]})    
    invoice = fields.Many2one('account.move', string='Invoice')    
    number = fields.Char(string='Reference', readonly=True, index=True, tracking=True)    
 

    def compute(self):
        results = []
        next_y=next_ys = 0
        deferreds = self.env['deferred.report'].search([])
        for defer in deferreds:
            if defer.invoice:
                deferrs = self.env['deferred.report.line'].search([('deferred_report_id', '=', defer.id)])
                for deferr in deferrs:
                    move = self.env['account.move'].search([('id', '=', deferr.move.id)], limit=1)
                    startdate = self.env['res.policy'].search([('id', '=', move.policy.id)], limit=1).startDate
                    enddate = self.env['res.policy'].search([('id', '=', move.policy.id)], limit=1).endDate
                    poli_numb = self.env['res.policy'].search([('id', '=', move.policy.id)], limit=1).poli_num
                    this_year = date.today().year

                    if deferr.revenue_date:
                        d_date0 = deferr.revenue_date
                        d_date = d_date0.month 
                        d_year = d_date0.year
                        if this_year == d_year:
                            if d_date == 1:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':deferr.revenue,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)
                            elif d_date == 2:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':deferr.revenue,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)
                            elif d_date == 3:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':deferr.revenue,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)
                            elif d_date == 4:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':deferr.revenue,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res) 
                            elif d_date == 5:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':deferr.revenue,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res) 
                            elif d_date == 6:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':deferr.revenue,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)  
                            elif d_date == 7:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':deferr.revenue,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)  
                            elif d_date == 8:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':deferr.revenue,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)  
                            elif d_date == 9:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':deferr.revenue,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)  
                            elif d_date == 10:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':deferr.revenue,
                                    'nov1':0,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)  
                            elif d_date == 11:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':deferr.revenue,
                                    'dec1':0, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)  
                            elif d_date == 12:
                                res=({
                                    'deferred_report_id1':self.id,
                                    'deferred_report_id2':defer.id,
                                    'poli_numb1': poli_numb,
                                    'start_date1': startdate,
                                    'end_date1':enddate,
                                    'partner1': move.partner_id.id,
                                    'premium_amount1':move.amount_untaxed,
                                    'jan1':0,
                                    'feb1':0,
                                    'mar1':0,
                                    'apr1':0,
                                    'may1':0,
                                    'jun1':0,
                                    'jul1':0,
                                    'aug1':0,
                                    'sep1':0,
                                    'oct1':0,
                                    'nov1':0,
                                    'dec1':deferr.revenue, 
                                    'next_year1':0,
                                    'exclude_from_rev_tab1': True,
                                    'move1':move.id, 
                                })
                                results.append(res)                                     

                        else:
                            next_ys += deferr.revenue
                            res=({
                                'deferred_report_id1':self.id,
                                'deferred_report_id2':defer.id,
                                'poli_numb1': poli_numb,
                                'start_date1': startdate,
                                'end_date1':enddate,
                                'partner1': move.partner_id.id,
                                'premium_amount1':move.amount_untaxed,
                                'jan1':0,
                                'feb1':0,
                                'mar1':0,
                                'apr1':0,
                                'may1':0,
                                'jun1':0,
                                'jul1':0,
                                'aug1':0,
                                'sep1':0,
                                'oct1':0,
                                'nov1':0,
                                'dec1':0, 
                                'next_year1':next_ys, 
                                'exclude_from_rev_tab1': True,
                                'move1':move.id, 
                            })
                            results.append(res)
                        
                next_ys = 0    
                            
                             
        def keyfun(x):
            return x['deferred_report_id2']
        lineGroups = itertools.groupby(results, keyfun)
        for resu in lineGroups:
            defer_id2 = resu[0]
            line_moves = resu[1]
            jans=fevs=mars=avrs=mays=juns=juls=augs=seps=octs=novs=decs=0
            for line_move in line_moves:
                jans += line_move['jan1']
                fevs += line_move['feb1']
                mars += line_move['mar1']
                avrs += line_move['apr1']
                mays += line_move['may1']
                juns += line_move['jun1']
                juls += line_move['jul1']
                augs += line_move['aug1']
                seps += line_move['sep1']
                octs += line_move['oct1']
                novs += line_move['nov1']
                decs += line_move['dec1']   

            line = self.env['deferred.report.line'].create({
                'deferred_report_id':line_move['deferred_report_id1'],
                'poli_numb':line_move['poli_numb1'],
                'start_date':line_move['start_date1'],
                'end_date':line_move['end_date1'],
                'partner_id': line_move['partner1'],
                'premium_amount':line_move['premium_amount1'],
                'jan':jans,
                'feb':fevs,
                'mar':mars,
                'apr':avrs,
                'may':mays,
                'jun':juns,
                'jul':juls,
                'aug':augs,
                'sep':seps,
                'oct':octs,
                'nov':novs,
                'dec':decs,
                'next_year':line_move['next_year1'], 
                'exclude_from_rev_tab': line_move['exclude_from_rev_tab1'],
                'move':line_move['move1']
                })   
        self.confirm_sheet()



        # assets = self.env['account.asset'].search([])
        # for ass in assets:
        #     next_y=next_ys = 0
        #     if ass.model_id:
        #         moves = self.env['account.move'].search([('asset_id', '=', ass.id)])
        #         id_move = self.env['account.move.line'].search([('asset_id', '=', ass.id)]).move_id
        #         partnerid = self.env['account.move'].search([('id', '=', id_move.id)]).partner_id.id
        #         for mov in moves.sorted(lambda x: x.id): 
        #             startdate = self.env['res.policy'].search([('partner_id', '=', partnerid)], limit=1).startDate
        #             enddate = self.env['res.policy'].search([('partner_id', '=', partnerid)], limit=1).endDate
        #             poli_numb = self.env['res.policy'].search([('partner_id', '=', partnerid)], limit=1).poli_num
        #             this_year = date.today().year

        #             m_date0 = mov.date
        #             m_date = m_date0.month   
        #             m_year = m_date0.year
        #             if this_year == m_year:
        #                 if m_date == 1:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':mov.amount_total,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)
        #                 elif m_date == 2:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':mov.amount_total,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res) 
        #                 elif m_date == 3:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':mov.amount_total,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)  
        #                 elif m_date == 4:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':mov.amount_total,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res) 
        #                 elif m_date == 5:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':mov.amount_total,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)   
        #                 elif m_date == 6:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':mov.amount_total,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res) 
        #                 elif m_date == 7:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':mov.amount_total,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0,
        #                         'next_year1':0, 
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)
        #                 elif m_date == 8:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':mov.amount_total,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)   
        #                 elif m_date == 9:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':mov.amount_total,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)
        #                 elif m_date == 10:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':mov.amount_total,
        #                         'nov1':0,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)  
        #                 elif m_date == 11:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':mov.amount_total,
        #                         'dec1':0, 
        #                         'next_year1':0,
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)    
        #                 elif m_date == 12:
        #                     res=({
        #                         'asset_id1':mov.asset_id.id,
        #                         'deferred_report_id1':self.id,
        #                         'poli_numb1': poli_numb,
        #                         'start_date1': startdate,
        #                         'end_date1':enddate,
        #                         'partner1': partnerid,
        #                         'premium_amount1':ass.original_value,
        #                         'jan1':0,
        #                         'feb1':0,
        #                         'mar1':0,
        #                         'apr1':0,
        #                         'may1':0,
        #                         'jun1':0,
        #                         'jul1':0,
        #                         'aug1':0,
        #                         'sep1':0,
        #                         'oct1':0,
        #                         'nov1':0,
        #                         'dec1':mov.amount_total,
        #                         'next_year1':0, 
        #                         'exclude_from_rev_tab1': True,
        #                         'move1':mov.id, 
        #                     })
        #                     results.append(res)                       

        #             else:
        #                 next_ys +=  mov.amount_total
        #                 res=({
        #                     'asset_id1':mov.asset_id.id,
        #                     'deferred_report_id1':self.id,
        #                     'poli_numb1': poli_numb,
        #                     'start_date1': startdate,
        #                     'end_date1':enddate,
        #                     'partner1': partnerid,
        #                     'premium_amount1':ass.original_value,
        #                     'jan1':0,
        #                     'feb1':0,
        #                     'mar1':0,
        #                     'apr1':0,
        #                     'may1':0,
        #                     'jun1':0,
        #                     'jul1':0,
        #                     'aug1':0,
        #                     'sep1':0,
        #                     'oct1':0,
        #                     'nov1':0,
        #                     'dec1':0, 
        #                     'next_year1':next_ys, 
        #                     'exclude_from_rev_tab1': True,
        #                     'move1':mov.id, 
        #                 })
        #                 results.append(res)

        #             # date_end=mov.date
        #         # _logger.info("next_y=== '" + str(next_y) + "' ok !")
        # def keyfun(x):
        #     return x['asset_id1']
        # lineGroups = itertools.groupby(results, keyfun)
        # for resu in lineGroups:
        #     asset_id2 = resu[0]
        #     line_moves = resu[1]
        #     jans=fevs=mars=avrs=mays=juns=juls=augs=seps=octs=novs=decs=0
        #     for line_move in line_moves:
        #         jans += line_move['jan1']
        #         fevs += line_move['feb1']
        #         mars += line_move['mar1']
        #         avrs += line_move['apr1']
        #         mays += line_move['may1']
        #         juns += line_move['jun1']
        #         juls += line_move['jul1']
        #         augs += line_move['aug1']
        #         seps += line_move['sep1']
        #         octs += line_move['oct1']
        #         novs += line_move['nov1']
        #         decs += line_move['dec1']                    
                    
        #     line = self.env['deferred.report.line'].create({
        #         'deferred_report_id':line_move['deferred_report_id1'],
        #         'poli_numb':line_move['poli_numb1'],
        #         'start_date':line_move['start_date1'],
        #         'end_date':line_move['end_date1'],
        #         'partner_id': line_move['partner1'],
        #         'premium_amount':line_move['premium_amount1'],
        #         'jan':jans,
        #         'feb':fevs,
        #         'mar':mars,
        #         'apr':avrs,
        #         'may':mays,
        #         'jun':juns,
        #         'jul':juls,
        #         'aug':augs,
        #         'sep':seps,
        #         'oct':octs,
        #         'nov':novs,
        #         'dec':decs,
        #         'next_year':line_move['next_year1'], 
        #         'exclude_from_rev_tab': line_move['exclude_from_rev_tab1'],
        #         'move':line_move['move1']
        #         })   
        # self.confirm_sheet()

        
    def compute_deferred(self):
        results =[]
        narr = rev_date = ""
        rev = rev_cum = rev_next = rev_total = rev_cum_total = rev_next_total= 0
        assets = self.env['account.asset'].search([('move_id', '=', self.invoice.id)])
        for ass in assets:
            invoices = self.env['account.move'].search([('asset_id', '=', ass.id)])
            for inv in invoices.sorted(lambda x: x.id):
                rev_ref = inv.ref2
                rev_date = inv.date
                rev = inv.amount_total
                rev_cum = inv.asset_depreciated_value
                rev_next = inv.asset_remaining_value 

                res =({
                    'rev_ref1': rev_ref,
                    'rev_date1': rev_date,
                    'rev1': rev,
                    'rev_cum1': rev_cum,
                    'rev_next1': rev_next,
                    'exclude_from_def_tab1': True,
                    'deferred_report_id1':self.id,
                    'move1': self.invoice.id
                })    
                results.append(res)                                               

        try :
            def key_func(k):
                return k['rev_ref1']
        except ValueError:
            raise ValidationError("Please contact the administrator")
        results = sorted(results, key=key_func)
        for resu, resus in groupby(results, key_func):
            revs=rev_cums=rev_nexts=0
            for line_move in resus:
                revs += line_move['rev1']
                rev_cums += line_move['rev_cum1']
                rev_nexts += line_move['rev_next1']    

            line = self.env['deferred.report.line'].create({
                'revenue_ref': line_move['rev_ref1'], 
                'revenue_date': line_move['rev_date1'],
                'revenue': revs,
                'cumulative_revenue': rev_cums,
                'next_revenue': rev_nexts,
                'exclude_from_def_tab': line_move['exclude_from_def_tab1'],
                'deferred_report_id':line_move['deferred_report_id1'],
                'move': line_move['move1']
                })      
        self.confirm_deferred()

    
    def confirm_sheet(self):
        """
        confirm Deferred report  - confirmed deferred report after computing deferred Lines..
        """
        for deferred in self:
            if not deferred.line_ids:
                raise UserError(_('You can not generate deferred report without deferred lines.'))
            date = fields.Date.from_string(fields.Date.today())
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('deferred.report')   
            deferred.write({
                'number': 'DEFERRED' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })  
            # _logger.info("youpiii")


    def confirm_deferred(self):
        """
        confirm revenue board  - confirmed deferred report after computing revenue board Lines..
        """
        for deferred in self:
            if not deferred.deferred_line_ids:
                raise UserError(_('You can not generate deferred report without revenue board lines.'))
            date = fields.Date.from_string(fields.Date.today())
            advice_year = date.strftime('%m') + '/' + date.strftime('%Y')
            number = self.env['ir.sequence'].next_by_code('revenue.report')   
            deferred.write({
                'number': 'REVENUE' + '/' + advice_year + '/' + number,
                'state': 'confirm',
            })
    
class DeferredReportLine(models.Model):
    '''
    Bank deferred report Lines
    '''
    _name = 'deferred.report.line'
    _description = 'Deferred Report Lines'
    
    deferred_report_id = fields.Many2one('deferred.report', string='Deferred report', ondelete="cascade")
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    partner_id = fields.Many2one('res.partner', string="Name Partner") 
    premium_amount = fields.Float(string='Premium Amount')
    poli_numb = fields.Char(string="Policy Number")
    jan = fields.Float(string='Jan')
    feb = fields.Float(string='Feb')
    mar = fields.Float(string='Mar')
    apr = fields.Float(string='Apr')
    may = fields.Float(string='May')
    jun = fields.Float(string='Jun')
    jul = fields.Float(string='Jul')
    aug = fields.Float(string='Aug')
    sep = fields.Float(string='Sep')
    oct = fields.Float(string='Oct')
    nov = fields.Float(string='Nov')
    dec = fields.Float(string='Dec')
    next_year = fields.Float(string='Next Year')

   
    revenue_ref = fields.Char(string="Number")
    revenue_date = fields.Date(string='Revenue Date')
    revenue = fields.Float(string="Revenue") 
    cumulative_revenue = fields.Float(string='Cumulative Revenue')
    next_revenue = fields.Float(string="Next Period Revenue")

    exclude_from_def_tab = fields.Boolean(help="Technical field used to exclude some lines from the line_ids tab in the form view.")
    exclude_from_rev_tab = fields.Boolean(help="Technical field used to exclude some lines from the deferred_line_ids tab in the form view.")
    move = fields.Many2one('account.move', string='move')


class deferredrepo(models.AbstractModel):
    _name = "report.client_pi.report_deferred"
    _template = 'client_pi.report_deferred'
    _description = "deferred Report"

    def get_total_pa(self):
        return self.total_pa
    def get_total_jan(self):
        return self.total_jan
    def get_total_feb(self):
        return self.total_feb  
    def get_total_mar (self):
        return self.total_mar
    def get_total_apr(self):
        return self.total_apr
    def get_total_may(self):
        return self.total_may 
    def get_total_jun (self):
        return self.total_jun
    def get_total_jul(self):
        return self.total_jul
    def get_total_aug(self):
        return self.total_aug 
    def get_total_sep (self):
        return self.total_sep
    def get_total_oct(self):
        return self.total_oct
    def get_total_nov(self):
        return self.total_nov
    def get_total_dec(self):
        return self.total_dec  
    def get_total_ny(self):
        return self.total_ny                              

    def get_detail(self, line_ids):
        result = []
        self.total_pa = 0.00
        self.total_jan = 0.00
        self.total_feb = 0.00
        self.total_mar = 0.00
        self.total_apr = 0.00
        self.total_may = 0.00
        self.total_jun = 0.00
        self.total_jul = 0.00
        self.total_aug = 0.00
        self.total_sep = 0.00
        self.total_oct = 0.00
        self.total_nov = 0.00
        self.total_dec = 0.00
        self.total_ny= 0.00
        for l in line_ids:
            res = {}
            res.update({  
                    'partner_id': l.partner_id.name,
                    'poli_numb': l.poli_numb,
                    'premium_amount': l.premium_amount, 
                    'start_date': l.start_date, 
                    'end_date': l.end_date,
                    'jan': l.jan,
                    'feb': l.feb,
                    'mar': l.mar,
                    'apr': l.apr,
                    'may': l.may,
                    'jun': l.jun,
                    'jul': l.jul,
                    'aug': l.aug,
                    'sep': l.sep,
                    'oct': l.oct,
                    'nov': l.nov,
                    'dec': l.dec,
                    'next_year': l.next_year
                    })
            self.total_pa += l.premium_amount
            self.total_jan += l.jan
            self.total_feb += l.feb
            self.total_mar += l.mar
            self.total_apr += l.apr
            self.total_may += l.may
            self.total_jun += l.jun
            self.total_jul += l.jul
            self.total_aug += l.aug
            self.total_sep += l.sep
            self.total_oct += l.oct
            self.total_nov += l.nov
            self.total_dec += l.dec
            self.total_ny += l.next_year
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        deferred = self.env['deferred.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'deferred.report',
            'data': data,
            'docs': deferred,
            'time': time,
            'get_detail': self.get_detail,
            'get_total_pa': self.get_total_pa,
            'get_total_jan': self.get_total_jan,
            'get_total_feb': self.get_total_feb,
            'get_total_mar': self.get_total_mar,
            'get_total_apr': self.get_total_apr,
            'get_total_may': self.get_total_may,
            'get_total_jun': self.get_total_jun,
            'get_total_jul': self.get_total_jul,
            'get_total_aug': self.get_total_aug,
            'get_total_sep': self.get_total_sep,
            'get_total_oct': self.get_total_oct,
            'get_total_nov': self.get_total_nov,
            'get_total_dec': self.get_total_dec,
            'get_total_ny': self.get_total_ny,
        }



class deferredrevenue(models.AbstractModel):
    _name = "report.client_pi.report_deferred_revenue"
    _template = 'client_pi.report_deferred_revenue'
    _description = "deferred Report Revenue"

    def get_total_rev(self):
        return self.total_rev
    def get_total_rev_cum(self):
        return self.total_rev_cum
    def get_total_rev_next(self):
        return self.total_rev_next  
                                     

    def get_detail(self, deferred_line_ids):
        result = []
        self.total_rev = 0.00
        self.total_rev_cum = 0.00
        self.total_rev_next = 0.00
        for l in deferred_line_ids:
            res = {}
            res.update({  
                    'revenue_ref': l.revenue_ref,
                    'revenue_date': l.revenue_date,
                    'revenue': l.revenue,
                    'cumulative_revenue': l.cumulative_revenue, 
                    'next_revenue': l.next_revenue, 
                    })
            self.total_rev += l.revenue
            self.total_rev_cum += l.cumulative_revenue
            self.total_rev_next += l.next_revenue
            result.append(res)
        return result

    @api.model
    def _get_report_values(self, docids, data=None):
        deferred_rev = self.env['deferred.report'].browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'deferred.report',
            'data': data,
            'docs': deferred_rev,
            'time': time,
            'get_detail': self.get_detail,
            'get_total_rev': self.get_total_rev,
            'get_total_rev_cum': self.get_total_rev_cum,
            'get_total_rev_next': self.get_total_rev_next,
        }