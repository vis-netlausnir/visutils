import re
import decimal
import datetime
_SEQ_TYPES = [type(t()) for t in [dict, list]]

class DataAttributeMissing(AttributeError):
    pass

def strip_empty_xmlns(tree):
    '''
    Strips out empty xmlns tags
    '''
    if isinstance(tree, dict):
        marked = []
        for key in tree.keys():
            if isinstance(tree[key], dict) or isinstance(tree[key], list):
                tree[key] = strip_empty_xmlns(tree[key])
            elif tree[key] is None:
                tree.pop(key)
            elif key == 'xmlns' and len(tree[key]) == 0:
                tree.pop(key)
        for key in marked:
            del tree[key]
    if isinstance(tree, list):
        for i in range(len(tree)):
            if isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = strip_empty_xmlns(tree[i])
    return tree

def strip_xmlns(tree):
    '''
    Strips out empty xmlns tags
    '''
    if isinstance(tree, dict):
        marked = []
        for key in tree.keys():
            if isinstance(tree[key], dict) or isinstance(tree[key], list):
                tree[key] = strip_xmlns(tree[key])
            elif tree[key] is None:
                tree.pop(key)
            elif key == 'xmlns':
                tree.pop(key)
        for key in marked:
            del tree[key]
    if isinstance(tree, list):
        for i in range(len(tree)):
            if isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = strip_xmlns(tree[i])
    return tree

def collapse_singleton_dict_strings(tree):
    '''
    Checks for lists in the tree that contain single items and collapses
    them if the value of the pair is a string or unicode
    '''
    if isinstance(tree, dict):
        for key in tree.keys():
            if isinstance(tree[key], dict) and len(tree[key]) == 1:
                for _key in tree[key].keys():
                    if isinstance(tree[key][_key], str) or isinstance(tree[key][_key], unicode):
                        tree[key] = tree[key][_key]
            if isinstance(tree[key], dict) or isinstance(tree[key], list):
                tree[key] = collapse_singleton_dict_strings(tree[key])
    elif isinstance(tree, list) and len(tree) > 0:
        for i in range(len(tree)):
            if isinstance(tree[i], dict) and len(tree[i]) == 1:
                for _key in tree[i].keys():
                    if isinstance(tree[i][_key], str) or isinstance(tree[i][_key], unicode):
                        tree[i] = unicode(tree[i][_key])
            if isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = collapse_singleton_dict_strings(tree[i])
    return tree

def collapse_singleton_list_strings(tree):
    '''
    Checks for lists in the tree that contain single items and collapses
    them into a regular scalar value
    '''
    if isinstance(tree, dict):
        for key in tree.keys():
            if isinstance(tree[key], list) and len(tree[key]) == 1:
                tree[key] = tree[key][0]
            elif isinstance(tree[key], dict) or isinstance(tree[key], list):
                tree[key] = collapse_singleton_list_strings(tree[key])
    if isinstance(tree, list):
        for i in range(len(tree)):
            if isinstance(tree[i], list) and len(tree[i]) == 1:
                tree[i] = tree[i][0]
            elif isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = collapse_singleton_list_strings(tree[i])
    return tree

def convert_empty_dict_to_string(tree):
    '''
    Checks for dicts in the dataset that are empty and converts them
    to empty string values in their parent dict under the same key
    '''
    if isinstance(tree, dict):
        for key in tree.keys():
            if isinstance(tree[key], dict) and len(tree[key]) == 0:
                tree[key] = ''
            elif isinstance(tree[key], dict) or isinstance(tree[key], list):
                tree[key] = convert_empty_dict_to_string(tree[key])
    if isinstance(tree, list):
        for i in range(len(tree)):
            if isinstance(tree[i], dict) and len(tree[i]) == 0:
                tree[i] = ''
            elif isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = convert_empty_dict_to_string(tree[i])
    return tree


def _parse_native_type(obj, types=list(), function=None):
    if function is not None:
        return function(obj)
    for t in types:
        try:
            if t.__name__ == 'datetime':
                try:
                    return datetime.datetime.strptime(str(obj), "%d.%m.%Y %H:%M")
                except:
                    try:
                        return datetime.datetime.strptime(str(obj), "%d.%m.%Y")
                    except:
                        continue
            return t(obj)
        except:
            continue
    return obj

def parse_native_types(tree, types=list(), functions=dict()):
    '''
    Checks if string values can be converted to native types and does so.
    If types is empty, the method defaults to
    [str, long, int, decimal.Decimal, datetime.datetime] (in that order)
    Decimal is used in preference to float as it is a precise value as
    opposed to binary floating points.
    If values test as strings, the datetime parsing is attempted.
    Forced parsing of a specific type can be attempted by passing only
    that type. Note however that this might not be safe and probably
    better attempted with the native parser of that type.
    '''
    if not len(types):
        types = [long, int, decimal.Decimal, datetime.datetime]
    if isinstance(tree, dict):
        for key in tree.keys():

            if key in ('ssid','@ssid','Persidno','id','policyNumber','ownerSSN'): continue
            if type(tree[key]) in _SEQ_TYPES:
                parse_native_types(tree[key], types=types, functions=functions)
            elif key in functions.keys():
                tree[key] = _parse_native_type(tree[key], function=functions[key])
            else:
                tree[key] = _parse_native_type(tree[key], types=types)

    elif isinstance(tree, list):
        for i in range(len(tree)):
            if type(tree[i]) in _SEQ_TYPES:
                parse_native_types(tree[i], types=types, functions=functions)
            else:
                tree[i] = _parse_native_type(tree[i], types=types)
    return tree


def embed_hash_tags(tree):
    '''
    Checks if dict keys start with '#' and changes it to lstrip('#')
    If there is another key with the same name (without the '#') no
    action is taken.
    '''
    if isinstance(tree, dict):
        marked = []
        for key in tree.keys():
            _key = unicode(key).lstrip('#')
            if unicode(key).startswith('#') and _key not in tree.keys():
                tree[_key] = tree[key]
                marked.append(key)
            if isinstance(tree[_key], dict) or isinstance(tree[_key], list):
                tree[_key] = embed_hash_tags(tree[_key])
        for key in marked:
            del tree[key]
    elif isinstance(tree, list):
        for i in range(len(tree)):
            if isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = embed_hash_tags(tree[i])
    return tree

def embed_at_tags(tree):
    '''
    Checks if dict keys start with '@' and changes it to lstrip('@')
    If there is another key with the same name (without the '@') no
    action is taken.
    '''
    if isinstance(tree, dict):
        marked = []
        for key in tree.keys():
            _key = unicode(key).lstrip('@')
            if unicode(key).startswith('@') and _key not in tree.keys():
                tree[_key] = tree[key]
                marked.append(key)
            if isinstance(tree[_key], dict) or isinstance(tree[_key], list):
                embed_at_tags(tree[_key])
        for key in marked:
            del tree[key]
    elif isinstance(tree, list):
        for i in range(len(tree)):
            if isinstance(tree[i], dict) or isinstance(tree[i], list):
                tree[i] = embed_at_tags(tree[i])
    return tree

_non_id_char = re.compile('[^_0-9a-zA-Z]')
class _SafeObject(object):
    def __init__(self):
        pass
    def __unicode__(self):
        return None
    def __str__(self):
        return None
    def __getattr__(self, item):
        try:
            return object.__getattribute__(self, item)
        except:
            return _SafeObject()


class BaseObject(object):
    def __getattribute__(self, item):
        return object.__getattribute__(self, item)

    def __getattr__(self, item):
        if item in self.__dict__.keys():
            return object.__getattribute__(self, item)
        else:
            concat_keys = lambda sep, keys: sep.join(key for key in keys)
            raise DataAttributeMissing(
                    "Attribute {key} does not exist. Possible choices are: {keys}".format(key=item,
                                                                                          keys=concat_keys(', ',
                                                                                                           self.__dict__.keys()))
            )

    def __setattr__(self, item, value):
        item = _non_id_char.sub('', item)
        object.__setattr__(self, item, value)

    def __unicode__(self):
        if hasattr(self, 'text') and type(getattr(self, 'text')) in [type(t()) for t in [str, unicode]]:
            return getattr(self, 'text')
        elif hasattr(self, 'Text') and type(getattr(self, 'Text')) in [type(t()) for t in [str, unicode]]:
            return getattr(self, 'Text')
        return self.__class__.__name__

    def __str__(self):
        if hasattr(self, 'text') and type(getattr(self, 'text')) in [type(t()) for t in [str, unicode]]:
            return getattr(self, 'text')
        elif hasattr(self, 'Text') and type(getattr(self, 'Text')) in [type(t()) for t in [str, unicode]]:
            return getattr(self, 'Text')
        return self.__class__.__name__

    def _name_mangle(self, name):
        return _non_id_char.sub('', name)

    def __repr__(self):
        fields_string = ", ".join(sorted(self.__dict__.keys()))
        return u"<BaseObject: {fields}>".format(fields=fields_string)

def objectify_tree(tree, collations=dict(), parent=''):
    '''
    Takes a dict and makes an object from it. Note that if this is called
    as a prettifier, it will not return a dict.
    If parent is set keys in the collations dict can be of the form 'parent.child'
    and the collations matcher will include the term in searches.
    '''
    ret = BaseObject()
    if isinstance(tree, dict):
        for key in tree.keys():
            if key in collations.keys() or parent+'.'+key in collations.keys():
                colKey = key
                if parent+'.'+key in collations.keys():
                    colKey = parent+'.'+key
                if not hasattr(ret, collations[colKey]):
                    setattr(ret, collations[colKey], list())
                if isinstance(tree[key], dict):
                    getattr(ret, collations[colKey]).append(objectify_tree(tree[key], collations=collations, parent=key))
                elif isinstance(tree[key], list):
                    for item in tree[key]:
                        if isinstance(item, list) or isinstance(item, dict):
                            getattr(ret, collations[colKey]).append(
                                    objectify_tree(item, collations=collations, parent=key)
                            )
                        else:
                            getattr(ret, collations[colKey]).append(item)
                else:
                    setattr(ret, collations[colKey], [tree[key]])
            else:
                if isinstance(tree[key], dict):
                    setattr(ret, key, objectify_tree(tree[key], collations=collations, parent=key))
                elif isinstance(tree[key], list):
                    setattr(ret, key, list())
                    for item in tree[key]:
                        if isinstance(item, list) or isinstance(item, dict):
                            getattr(ret, key).append(objectify_tree(item, collations=collations, parent=key))
                        else:
                            getattr(ret, key).append(item)
                else:
                    setattr(ret, key, tree[key])
    return ret
