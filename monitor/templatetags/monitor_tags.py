from django import template

register = template.Library()

STORE_SLUGS = {
    'Citilink':  'citilink',
    'DNS':       'dns',
    'М.Видео':   'mvideo',
    'Эльдорадо': 'eldorado',
}

@register.filter
def dict_get(d, key):
    if isinstance(d, dict):
        return d.get(key)
    return None

@register.filter
def store_slug(store_name):
    return STORE_SLUGS.get(store_name, 'unknown')
