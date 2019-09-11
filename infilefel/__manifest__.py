# -*- coding: utf-8 -*-
{
    'name': "InFile FEL",
    'summary': """
        Generación de Factura Electrónica en Línea (FEL) de InFile
    """,
    'description': """
        Conexión a servicios de InFile para generación de Factura Electrónica en Línea (FEL)
    """,
    'author': "acentoNET",
    'website': "http://www.acentoNET.com",
    'category': 'Sales',
    'sequence': 20,
    'version': '0.1',
    'depends': ['account'],
    'data': [
        "security/ir.model.access.csv",
        'views/infilefel_settings.xml',
        'views/account_tax.xml',
        'views/account_journal.xml',
        'views/account_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}