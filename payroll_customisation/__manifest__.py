# Copyright 2019 Pether Solutions (http://www.pethersolutions.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# @author Christian Ferdinand Fotie  <christian.ferdinand@pethersolutions.com>

{
    'name': 'Odoo Payroll PETHER INSURE',
    'version': '1.0',
    'category': 'General',
    'license': 'AGPL-3',
    'description': """
        Customized Payslip Report and Email-Payslip
    """,
    'summary': 'to complete',
    'author': 'Christian Ferdinand FOTIE,Pether Solutions',
    'website': 'https://www.pethersolutions.com',
    'company': "Pether Solutions",
    'depends': ['base', 'hr', 'hr_payroll', 'mail','l10n_in_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'security/user_groups.xml',
        'views/payment.xml',
        'wizard/register_payment.xml',
        'views/contribution.xml',
        'views/views.xml',
        'views/send_payslip.xml',
        'views/payslip_mail_template.xml',
        'views/report_payslips_custom.xml',
        'views/template_advice.xml',
        'report/hr_payslip_report.xml',
        'report/templa_contributions.xml',
        'report/payment_voucher.xml',
        'views/report_payroll_summary_template.xml'
        ],
    'qweb': [],
    # 'demo': ['demo/partner_demo.xml'],
    'installable': True,
    'application': True,
}

