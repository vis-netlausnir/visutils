import locale
from copy import deepcopy
from django.conf import settings


def totalize_list(l, *fields, **named):
    '''
    Create and return a list of BaseObject instances where attributes
    have been added that contain the current totals of attributes
    defined in *fields
    Pass parameter inline=False to override the inline functionality
    and create a new deep copy of the first list instance with the
    relevant attributes set to their respective totals
    NOTE: inline declaration does not support sub-notation!
    '''
    def get_sub_notation(obj, field_notation):
        ret = obj
        for f in field_notation.split('.'):
            if hasattr(ret, f):
                ret = getattr(ret, f)
        return ret
    inline = True
    if 'inline' in named.keys():
        inline=named['inline']
    fields = [n for n in fields]
    totals = {}
    for key in fields:
        totals[key] = 0
    for i in l:
        for key in fields:
            totals[key] = totals[key]+get_sub_notation(i, key)
            if inline:
                setattr(i, key.replace('.', '_')+'_total', totals[key])
    if len(l) > 0 and not inline:
        new_val = deepcopy(l[0])
        for key in fields:
            setattr(new_val, key, totals[key])
        l.append(new_val)
    return l

def sub_totalize_list(l, group_field, *fields, **kwargs):
    '''
    Create and return a list of BaseObject instance where attribuets
    have been added that contain the current and group-by totals of
    attributes defined in *fields as grouped-by group_field
    You can pass in fields named 'foo.bar' and there will be totals
    that have the name 'foo_bar_total' on the objects in the list
    '''
    # TODO: this could use a little cleaning
    # do this with kwargs to get argument order right
    reverse = kwargs.get('reverse', False)

    def get_sub_notation(obj, field_notation):
        ret = obj
        for f in field_notation.split('.'):
            if hasattr(ret, f):
                ret = getattr(ret, f)
        return ret
    fields = [f for f in fields]
    current_totals, group_totals, field_total_names, group_total_names, group_counts = dict(), dict(), dict(), dict(), dict()
    group_index_name = 'group_index' #'_'+group_field.replace('.', '_')+'_index'
    group_count_name = 'group_count' #'_'+group_field.replace('.', '_')+'_count'
    group_last_name = 'group_last' #'_'+group_field.replace('.', '_')+'_last'
    group_first_name = 'group_first' #'_'+group_field.replace('.', '_')+'_first'
    group_pleb_name = 'group_pleb' #'_'+group_field.replace('.', '_')+'_pleb'
    group_index, group_count, total_count, total_index = 0, 0, 0 ,0
    for f in fields:
        current_totals[f] = 0
        field_total_names[f] = f.replace('.', '_')+'_total'
        group_totals[f] = 0
        group_total_names[f] = f.replace('.', '_')+'_group_total'
    group_val = None
    l = locale_sorted(l, key=lambda i: get_sub_notation(i, group_field), reverse=reverse)
    for i in l:
        if get_sub_notation(i, group_field) != group_val:
            for f in fields:
                group_totals[f] = 0
            group_val = get_sub_notation(i, group_field)
            group_counts[group_val] = 0
        for f in fields:
            current_totals[f] = current_totals[f] + get_sub_notation(i, f)
            setattr(i, field_total_names[f], current_totals[f])
            group_totals[f] = group_totals[f] + get_sub_notation(i, f)
            setattr(i, group_total_names[f], group_totals[f])
        group_counts[group_val] += 1

    group_val = None
    for i in range(len(l)):
        if get_sub_notation(l[i], group_field) != group_val:
            setattr(l[i], group_first_name, True)
            if i != 0:
                # set for last item in previous group
                setattr(l[i-1], group_last_name, True)
            group_val = get_sub_notation(l[i], group_field)
            group_count = group_counts[group_val]
            group_index = 0
        if i == len(l)-1:
            # last item in list
            setattr(l[i], group_last_name, True)
            setattr(l[i], group_pleb_name, False)
            setattr(l[i], '_last', True)
        setattr(l[i], 'list_index', i)
        setattr(l[i], 'list_count', len(l))
        setattr(l[i], 'list_first', i == 0)
        setattr(l[i], 'list_last', i == len(l)-1)
        setattr(l[i], 'list_pleb', i != len(l)-1 and i != 0)
        setattr(l[i], group_count_name, group_counts[group_val])
        setattr(l[i], group_first_name, group_index == 0)
        setattr(l[i], group_index_name, group_index)
        setattr(l[i], group_pleb_name, group_index != 0 and group_index != group_count-1)
        setattr(l[i], group_last_name, group_index == group_count-1)
        group_index += 1
        total_index += 1
        total_count += 1

    return l

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