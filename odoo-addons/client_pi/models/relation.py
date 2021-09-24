# Copyright 2021 Pether Solutions - Christian Ferdinand <christian.ferdinand@pether.io>

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


class RelationPI(models.Model):
    _name = 'res.relation'
    _inherit = ['portal.mixin', 'mail.thread']
    _description = "relation"
    _order = "id desc"
    _rec_name ='name'

    name = fields.Char(string="Relation",  required=True)
    relation_id = fields.Char(string="Relation ID")
    type = fields.Char(string="Type")
    desc = fields.Char(string="Relation Description")



    def fetch_relation(self):
        url = self.env['res.company'].search([('id', '=',1)], limit=1).url_pi        
        connid = self.env['res.company'].search([('id', '=',1)], limit=1).connid
        # url_login to connect to PI
        url_login =url+'/ghi/c/ws/ws-login.php'
        # urlPol for fetch line of policies in PI
        urlPol = url+'/ghi/reg/ws/'
        if connid:
            respol = requests.get(urlPol, params={'op': 'qoreftypes', 'connid':connid})
            datapol = respol.json()
            if datapol["error"]==False :
                pols = datapol["result"]["value"]
                for rel in pols:
                    name = rel['name']
                    relation_id = rel['id']
                    type = rel['type']
                    desc = rel['descr']
                    relatiom = {'name':name, 'relation_id' : relation_id, 'type' : type, 'desc' : desc}
                    rel_id = self.env['res.relation'].search([('relation_id', '=', relation_id)], limit=1) 
                    if rel_id:
                        for one in rel_id:
                            one.name = name
                            one.type = type
                            one.desc = desc
                    else:
                        self.env['res.relation'].create(relatiom)  
