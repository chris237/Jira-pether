# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

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



class AccountSendNotif(models.Model):
    '''
    Account Send Notification
    '''
    _name = 'account.send.notif'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "Send Notfication"
    _order = "id desc, date desc"

    def _get_default_date(self):
        return fields.Date.from_string(fields.Date.today())
    
    date = fields.Date(readonly=True , index=True, tracking=True, required=True, string='Date', default=_get_default_date)   
    accountant = fields.Many2one('res.users', string='Accountant',required=True)
    auditor = fields.Many2one('res.users', string='Auditor',required=True)
    ceo = fields.Many2one('res.users', string='CEO',required=True)
    cfo = fields.Many2one('res.users', string='CFO',required=True)
    finance_officer = fields.Many2one('res.users', string='Finance Officer',required=True)
    accountant_exp = fields.Many2one('res.users', string='Accountant Expense')
 