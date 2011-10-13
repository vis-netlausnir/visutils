# encoding=utf-8
import re
from lxml import objectify, etree
import xml.sax.handler
from xml.dom import minidom as dom
import json as simplejson
_non_id_char = re.compile('[^_0-9a-zA-Z]')
import collections


def xml2obj(src):
    """
    A simple function to converts XML data into native Python object.
    """

    non_id_char = re.compile('[^_0-9a-zA-Z]')
    def _name_mangle(name):
        return non_id_char.sub('_', name)

    class DataNode(object):
        def __init__(self):
            self._attrs = {}    # XML attributes and child elements
            self.data = None    # child text data
        def __len__(self):
            # treat single element as a list of 1
            return 1
        def __getitem__(self, key):
            if isinstance(key, basestring):
                return self._attrs.get(key,None)
            else:
                return [self][key]
        def __contains__(self, name):
            return self._attrs.has_key(name)
        def __nonzero__(self):
            return bool(self._attrs or self.data)
        def __getattr__(self, name):
            if name.startswith('__'):
                # need to do this for Python special methods???
                raise AttributeError(name)
            return self._attrs.get(name,None)
        def _add_xml_attr(self, name, value):
            if name in self._attrs:
                # multiple attribute of the same name are represented by a list
                children = self._attrs[name]
                if not isinstance(children, list):
                    children = [children]
                    self._attrs[name] = children
                children.append(value)
            else:
                self._attrs[name] = value
        def __str__(self):
            return self.data or ''
        def __repr__(self):
            items = sorted(self._attrs.items())
            if self.data:
                items.append(('data', self.data))
            return u'{%s}' % ', '.join([u'%s:%s' % (k,repr(v)) for k,v in items])

    class TreeBuilder(xml.sax.handler.ContentHandler):
        def __init__(self):
            self.stack = []
            self.root = DataNode()
            self.current = self.root
            self.text_parts = []
        def startElement(self, name, attrs):
            self.stack.append((self.current, self.text_parts))
            self.current = DataNode()
            self.text_parts = []
            # xml attributes --> python attributes
            for k, v in attrs.items():
                self.current._add_xml_attr(_name_mangle(k), v)
        def endElement(self, name):
            text = ''.join(self.text_parts).strip()
            if text:
                self.current.data = text
            if self.current._attrs:
                obj = self.current
            else:
                # a text only node is simply represented by the string
                obj = text or ''
            self.current, self.text_parts = self.stack.pop()
            self.current._add_xml_attr(_name_mangle(name), obj)
        def characters(self, content):
            self.text_parts.append(content)

    builder = TreeBuilder()
    if isinstance(src,basestring):
        xml.sax.parseString(src, builder)
    else:
        xml.sax.parse(src, builder)
    return builder.root._attrs.values()[0]

def xml2json(src, prettifiers=[]):
    enc = simplejson.JSONEncoder()
    return enc.encode(xml2struct(src, prettifiers))

def xml2struct(src, prettifiers=[], ignore=list()):
    non_id_char = re.compile('[^_0-9a-zA-Z]')
    def _name_mangle(name):
        return unicode(non_id_char.sub('', name))
    def traverse(node, d, indents = ''):
        c = dict()
        name = _name_mangle(node.nodeName)
        if node.nodeType == node.TEXT_NODE or node.nodeType == node.ELEMENT_NODE:
            if node.nodeType == node.TEXT_NODE:
                d['#'+name] = node.data
            elif node.nodeType == node.ELEMENT_NODE:
                for key in node.attributes.keys():
                    if key in ignore:
                        continue
                    c['@'+key] = node.attributes[key].value
                for child in node.childNodes:
                    if child.nodeName in ignore:
                        continue
                    traverse(child, c, indents+'\t')
            if name in d.keys():
                if isinstance(d[name], list):
                    d[name].append(c)
                else:
                    old = d[name]
                    d[name] = [old, c]
            elif node.nodeType == node.ELEMENT_NODE:
                d[name] = c
    ret = dict()
    if isinstance(src, unicode):
        src = src.encode("utf-8", "ignore")
    xml = dom.parseString(src)
    for node in xml.childNodes:
        traverse(node, ret)
    for prettifier in prettifiers:
        ret = prettifier(ret)
    return ret

def dict_to_etree_element(parent_name, dictionary):
    """
    Returns an ``lxml.etree`` element from a dictionary.  Such elements can
    easily be injected into other groups of elements or converted to an XML
    string.  No annotations or namespaces are used for elements.

    >>> element = dict_to_etree_element('employee', {'name': 'John', 'age': 32})
    >>> print(etree.tostring(element, pretty_print=True))
    <employee>
      <age>32</age>
      <name>John</name>
    </employee>

    If order is important, using SortedDict is acceptable and encouraged.

    This function currently only takes simple directories and handles a depth
    of one.
    """
    root = objectify.Element(parent_name)
    for key, value in dictionary.items():
        setattr(root, key, value)
    objectify.deannotate(root)
    etree.cleanup_namespaces(root)
    return root


def merge(a, b): # source: http://appdelegateinc.com/blog/2011/01/12/merge-deeply-nested-dicts-in-python/
    """Merge two deep dicts non-destructively

    Uses a stack to avoid maximum recursion depth exceptions

    >>> a = {'a': 1, 'b': {1: 1, 2: 2}, 'd': 6}
    >>> b = {'c': 3, 'b': {2: 7}, 'd': {'z': [1, 2, 3]}}
    >>> c = merge(a, b)
    >>> from pprint import pprint; pprint(c)
    {'a': 1, 'b': {1: 1, 2: 7}, 'c': 3, 'd': {'z': [1, 2, 3]}}
    """
    assert quacks_like_dict(a), quacks_like_dict(b)
    dst = a.copy()

    stack = [(dst, b)]
    while stack:
        current_dst, current_src = stack.pop()
        for key in current_src:
            if key not in current_dst:
                current_dst[key] = current_src[key]
            else:
                if quacks_like_dict(current_src[key])\
                and quacks_like_dict(current_dst[key]):
                    stack.append((current_dst[key], current_src[key]))
                else:
                    current_dst[key] = current_src[key]
    return dst

def quacks_like_dict(object):
    """Check if object is dict-like"""
    return isinstance(object, collections.Mapping)
