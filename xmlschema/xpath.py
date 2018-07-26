# -*- coding: utf-8 -*-
#
# Copyright (c), 2016-2018, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
"""
This module defines a mixin class for enabling XPath on schemas.
"""
from abc import abstractmethod
from collections import Sequence
from elementpath import XPath2Parser, XPathContext


class ElementPathContext(XPathContext):
    """
    XPath dynamic context class for XMLSchema. Implements safe iteration methods for
    schema elements that recognize circular references.
    """
    def _iter_descendants(self):
        def safe_iter_descendants(context):
            elem = context.item
            yield elem
            if elem.text is not None:
                context.item = elem.text
                yield context.item
            if len(elem):
                context.size = len(elem)
                for context.position, context.item in enumerate(elem):
                    if context.item.is_global:
                        for item in safe_iter_descendants(context):
                            yield item
                    elif getattr(context.item, 'ref', None) is not None:
                        yield context.item
                    elif context.item not in local_items:
                        local_items.append(context.item)
                        for item in safe_iter_descendants(context):
                            yield item

        local_items = []
        return safe_iter_descendants(self)

    def _iter_context(self):
        def safe_iter_context(context):
            elem = context.item
            yield elem
            if elem.text is not None:
                context.item = elem.text
                yield context.item

            for item in elem.attrib.items():
                context.item = item
                yield item

            if len(elem):
                context.size = len(elem)
                for context.position, context.item in enumerate(elem):
                    if context.item.is_global:
                        for item in safe_iter_context(context):
                            yield item
                    elif getattr(context.item, 'ref', None) is not None:
                        yield context.item
                    elif context.item not in local_items:
                        local_items.append(context.item)
                        for item in safe_iter_context(context):
                            yield item

        local_items = []
        return safe_iter_context(self)


class ElementPathMixin(Sequence):
    """
    Mixin abstract class for enabling the XPath API on XSD components.
    """
    _attrib = {}
    text = None
    tail = None

    @abstractmethod
    def __iter__(self):
        pass

    def __getitem__(self, i):
        try:
            return [e for e in self][i]
        except AttributeError:
            raise IndexError('child index out of range')

    def __reversed__(self):
        return reversed([e for e in self])

    def __len__(self):
        return len([e for e in self])

    @property
    def tag(self):
        return getattr(self, 'name')

    @property
    def attrib(self):
        return getattr(self, 'attributes', self._attrib)

    def get(self, key, default=None):
        return self.attrib.get(key, default)

    @property
    def xpath_namespaces(self):
        if hasattr(self, 'namespaces'):
            namespaces = {k: v for k, v in self.namespaces.items() if k}
            xpath_default_namespace = getattr(self, 'xpath_default_namespace', None)
            if xpath_default_namespace is not None:
                namespaces[''] = xpath_default_namespace
            return namespaces

    def match(self, tag, default_namespace=None):
        """Matching method for element tag."""
        if tag[0] == '{':
            return self.tag == tag
        elif default_namespace:
            return self.tag in (tag, '{%s}%s' % (default_namespace, tag))

    def iterfind(self, path, namespaces=None):
        """
        Creates and iterator for all XSD subelements matching the path.

        :param path: an XPath expression that considers the XSD component as the root element.
        :param namespaces: is an optional mapping from namespace prefix to full name.
        :return: an iterable yielding all matching XSD subelements in document order.
        """
        if path.startswith('/'):
            path = u'.%s' % path  # Avoid document root positioning
        namespaces = self.xpath_namespaces if namespaces is None else namespaces
        parser = XPath2Parser(namespaces, strict=False)
        root_token = parser.parse(path)
        context = ElementPathContext(self)
        return root_token.select(context)

    def find(self, path, namespaces=None):
        """
        Finds the first XSD subelement matching the path.

        :param path: an XPath expression that considers the XSD component as the root element.
        :param namespaces: an optional mapping from namespace prefix to full name.
        :return: The first matching XSD subelement or ``None`` if there is not match.
        """
        if path.startswith('/'):
            path = u'.%s' % path
        namespaces = self.xpath_namespaces if namespaces is None else namespaces
        parser = XPath2Parser(namespaces, strict=False)
        root_token = parser.parse(path)
        context = ElementPathContext(self)
        return next(root_token.select(context), None)

    def findall(self, path, namespaces=None):
        """
        Finds all XSD subelements matching the path.

        :param path: an XPath expression that considers the XSD component as the root element.
        :param namespaces: an optional mapping from namespace prefix to full name.
        :return: a list containing all matching XSD subelements in document order, an empty \
        list is returned if there is no match.
        """
        if path.startswith('/'):
            path = u'.%s' % path
        namespaces = self.xpath_namespaces if namespaces is None else namespaces
        parser = XPath2Parser(namespaces, strict=False)
        root_token = parser.parse(path)
        context = ElementPathContext(self)
        return root_token.get_results(context)

    def iter(self, tag=None):
        """
        Creates an iterator for the XSD element and its subelements. If tag is not `None` or '*',
        only XSD elements whose matches tag are returned from the iterator. Local elements are
        expanded without repetitions. Element references are not expanded because the global
        elements are not descendants of other elements.
        """
        def safe_iter(elem):
            if tag is None or elem.match(tag):
                yield elem
            for child in elem:
                if child.is_global:
                    for e in safe_iter(child):
                        yield e
                elif getattr(child, 'ref', None) is not None:
                    if tag is None or elem.match(tag):
                        yield child
                elif child not in local_elements:
                    local_elements.append(child)
                    for e in safe_iter(child):
                        yield e

        if tag == '*':
            tag = None
        local_elements = []
        return safe_iter(self)

    def iterchildren(self, tag=None):
        """
        Creates an iterator for the child elements of the XSD component. If *tag* is not `None`
        or '*', only XSD elements whose name matches tag are returned from the iterator.
        """
        if tag == '*':
            tag = None
        for child in self:
            if tag is None or child.match(tag):
                yield child
