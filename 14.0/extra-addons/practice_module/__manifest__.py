# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Practic model',
    'version': '1.0',
    'category': 'Sales',
    'description': "Test model for practice",
    'author': 'Vlad',
    'depends': ['base', 'mail'],
    'data': ['security/ir.model.access.csv',
             'views/practice_views.xml'],
    'demo': [],
    'installable': True,
    'application': True,
    'autho_install': False
}
