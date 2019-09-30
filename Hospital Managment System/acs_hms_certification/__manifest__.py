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
    'name': 'Certificate Management System',
    'summary': """This Module will Add functionality to provide certificate to Patients. Maintain history of certificate allocation.""",
    'description': """
        This Module will Add functionality to provide certificate to Patients. Maintain history of certificate allocation.
        Certification hospital certificate medical certificate patient certification ACS HMS
    """,
    'version': '1.0.5',
    'category': 'Hospital Management System',
    'author': 'Almighty Consulting Services',
    'support': 'info@almightycs.com',
    'website': 'https://www.almightycs.com',
    'license': 'OPL-1',
    'depends': ["acs_hms"],
    'data' : [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/certificate_management_view.xml',
        'report/certificate_report.xml',
    ],
    'images': [
        'static/description/hms_certificate_almightycs_cover.jpg',
    ],
    'installable': True,
    'application': True,
    'sequence': 2,
    'price': 35,
    'currency': 'EUR',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: