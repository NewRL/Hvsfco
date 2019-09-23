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
    'name': 'Hospital Vaccination Management',
    'summary': 'Hospital Vaccination Management to manage patient Vaccination flow and history',
    'description': """
        This Module will add a Page in Patient for managing Vaccine for Paediatrics in HMS. acs hms
    """,
    'version': '1.0.7',
    'category': 'Hospital Management System',
    'author': 'Almighty Consulting Services',
    'website': 'https://www.almightycs.com',
    'license': 'OPL-1',
    'depends': ['acs_hms'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/acs_hms_views.xml',
        'views/vaccination_view.xml',
        'views/menu_item.xml',
    ], 
    'demo': [
        'demo/vaccine_demo.xml',
    ],
    'images': [
        'static/description/hms_vaccination_almightycs_odoo_cover.jpg',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 30,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
