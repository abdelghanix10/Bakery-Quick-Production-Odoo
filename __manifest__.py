{
    'name': 'Bakery Quick Production',
    'version': '1.0',
    'category': 'Manufacturing/Bakery',
    'summary': 'Simplified production interface for bakers',
    'description': """
        This module provides a simplified "Kiosk Mode" interface for bakers to register production.
        It includes:
        - A Kanban dashboard filtered for Bakery products.
        - A Wizard to quickly register production quantities.
        - Automatic calculation of ingredients based on BOM.
        - One-click production confirmation and completion.
    """,
    'depends': ['mrp', 'stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/dashboard_action.xml',
        'views/wizard_view.xml',
        'views/bulk_production_view.xml',
        'views/res_users_view.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
