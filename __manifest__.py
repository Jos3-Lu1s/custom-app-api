{
    'name': "REST API Integration",

    'summary': "REST API personalizada para integraciones externas",

    'description': """
REST API personalizada para integrar aplicaciones externas con Odoo.

Características iniciales:

- Endpoints RESTful.
- Autenticación mediante API Key / Bearer Token.
- Recepción de payloads JSON.
- Mapeo y transformación de datos.
- Creación y actualización de registros.
- Operaciones masivas (Bulk Create).
    """,

    'author': "Tekuno",
    'website': "https://tekuno.mx/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Technical',
    'version': '19.0.1.0.0',
    "license": "LGPL-3",
    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'sale_subscription'],

    # always loaded
    'data': [
        'data/subscritions_products.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
}

