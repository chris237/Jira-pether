# -*- coding: utf-8 -*-
{
    'name': 'Sale Discount on Total Amount',
    'version': '13.0.1.0.1',
    'category': 'Sales Management',
    'summary': "Discount on Total in Sale and Invoice With Discount Limit and Approval",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'http://www.cybrosys.com',
    'description': """

Sale Discount for Total Amount
=======================
Module to manage discount on total amount in Sale.
        as an specific amount or percentage
""",
    'depends': [
                'account', 'sale', 'client_pi'
                ],
    'data': [
        'views/sale_view.xml',
        'views/account_invoice_view.xml',
        'views/invoice_report.xml',
        'views/ks_account_account.xml',
        'views/assets.xml',
        # 'views/sale_order_report.xml',
        #'views/res_config_view.xml',

    ],
    'demo': [
    ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}
