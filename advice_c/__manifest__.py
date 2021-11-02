# Copyright 2019 Pether Solutions (http://www.pethersolutions.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# @author Christian Ferdinand Fotie  <christian.ferdinand@pethersolutions.com>

{
    'name': 'Vendor Payment Cheques Advice',
    'version': '1.0',
    'category': 'General',
    'license': 'AGPL-3',
    'website': 'https://www.pethersolutions.com',
    'depends': ['account'],
    'description': """
        Accounting Payment Cheques vendor.
        ============================
            """,

    'data': [
        'views/l10n_in_hr_payroll_view.xml',
        'data/data.xml',
        'views/l10n_in_hr_payroll_report.xml',
        'views/report_payroll_advice_template.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}
