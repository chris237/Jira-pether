# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class client_posh(models.Model):
#     _name = 'client_posh.client_posh'
#     _description = 'client_posh.client_posh'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
