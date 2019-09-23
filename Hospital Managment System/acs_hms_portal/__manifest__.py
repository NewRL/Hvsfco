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
    'name' : 'Hospital Patient Portal Management',
    'summary' : 'This Module Adds Hospital Portal facility for Patients to allow access to their appointments and prescriptions',
    'description' : """
    This Module Adds Hospital Portal facility for Patients to allow access to their appointments and prescriptions
    HMS Website Portal acs hms hospital management system medical
    """,
    'version': '1.0.6',
    'category': 'Hospital Management System',
    'author': 'Almighty Consulting Services',
    'website': 'https://www.almightycs.com',
    'license': 'OPL-1',
    'depends' : ['portal','acs_hms'],
    'data' : [
        'security/ir.model.access.csv',
        'views/template.xml',
        'views/hms_view.xml',
    ],
    'images': [
        'static/description/hms_portal_almightycs_odoo_cover.jpg',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 30,
    'currency': 'EUR',
}
