{
    'name': 'Custom Search Folder',
    'version': '1.0',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/custom_search_folder_views.xml',
    ],
    'installable': True,
    'application': True,
}
