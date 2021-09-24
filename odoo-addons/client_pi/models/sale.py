# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models,_, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import datetime
import time
import odoo.addons.decimal_precision as dp
from datetime import date
import json
import requests
from operator import itemgetter
from itertools import groupby
from json import dumps
from itertools import zip_longest
from hashlib import sha256
from datetime import date, timedelta

from collections import defaultdict
import re
import logging
_logger = logging.getLogger(__name__)

class SalesOrder(models.Model):
    _inherit = "sale.order"

    Pi_from = fields.Boolean(string ="Quotation from PI", default=False)
    nbr = fields.Integer(string='Number of Person Loaded', tracking=True)
    preexisting = fields.Monetary(string='Pre-existing Condition',  tracking=True)
    sign_confi = fields.Binary(string="confirme signature")
    approveiud = fields.Char(string="approver user" , tracking=True)
    sign_approv = fields.Binary(string="approve signature doctor")
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('approve', 'Waiting Approval'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    def send_email_from(self):
        outmails = self.env['ir.mail_server'].search([])
        for outmail in outmails:
            smtpuser = outmail.smtp_user

        return smtpuser 

        
    def action_approve(self):
        self.write({'state': 'sent'})
        self.write({'approveiud': self.env.user.name})
        if self.env.user.is_sign == True:
            self.write({'sign_approv': self.env.user.sign})

        return True    

    def action_quotation_send(self):
        res = super(SalesOrder, self).action_quotation_send()
        self.write({'state': 'sale'})

        return res

    def action_confirm(self):
        discnt = 0.0
        no_line = 0.0
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write({
            'state': 'approve',
            'date_order': fields.Datetime.now(),
            'sign_confi': self.env.user.sign
        })

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)

        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()


        if self.company_id.so_double_validation == 'two_step':
            for line in self.order_line:
                no_line += 1
                discnt += line.discount
            discnt = (discnt / no_line)
            if self.company_id.so_double_validation_limit and discnt > self.company_id.so_double_validation_limit:
                self.state = 'approve'  

        return True


    @api.depends('order_line.price_total','preexisting')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_discount =0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_discount': amount_discount,
                'amount_total': amount_untaxed + amount_tax + order.preexisting,
            })

class SaleOrderLineB(models.Model):
    _inherit = 'sale.order.line'
    
    typ = fields.Selection(selection=[
        ('principal', 'Principal'),
        ('spouses', 'Spouses'),
        ('dep_a', 'Adult Dependant'),
        ('child', 'Child'),
        ('preexising', 'Preexisting')],
        default='principal', string='Type',tracking=True)
    quantity = fields.Integer(
        string='Quantity',
        default=1, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
        "The quantity is not a legal requirement but is very useful for some reports.")
    
    price_unit = fields.Float('Premium per person', required=True, digits='Product Price', default=0.0)
    product_uom_qty = fields.Integer(string='Membership', digits='Product Unit of Measure', required=True, default=1)    
