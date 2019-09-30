# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════╗
#║                                                                  ║
#║                ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                 ║
#║                ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                 ║
#║                ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                 ║
#║                ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                 ║
#║                ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                 ║
#║                ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                 ║
#║                          ╔═╝║     ╔═╝║                           ║
#║                          ╚══╝     ╚══╝                           ║
#║ SOFTWARE DEVELOPED AND SUPPORTED BY ALMIGHTY CONSULTING SERVICES ║
#║                   COPYRIGHT (C) 2016 - TODAY                     ║
#║                   http://www.almightycs.com                      ║
#║                                                                  ║
#╚══════════════════════════════════════════════════════════════════╝
{
    'name': 'Facility Management System',
    'category': 'Extra Tools',
    'version': '1.0.3',
    'author' : 'Almighty Consulting Services',
    'support': 'info@almightycs.com',
    'website': 'https://www.almightycs.com',
    'license': 'OPL-1',
    'summary': """Application to manage Facility of office or premises in odoo""",
    'description': """Application to manage Facility of office or premises in odoo.
    Facility Management Cleaning of office Cleaning management Office Cleaning
    Maintenance Register Cleaning Register Premises Cleaning Activity Register acs hms hopital management system medical
    """,
    'depends': ["base","mail"],
    'data' : [
        'security/facility_security.xml',
        'security/ir.model.access.csv',
        'views/facility_management_view.xml',
        'data/data.xml',
    ],
    'images': [
        'static/description/facility_cover_almightycs.jpg',
    ],
    'installable': True,
    'auto_install': False,
    'price': 35,
    'currency': 'EUR',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
