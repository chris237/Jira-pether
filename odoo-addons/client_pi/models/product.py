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
from itertools import groupby
from json import dumps
from itertools import zip_longest
from hashlib import sha256
from datetime import date, timedelta

from collections import defaultdict
import re

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class ProductTemp(models.Model):
    _inherit = 'product.template'   
    
    idprod = fields.Integer("id product PI")
    idpack = fields.Integer("id package PI")
    supplier_taxes_id1 = fields.Many2one('account.tax', string='Vendor Taxes(Withholding)', help='Withholding taxes used when buying the product.',
        domain=[('type_tax_use', '=', 'purchase')])   
    # debit = fields.Monetary(string='Debit', default=0.0)
    # credit = fields.Monetary(string='Credit', default=0.0)    
    #supplier_untaxes_id = fields.Many2many('account.tax', 'prod_id', 'tax_id', string='Withholding Taxes', help='Default taxes used when buying the product.', domain=[('type_tax_use', '=', 'purchase')])