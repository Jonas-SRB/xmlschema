#!/usr/bin/env python
#
# Copyright (c), 2018-2020, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
import unittest
import os
import platform
from xml.etree import ElementTree
import lxml.etree

from xmlschema import etree

TEST_CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_cases/')


def casepath(relative_path):
    return os.path.join(TEST_CASES_DIR, relative_path)


class TestElementTree(unittest.TestCase):

    def test_imported_element_tree(self):
        self.assertIs(ElementTree, etree.ElementTree)

    def test_element_string_serialization(self):
        self.assertRaises(TypeError, etree.etree_tostring, '<element/>')

        elem = ElementTree.Element('element')
        self.assertEqual(etree.etree_tostring(elem), '<element />')
        elem = etree.ElementTree.Element('element')
        self.assertEqual(etree.etree_tostring(elem), '<element />')
        elem = etree.PyElementTree.Element('element')
        self.assertEqual(etree.etree_tostring(elem), '<element />')

        self.assertEqual(etree.etree_tostring(elem, encoding='us-ascii'), b'<element />')

    def test_defuse_xml_entities(self):
        xml_file = casepath('resources/with_entity.xml')

        elem = etree.ElementTree.parse(xml_file).getroot()
        self.assertEqual(elem.text, 'abc')

        parser = etree.SafeXMLParser(target=etree.PyElementTree.TreeBuilder())
        with self.assertRaises(etree.PyElementTree.ParseError) as ctx:
            etree.ElementTree.parse(xml_file, parser=parser)
        self.assertEqual("Entities are forbidden (entity_name='e')", str(ctx.exception))

    def test_defuse_xml_external_entities(self):
        xml_file = casepath('resources/external_entity.xml')

        with self.assertRaises(etree.ParseError) as ctx:
            etree.ElementTree.parse(xml_file)
        self.assertIn("undefined entity &ee", str(ctx.exception))

        parser = etree.SafeXMLParser(target=etree.PyElementTree.TreeBuilder())
        with self.assertRaises(etree.PyElementTree.ParseError) as ctx:
            etree.ElementTree.parse(xml_file, parser=parser)
        self.assertEqual("Entities are forbidden (entity_name='ee')", str(ctx.exception))

    def test_defuse_xml_unused_external_entities(self):
        xml_file = casepath('resources/unused_external_entity.xml')

        elem = etree.ElementTree.parse(xml_file).getroot()
        self.assertEqual(elem.text, 'abc')

        parser = etree.SafeXMLParser(target=etree.PyElementTree.TreeBuilder())
        with self.assertRaises(etree.PyElementTree.ParseError) as ctx:
            etree.ElementTree.parse(xml_file, parser=parser)
        self.assertEqual("Entities are forbidden (entity_name='ee')", str(ctx.exception))

    def test_defuse_xml_unparsed_entities(self):
        xml_file = casepath('resources/unparsed_entity.xml')

        parser = etree.SafeXMLParser(target=etree.PyElementTree.TreeBuilder())
        with self.assertRaises(etree.PyElementTree.ParseError) as ctx:
            etree.ElementTree.parse(xml_file, parser=parser)
        self.assertEqual("Unparsed entities are forbidden (entity_name='logo_file')",
                         str(ctx.exception))

    def test_defuse_xml_unused_unparsed_entities(self):
        xml_file = casepath('resources/unused_unparsed_entity.xml')

        elem = etree.ElementTree.parse(xml_file).getroot()
        self.assertIsNone(elem.text)

        parser = etree.SafeXMLParser(target=etree.PyElementTree.TreeBuilder())
        with self.assertRaises(etree.PyElementTree.ParseError) as ctx:
            etree.ElementTree.parse(xml_file, parser=parser)
        self.assertEqual("Unparsed entities are forbidden (entity_name='logo_file')",
                         str(ctx.exception))

    def test_etree_iterpath(self):
        root = ElementTree.XML('<a><b1><c1/><c2/></b1><b2/><b3><c3/></b3></a>')

        items = list(etree.etree_iterpath(root))
        self.assertListEqual(items, [
            (root, '.'), (root[0], './b1'), (root[0][0], './b1/c1'),
            (root[0][1], './b1/c2'), (root[1], './b2'), (root[2], './b3'),
            (root[2][0], './b3/c3')
        ])

        self.assertListEqual(items, list(etree.etree_iterpath(root, tag='*')))
        self.assertListEqual(items, list(etree.etree_iterpath(root, path='')))
        self.assertListEqual(items, list(etree.etree_iterpath(root, path=None)))

        self.assertListEqual(list(etree.etree_iterpath(root, path='/')), [
            (root, '/'), (root[0], '/b1'), (root[0][0], '/b1/c1'),
            (root[0][1], '/b1/c2'), (root[1], '/b2'), (root[2], '/b3'),
            (root[2][0], '/b3/c3')
        ])

    def test_etree_getpath(self):
        root = ElementTree.XML('<a><b1><c1/><c2/></b1><b2/><b3><c3/></b3></a>')

        self.assertEqual(etree.etree_getpath(root, root), '.')
        self.assertEqual(etree.etree_getpath(root[0], root), './b1')
        self.assertEqual(etree.etree_getpath(root[2][0], root), './b3/c3')
        self.assertEqual(etree.etree_getpath(root[0], root, parent_path=True), '.')
        self.assertEqual(etree.etree_getpath(root[2][0], root, parent_path=True), './b3')

        self.assertIsNone(etree.etree_getpath(root, root[0]))
        self.assertIsNone(etree.etree_getpath(root[0], root[1]))
        self.assertIsNone(etree.etree_getpath(root, root, parent_path=True))

    def test_etree_elements_assert_equal(self):
        e1 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>\n')
        e2 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>\n')

        self.assertIsNone(etree.etree_elements_assert_equal(e1, e1))
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2))

        e2 = lxml.etree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>\n')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2))

        e2 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2/><b3/><b4/></a>\n')
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2)
        self.assertIn("has lesser children than <Element 'a'", str(ctx.exception))

        e2 = ElementTree.XML('<a><b1>text  <c1 a="1"/></b1>\n<b2/><b3/></a>\n')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, strict=False))
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2)
        self.assertIn("texts differ: 'text' != 'text  '", str(ctx.exception))

        e2 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2>text</b2><b3/></a>\n')
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2, strict=False)
        self.assertIn("texts differ: None != 'text'", str(ctx.exception))

        e2 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2))

        e2 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1><b2/><b3/></a>\n')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, strict=False))
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2)
        self.assertIn(r"tails differ: '\n' != None", str(ctx.exception))

        e2 = ElementTree.XML('<a><b1>text<c1 a="1 "/></b1>\n<b2/><b3/></a>\n')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, strict=False))
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2)
        self.assertIn("attributes differ: {'a': '1'} != {'a': '1 '}", str(ctx.exception))

        e2 = ElementTree.XML('<a><b1>text<c1 a="2 "/></b1>\n<b2/><b3/></a>\n')
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2, strict=False)
        self.assertIn("attribute 'a' values differ: '1' != '2'", str(ctx.exception))

        e2 = ElementTree.XML('<a><!--comment--><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>\n')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2))
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, skip_comments=False))

        e2 = lxml.etree.XML('<a><!--comment--><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>\n')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2))

        e1 = ElementTree.XML('<a><b1>+1</b1></a>')
        e2 = ElementTree.XML('<a><b1>+ 1 </b1></a>')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, strict=False))

        e1 = ElementTree.XML('<a><b1>+1</b1></a>')
        e2 = ElementTree.XML('<a><b1>+1.1 </b1></a>')

        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2, strict=False)
        self.assertIn("texts differ: '+1' != '+1.1 '", str(ctx.exception))

        e1 = ElementTree.XML('<a><b1>1</b1></a>')
        e2 = ElementTree.XML('<a><b1>true </b1></a>')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, strict=False))
        self.assertIsNone(etree.etree_elements_assert_equal(e2, e1, strict=False))

        e2 = ElementTree.XML('<a><b1>false </b1></a>')
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2, strict=False)
        self.assertIn("texts differ: '1' != 'false '", str(ctx.exception))

        e1 = ElementTree.XML('<a><b1> 0</b1></a>')
        self.assertIsNone(etree.etree_elements_assert_equal(e1, e2, strict=False))
        self.assertIsNone(etree.etree_elements_assert_equal(e2, e1, strict=False))

        e2 = ElementTree.XML('<a><b1>true </b1></a>')
        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2, strict=False)
        self.assertIn("texts differ: ' 0' != 'true '", str(ctx.exception))

        e1 = ElementTree.XML('<a><b1>text<c1 a="1"/></b1>\n<b2/><b3/></a>\n')
        e2 = ElementTree.XML('<a><b1>text<c1 a="1"/>tail</b1>\n<b2/><b3/></a>\n')

        with self.assertRaises(AssertionError) as ctx:
            etree.etree_elements_assert_equal(e1, e2, strict=False)
        self.assertIn("tails differ: None != 'tail'", str(ctx.exception))

    def test_iter_location_hints(self):
        elem = ElementTree.XML(
            """<root xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="http://example.com/xmlschema/ns-A import-case4a.xsd"/>"""
        )
        self.assertListEqual(
            list(etree.etree_iter_location_hints(elem)),
            [('http://example.com/xmlschema/ns-A', 'import-case4a.xsd')]
        )
        elem = ElementTree.XML(
            """<foo xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
            xsi:noNamespaceSchemaLocation="schema.xsd"/>"""
        )
        self.assertListEqual(
            list(etree.etree_iter_location_hints(elem)), [('', 'schema.xsd')]
        )

    def test_prune_etree(self):
        root = ElementTree.XML('<a><b1><c1/><c2/></b1><b2/><b3><c3/></b3></a>')
        etree.prune_etree(root, selector=lambda x: x.tag == 'b1')
        self.assertListEqual([e.tag for e in root.iter()], ['a', 'b2', 'b3', 'c3'])

        root = ElementTree.XML('<a><b1><c1/><c2/></b1><b2/><b3><c3/></b3></a>')
        etree.prune_etree(root, selector=lambda x: x.tag.startswith('c'))
        self.assertListEqual([e.tag for e in root.iter()], ['a', 'b1', 'b2', 'b3'])


if __name__ == '__main__':
    header_template = "ElementTree tests for xmlschema with Python {} on {}"
    header = header_template.format(platform.python_version(), platform.platform())
    print('{0}\n{1}\n{0}'.format("*" * len(header), header))

    unittest.main()
