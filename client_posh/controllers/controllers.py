# -*- coding: utf-8 -*-
# from odoo import http


# class ClientPosh(http.Controller):
#     @http.route('/client_posh/client_posh/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/client_posh/client_posh/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('client_posh.listing', {
#             'root': '/client_posh/client_posh',
#             'objects': http.request.env['client_posh.client_posh'].search([]),
#         })

#     @http.route('/client_posh/client_posh/objects/<model("client_posh.client_posh"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('client_posh.object', {
#             'object': obj
#         })
