# -*- coding: utf-8 -*-
from odoo import http
import odoo


# class ClientCanal2(http.Controller):
#     @http.route('/client_canal_2/client_canal_2/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/client_canal_2/client_canal_2/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('client_canal_2.listing', {
#             'root': '/client_canal_2/client_canal_2',
#             'objects': http.request.env['client_canal_2.client_canal_2'].search([]),
#         })

#     @http.route('/client_canal_2/client_canal_2/objects/<model("client_canal_2.client_canal_2"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('client_canal_2.object', {
#             'object': obj
#         })