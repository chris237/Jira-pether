# Copyright 2019 Pether Solutions (http://www.pethersolutions.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# @author Christian Ferdinand Fotie  <christian.ferdinand@pethersolutions.com>

{
    'name': 'Odoo ACCOUNTING PETHER INSURE',
    'version': '1.0',
    'category': 'General',
    'license': 'AGPL-3',
    'description': """
        Customized Quotation, Invoice, Receipt and customer.
        Individual Claims
        Payments Vouchers
    """,
    'summary': 'Adds field Costumer and vendors',
    'author': 'Christian Ferdinand FOTIE,Pether Solutions',
    'website': 'https://www.pethersolutions.com',
    'depends': ['base','contacts','crm','l10n_us_check_printing','sale_management','sale_crm','account_accountant'],
    'data': [
        'views/views.xml',
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/crm_lead_view.xml',
        'views/claim.xml',
        'views/expense.xml',
        'views/move.xml',
        'views/signature.xml',
        'views/payment.xml',
        'views/product.xml',
        'views/sale.xml',
        'views/sale_portal_template.xml',
        # 'views/report.xml',
        #'views/report_financial_cu.xml',
        #'views/rescompanie.xml',
        'views/respartner.xml',
        'views/settings.xml',
        'views/connect.xml',
        'views/tax_report.xml',
        'views/claim_report.xml',
        'views/ledger_report.xml',
        'views/premium_report.xml',
        'views/deferred_report.xml',
        'views/res_policy.xml',
        'views/account_asset.xml',
        'views/account_statement.xml',
        'views/payment_mail_template.xml',
        'views/templates.xml',
        'views/template_tax.xml',
        'views/template_claim.xml',
        'views/template_ledger.xml',
        'views/template_premium.xml',
        'views/template_deferred.xml',
        'views/template_statement.xml',
        'data/ircron1.xml',
        'data/data.xml',
        'data/mail_data.xml',
        'views/individual_claims.xml',
        #'reports/voucher.xml',
        #'reports/advice_vendor.xml',
        'reports/report_journal.xml',
        'reports/report_journal_entry_template.xml',
        'wizard/fetch_claim.xml',
        'views/menu.xml',
        'views/send_notification.xml',
        #'reports/report_voucher_template.xml'
        ],
    # 'qweb': [   
    #     'static/src/xml/tree_view_button.xml'],
    # 'demo': ['demo/partner_demo.xml'],
    'installable': True,
    'application': True,
}

