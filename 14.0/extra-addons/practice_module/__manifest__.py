# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Practic model',
    'version': '1.0',
    'category': 'Tools',
    'summary': "Practice model",
    'description': "Test model for practice",
    'author': 'Vlad',
    'website': "http://www.yourcompany.com",
    'depends': ['base', 'mail', 'account', 'hr'],
    'data': ['security/ir.model.access.csv',
             'views/practice_views.xml'],
    'demo': [],
    'installable': True,
    'application': True,
    'autho_install': False
}
