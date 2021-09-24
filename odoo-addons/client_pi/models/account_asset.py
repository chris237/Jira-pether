# Copyright 2020 Pether Solutions - Christian Ferdinand <christina.ferdinand@pethersolutions.com>

from odoo import api, fields, models,_, _lt
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, float_round, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from dateutil.relativedelta import relativedelta
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
from datetime import date, timedelta

from collections import defaultdict
import re
import logging
_logger = logging.getLogger(__name__)


class AccountAssetA(models.Model):
    _inherit = "account.asset"

    move_id = fields.Many2one('account.move', readonly=True, string="Move")
    partner_id = fields.Many2one('res.partner', readonly=True, string="Partner")
    start_date_pi = fields.Date(readonly=True, states={'draft': [('readonly', False)]}, string='Start Date')

    @api.depends('original_move_line_ids', 'original_move_line_ids.account_id', 'asset_type')
    def _compute_value(self):
        res = super(AccountAssetA, self)._compute_value()

        for record in self:
            for line in record.original_move_line_ids:
                record.move_id = line.move_id 
                record.partner_id = line.move_id.partner_id

                record.start_date_pi = self.env['res.policy'].search([('partner_id', '=', line.move_id.partner_id.id)], limit=1).startDate


    @api.onchange('start_date_pi')
    def _onchange_method_period(self):
        self.first_depreciation_date = self.start_date_pi



    def _recompute_board(self, depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date, already_depreciated_amount, amount_change_ids):
        self.ensure_one()
        residual_amount = amount_to_depreciate
        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        move_vals = []
        prorata = self.prorata and not self.env.context.get("ignore_prorata")
        if amount_to_depreciate != 0.0:
            for asset_sequence in range(starting_sequence + 1, depreciation_number + 1):
                while amount_change_ids and amount_change_ids[0].date <= depreciation_date:
                    residual_amount -= amount_change_ids[0].amount_total
                    amount_to_depreciate -= amount_change_ids[0].amount_total
                    already_depreciated_amount += amount_change_ids[0].amount_total
                    amount_change_ids[0].write({
                        'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                        'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                    })
                    amount_change_ids -= amount_change_ids[0]
                amount = self._compute_board_amount(asset_sequence, residual_amount, amount_to_depreciate, depreciation_number, starting_sequence, depreciation_date)
                prorata_factor = 1
                move_ref = self.name + ' (%s/%s)' % (prorata and asset_sequence - 1 or asset_sequence, self.method_number)
                move_ref1 = '%s' % (prorata and asset_sequence - 1 or asset_sequence)
                if prorata and asset_sequence == 1:
                    move_ref = self.name + ' ' + _('(prorata entry)')
                    move_ref1 = 0
                    first_date = self.prorata_date
                    if int(self.method_period) % 12 != 0:
                        month_days = calendar.monthrange(first_date.year, first_date.month)[1]
                        days = month_days - first_date.day + 1
                        prorata_factor = days / month_days
                    else:
                        total_days = (depreciation_date.year % 4) and 365 or 366
                        days = (self.company_id.compute_fiscalyear_dates(first_date)['date_to'] - first_date).days + 1
                        prorata_factor = days / total_days
                amount = self.currency_id.round(amount * prorata_factor)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount

                move_vals.append(self.env['account.move']._prepare_move_for_asset_depreciation({
                    'amount': amount,
                    'asset_id': self,
                    'move_ref': move_ref,
                    'move_ref1': move_ref1,
                    'date': depreciation_date,
                    'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                    'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                }))

                depreciation_date = depreciation_date + relativedelta(months=+int(self.method_period))
                # datetime doesn't take into account that the number of days is not the same for each month
                if (not self.prorata or self.env.context.get("ignore_prorata")) and int(self.method_period) % 12 != 0:
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)
        return move_vals    