# encoding=utf-8
import locale
from django.conf import settings

def sort_list(l, *fields, **kwargs):
    '''
    Creates and sorts a list from the given l by the fields given in
    *fields IN REVERSE ORDER
    Pass reverse=True to reverse the sort itself ;)
    You can pass in field names like 'foo.bar' and the method will
    search for and sort by the sub-value
    '''
    reverse = False
    if 'reverse' in kwargs.keys():
        reverse = kwargs['reverse']
    def get_sub_notation(obj, field_notation):
        ret = obj
        for f in field_notation.split('.'):
            if hasattr(ret, f):
                ret = getattr(ret, f)
        return ret
    for f in reversed([f for f in fields]):
        l = locale_sorted(l, key=lambda i: get_sub_notation(i, f), reverse=reverse)
    return l

def subnotation_sort_list(l, *fields, **kwargs):
    reverse = False
    if 'reverse' in kwargs.keys():
        reverse = kwargs['reverse']
    def get_sub_notation(obj, field_notation):
        ret = obj
        for f in field_notation.split('.'):
            if hasattr(ret, f):
                ret = getattr(ret, f)
        return ret
    for f in reversed([f for f in fields]):
        l = locale_sorted(l, key=lambda i: get_sub_notation(i, f), reverse=reverse)
    return l


locale.setlocale(locale.LC_ALL, settings.SORTING_LOCALE)

class SortingTypeMismatchError(Exception):
    pass

def safe_collate(object1, object2):
    """
    A comparison function that uses locale string collation to sort strings,
    and assumes that None values are strings, but otherwise uses `cmp`.
    """
    if object1 is None:
        object1 = ''
    if object2 is None:
        object2 = ''
    if isinstance(object1, basestring) and isinstance(object2, basestring):
        return locale.strcoll(object1, object2)
    else:
        return cmp(object1, object2)

def locale_sorted(iterable, key=None, reverse=False):
    return sorted(iterable, cmp=safe_collate, key=key, reverse=reverse)