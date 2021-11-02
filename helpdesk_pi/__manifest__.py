# Copyright 2019 Pether Solutions (http://www.pethersolutions.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# @author Christian Ferdinand Fotie  <christian.ferdinand@pethersolutions.com>

{
    'name': 'Odoo HelpDesk PETHER INSURE',
    'version': '1.0',
    'category': 'General',
    'license': 'AGPL-3',
    'description': """
        Customized Ticket and Report Ticket.
    """,
    'summary': 'Adds field Costumer, Date of complaint, Name of complainant, Policy number, Details of the complaint, How it was resolved, When it was resolved',
    'author': 'Christian Ferdinand FOTIE,Pether Solutions',
    'website': 'https://www.pethersolutions.com',
    'depends': ['helpdesk'],
    'data': [
        'views/views.xml',
        'data/ircron2.xml',
        'data/mail_data.xml'
        ],
    'qweb': [],
    # 'demo': ['demo/partner_demo.xml'],
    'installable': True,
    'application': True,
}

