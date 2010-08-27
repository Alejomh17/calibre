#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import with_statement

__license__   = 'GPL v3'
__copyright__ = '2009, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import re

from calibre.customize.conversion import InputFormatPlugin
from calibre.ebooks.conversion.preprocess import line_length

class LITInput(InputFormatPlugin):

    name        = 'LIT Input'
    author      = 'Marshall T. Vandegrift'
    description = 'Convert LIT files to HTML'
    file_types  = set(['lit'])

    def convert(self, stream, options, file_ext, log,
                accelerators):
        from calibre.ebooks.lit.reader import LitReader
        from calibre.ebooks.conversion.plumber import create_oebbook
        self.log = log
        return create_oebbook(log, stream, options, self, reader=LitReader)

    def postprocess_book(self, oeb, opts, log):
        from calibre.ebooks.oeb.base import XHTML_NS, XPath, XHTML
        for item in oeb.spine:
            root = item.data
            if not hasattr(root, 'xpath'): continue
            for bad in ('metadata', 'guide'):
                metadata = XPath('//h:'+bad)(root)
                if metadata:
                    for x in metadata:
                        x.getparent().remove(x)
            body = XPath('//h:body')(root)
            if body:
                body = body[0]
                if len(body) == 1 and body[0].tag == XHTML('pre'):
                    pre = body[0]
                    from calibre.ebooks.txt.processor import convert_basic
                    from lxml import etree
                    import copy
                    html = convert_basic(pre.text).replace('<html>',
                            '<html xmlns="%s">'%XHTML_NS)
                    root = etree.fromstring(html)
                    body = XPath('//h:body')(root)
                    pre.tag = XHTML('div')
                    pre.text = ''
                    for elem in body:
                        ne = copy.deepcopy(elem)
                        pre.append(ne)


	def preprocess_html(self, html):
		self.log("*********  Preprocessing HTML  *********")
		# Detect Chapters to match the xpath in the GUI
		chapdetect = re.compile(r'(?=</?(br|p|span))(</?(br|p|span)[^>]*>)?\s*(?P<chap>(<(i|b)><(i|b)>|<(i|b)>)?(.?Chapter|Epilogue|Prologue|Book|Part|Dedication)\s*([\d\w-]+(\s\w+)?)?(</(i|b)></(i|b)>|</(i|b)>)?)(</?(p|br|span)[^>]*>)', re.IGNORECASE)
		html = chapdetect.sub('<h2>'+'\g<chap>'+'</h2>\n', html)
		# Unwrap lines using punctation if the median length of all lines is less than 150
		#
		# Insert extra line feeds so the line length regex functions properly
		html = re.sub(r"</p>", "</p>\n", html)
		length = line_length('html', html, 0.4)
		self.log("*** Median length is " + str(length) + " ***")
		unwrap = re.compile(r"(?<=.{%i}[a-z,;:\IA])\s*</(span|p|div)>\s*(</(p|span|div)>)?\s*(?P<up2threeblanks><(p|span|div)[^>]*>\s*(<(p|span|div)[^>]*>\s*</(span|p|div)>\s*)</(span|p|div)>\s*){0,3}\s*<(span|div|p)[^>]*>\s*(<(span|div|p)[^>]*>)?\s*" % length, re.UNICODE)
		if length < 150:
			html = unwrap.sub(' ', html)
        return html

