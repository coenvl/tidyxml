#!/usr/bin/python

# This scripts sorts the attributes of an XML file. Very much thanks to SnellyBigoda.
# Much of the code is taken from this answer: https://stackoverflow.com/a/30902567/3541094

import xml.etree.ElementTree as ET

def __sort_tags(tags):
    types = [t for t in tags if t[0].startswith('{http://www.w3.org/2001/XMLSchema')]
    other = [t for t in tags if not t[0].startswith('{http://www.w3.org/2001/XMLSchema')]
    return sorted(types) + sorted(other)

def _serialize_xml(write, elem, encoding, qnames, namespaces):
    tag = elem.tag
    text = elem.text
    if tag is ET.Comment:
        write("<!--%s-->" % ET._encode(text, encoding))
    elif tag is ET.ProcessingInstruction:
        write("<?%s?>" % ET._encode(text, encoding))
    else:
        tag = qnames[tag]
        if tag is None:
            if text:
                write(ET._escape_cdata(text, encoding))
            for e in elem:
                _serialize_xml(write, e, encoding, qnames, None)
        else:
            write("<" + tag)
            items = elem.items()
            if items or namespaces:
                if namespaces:
                    for v, k in sorted(namespaces.items(),
                                       key=lambda x: x[1]):  # sort on prefix
                        if k:
                            k = ":" + k
                        write(" xmlns%s=\"%s\"" % (
                            k.encode(encoding),
                            ET._escape_attrib(v, encoding)
                            ))
                for k, v in __sort_tags(items):  # lexical order
                #for k, v in items: # Monkey patch
                    if isinstance(k, ET.QName):
                        k = k.text
                    if isinstance(v, ET.QName):
                        v = qnames[v.text]
                    else:
                        v = ET._escape_attrib(v, encoding)
                    write(" %s=\"%s\"" % (qnames[k], v))
            if text or len(elem):
                write(">")
                if text:
                    write(ET._escape_cdata(text, encoding))
                for e in elem:
                    _serialize_xml(write, e, encoding, qnames, None)
                write("</" + tag + ">")
            else:
                write(" />")
    if elem.tail:
        write(ET._escape_cdata(elem.tail, encoding))

ET._serialize_xml = _serialize_xml

from collections import OrderedDict

class OrderedXMLTreeBuilder(ET.XMLTreeBuilder):
    def _start_list(self, tag, attrib_in):
        fixname = self._fixname
        tag = fixname(tag)
        attrib = OrderedDict()
        if attrib_in:
            for i in range(0, len(attrib_in), 2):
                attrib[fixname(attrib_in[i])] = self._fixtext(attrib_in[i+1])
        return self._target.start(tag, attrib)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print('Usage: %s in.xml out.xml' % sys.argv[0])
        exit()

    input = sys.argv[1]
    output = sys.argv[2]

    with open(input) as file:
        namespaces = dict([node for _, node in ET.iterparse(file, events=['start-ns'])])
        for name, domain in namespaces.items():
            ET.register_namespace(name, domain)

    with open(input) as file:
        tree = ET.parse(file, OrderedXMLTreeBuilder())
        tree.write(output, xml_declaration=True, encoding="UTF-8")