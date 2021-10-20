# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
import json
import requests

class UserSign(models.Model):
    _inherit = ['res.users']

    is_sign = fields.Boolean("Authorize digital signature ? " , default=False, store=True )
    sign = fields.Binary(string="Digital signature", store=True)