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

class ResConfigSettingscheque(models.TransientModel):
    _inherit = 'res.config.settings' 

    country_code = fields.Char(string="Company Country code", related='company_id.country_id.code', readonly=True)
    account_check_printing_layout = fields.Selection(related='company_id.account_check_printing_layout', string="Cheque Layout", readonly=False,
        help="Select the format corresponding to the cheque paper you will be printing your cheques on.\n"
             "In order to disable the printing feature, select 'None'.")
    account_check_printing_date_label = fields.Boolean(related='company_id.account_check_printing_date_label', string="Print Date Label", readonly=False,
        help="This option allows you to print the date label on the cheque as per CPA. Disable this if your pre-printed cheque includes the date label.")
    account_check_printing_multi_stub = fields.Boolean(related='company_id.account_check_printing_multi_stub', string='Multi-Pages Cheque Stub', readonly=False,
        help="This option allows you to print cheque details (stub) on multiple pages if they don't fit on a single page.")
    account_check_printing_margin_top = fields.Float(related='company_id.account_check_printing_margin_top', string='Cheque Top Margin', readonly=False,
        help="Adjust the margins of generated cheques to make it fit your printer's settings.")
    account_check_printing_margin_left = fields.Float(related='company_id.account_check_printing_margin_left', string='Cheque Left Margin', readonly=False,
        help="Adjust the margins of generated cheques to make it fit your printer's settings.")
    account_check_printing_margin_right = fields.Float(related='company_id.account_check_printing_margin_right', string='Cheque Right Margin', readonly=False,
        help="Adjust the margins of generated cheques to make it fit your printer's settings.")
