#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Put paragraph texts and some canvas primitives at absolute position
# in a template pdf page with reportlab and pdfrw, see README.txt

import sys
import re
from reportlab.platypus import PageTemplate, BaseDocTemplate, Frame
from reportlab.platypus import NextPageTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import mm
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


PAGE_WIDTH = defaultPageSize[0]
PAGE_HEIGHT = defaultPageSize[1]
STYLES = getSampleStyleSheet()
DEFAULT_STYLE = "Normal"


class MyPage(PageTemplate):
    "Backgroundpage plus additional paragraphs or canvas primiteve"

    def __init__(self, bg_page, name=None):
        frames = [Frame(
            22.0*mm,
            13.0*mm,
            PAGE_WIDTH-30.0*mm,
            PAGE_HEIGHT-30.0*mm,
            )]
        PageTemplate.__init__(self, name, frames)
        self.page_template = pagexobj(bg_page)
        # scale to fill the complete page
        self.page_xscale = PAGE_WIDTH/self.page_template.BBox[2]
        self.page_yscale = PAGE_HEIGHT/self.page_template.BBox[3]
        # store content and absolute position of paragraphs/primitives
        self.abspars = []
        self.absprims = []

    def beforeDrawPage(self, canvas, doc):
        "All drawing"
        canvas.saveState()
        rl_obj = makerl(canvas, self.page_template)
        canvas.scale(self.page_xscale, self.page_yscale)
        canvas.doForm(rl_obj)
        canvas.restoreState()
        self.canvas = canvas # store canvas for reuse
        for abspar in self.abspars:
            self._putAbsParagraph(*abspar)
        for absprim in self.absprims:
            self._putAbsPrim(*absprim)

    def _putAbsParagraph(self, text, x, y, width, style):
        "put paragraph on absolute position"
        p = Paragraph(text, style=style)
        p.wrapOn(self.canvas, width, PAGE_HEIGHT)
        p.drawOn(self.canvas, x, y)

    def _putAbsPrim(self, type, attr, content, x, y, width):
        "put primitive canvas operation on absolute position"
        if type not in PRIMITIVES:
            raise Exception("Unsupported type: %s" % type)
        self.canvas.saveState()
        PRIMITIVES[type](self.canvas, attr, content, x, y, width)
        self.canvas.restoreState()

    def addAbsParagraph(self, text, x, y, width, style):
        "user api, store paragraph texts to be rendered later"
        self.abspars.append((text, x, y, width, STYLES[style]))

    def addAbsPrimitive(self, data, x, y, width):
        "user api, store primitive description to be rendered later"
        type, attr, content = data
        self.absprims.append((type, attr, content, x, y, width))


## supported primitive operations
def put_line(canvas, attr, content, x, y, width):
    "draw a line, every four params are two points, start/end"
    if len(content) % 4 != 0:
        raise Exception("line: must have mutiple of 4 pos")
    if "width" in attr:
        canvas.setLineWidth(attr["width"])
    for i in range(0, len(content), 4):
        from_x, from_y, to_x, to_y = content[i:i+4]
        canvas.line(x+from_x, y+from_y, x+to_x, y+to_y)

def put_box(canvas, attr, content, x, y, width):
    "draw a box, every four params are one point (lower left), width, height"
    if len(content) % 4 != 0:
        raise Exception("line: must have mutiple of 4 pos")
    if "width" in attr:
        canvas.setLineWidth(attr["width"])
    for i in range(0, len(content), 4):
        ll_x, ll_y, width, height = content[i:i+4]
        canvas.rect(x+ll_x, y + ll_y, width, height)

def put_ellipse(canvas, attr, content, x, y, width):
    "draw an ellipse, 4 params are one point (lower left), width, height"
    if len(content) % 4 != 0:
        raise Exception("line: must have mutiple of 4 pos")
    if "width" in attr:
        canvas.setLineWidth(attr["width"])
    for i in range(0, len(content), 4):
        ll_x, ll_y, ru_x, ru_y = content[i:i+4]
        canvas.ellipse(x+ll_x, y+ll_y, x+ru_x, y+ru_y)


PRIMITIVES = {
    "line": put_line,
    "box": put_box,
    "ellipse": put_ellipse,
}
        


## configuration files
def read_template_page(template_filename):
    "first page of a template file"
    page = PdfReader(template_filename).pages[0]
    return page


def create_pdf(togen, template_page, pos, dat):
    "Create the pdf, stream api"
    document = BaseDocTemplate(togen)
    page = MyPage(template_page, name='background') 
    document.addPageTemplates([page])
    elements = [NextPageTemplate('background')]
    # may add flowables to element here
    
    # add absolute content
    for posname in dat:
        if posname.startswith("_"): # ignore extra info
            continue
        if posname not in pos:
            raise Exception("%s does not have a position" % posname)
        tup = pos[posname]
        x, y = tup[0], tup[1]
        width = tup[2] if len(tup)>2 else PAGE_WIDTH
        style = tup[3] if len(tup)>3 else DEFAULT_STYLE
        data = dat[posname]
        if type(data) in (str, unicode):
            page.addAbsParagraph(data, x, y, width, style)
        else:
            page.addAbsPrimitive(data, x, y, width) # don't need no style
    # create page
    document.multiBuild(elements)


import datetime
DYNAMICS = {
    '<date>': lambda : datetime.datetime.now().strftime("%d.%m.%Y"),
    '<day>' : lambda : datetime.datetime.now().strftime("%d"),
    '<weekday>' : lambda : datetime.datetime.now().strftime("%a"),
    '<fullweekday>' : lambda : datetime.datetime.now().strftime("%A"),
    '<month>' : lambda : datetime.datetime.now().strftime("%m"),
    '<amonth>' : lambda : datetime.datetime.now().strftime("%b"),
    '<fullmonth>' : lambda : datetime.datetime.now().strftime("%B"),
    '<year>': lambda : datetime.datetime.now().strftime("%Y"),
    '<time>': lambda : datetime.datetime.now().strftime("%H:%M:%S"),
    '<hour>' : lambda : datetime.datetime.now().strftime("%H"),
    '<min>' : lambda : datetime.datetime.now().strftime("%M"),
    '<sec>' : lambda : datetime.datetime.now().strftime("%S"),   
    }

def parse_tag(value, tag="line"):
    value = value.strip()
    starttagp, endtag = "<%s" % tag, "</%s>" % tag
    if not value.startswith(starttagp):
        raise Exception("<%s> does not start with <%s ???" % (tag, tag))
    value = value.lstrip(starttagp)
    if not value.endswith(endtag):
        raise Exception("<%s> does not end with </%s>" % (tag, tag))
    value = value.rstrip(endtag).strip()
    if ">" not in value:
        raise Exception("<%s ... does not end" % tag)
    endstarttag = value.find(">")
    attrs = value[0:endstarttag].strip()
    content = value[endstarttag+1:].strip()
    attr = dict()
    for e in re.split("\s+", attrs):
        e = e.strip()
        if not e:
            continue
        if "=" not in e:
            raise Exception("<%s attrs ... no = in attribute" % tag)
        key, value = e.split("=", 1)
        key = key.strip()
        value = value.strip()
        value = value.strip('"')
        value = value.strip("'")
        if key in ("width"): # floats            
            value = float(value)
        attr[key] = value    
    return attr, content
    

def parse_val_tag(value, tag):
    attr, content = parse_tag(value, tag)
    points = [float(v.strip(",")) for v in content.split(",")]
    return tag, attr, points
    
def apply_dynamics(value):
    "apply predefined dynamic values"
    for key in DYNAMICS:
        if key in value:
            func = DYNAMICS[key]
            value = value.replace(key, func())            
    return value 

def read_dict(fname, get_value):
    dic = dict()
    lc = 0
    last_name = None # if there is a continuation
    for line in file(fname):
        lc += 1
        if line.startswith("#"):
            continue
        if not line.strip(): # ignore empty lines
            continue
        if last_name != None: # a continuation
            value = line
        else:
            if "=" not in line:
                raise Exception("%s:%d: no = in line" % (fname, lc))
            name, value = line.split("=", 1)
            name = name.strip() # get rid of all whitespace for key
            if name in dic:
                raise Exception("%s:%d: double name %s" % (fname, lc, name))
        value = value.rstrip("\n")
        last_name = name if value.endswith("\\") else None # a continuation
        if last_name:
            value = value[:-1]
        value = get_value(value, lc)
        if name in dic: 
            dic[name] += value
        else:
            dic[name] = value
    return dic
    
def read_dat(tpldat):
    def get_value(value, lc):
        value = apply_dynamics(value)
        for prim in PRIMITIVES: # for now all val tags
            if value.startswith("<%s" % prim): # xxx special
                value = parse_val_tag(value, prim)
                break
        return value
    return read_dict(tpldat, get_value)

def read_pos(tplpos):
    def get_value(value, lc):
        vals = value.split(",")
        if len(vals) < 2:
            raise Exception("%s:%d: At least x, y expected" % (tplpos, lc))
        try: 
            x, y = float(vals[0]), float(vals[1])
        except ValueError:
            raise Exception("%s:%d: x, y must be float" % (tplpos, lc))
        width = PAGE_WIDTH
        if len(vals) >= 3:
            width = float(vals[2])
        style = "Normal"
        if len(vals) >= 4:
            style = vals[3].strip()
        return (x, y, width, style)
    return read_dict(tplpos, get_value)

def handle_console():
    import sys
    print("%s [ tpl.dat tpl.pos tpl.pdf out.pdf ]" % sys.argv[0])
    tpldat = sys.argv[1] if len(sys.argv) > 1 else "tpl.dat"
    tplpos = sys.argv[2] if len(sys.argv) > 2 else "tpl.pos"
    tplpdf = sys.argv[3] if len(sys.argv) > 3 else "tpl.pdf"
    outpdf = sys.argv[4] if len(sys.argv) > 4 else "out.pdf"
    tup = (tpldat, tplpos, tplpdf, outpdf)
    print("Add from %s at %s to %s generating %s" % tup)
    page = read_template_page(tplpdf)
    pos = read_pos(tplpos)
    dat = read_dat(tpldat)
    output_file = open(outpdf, "w")
    create_pdf(output_file, page, pos, dat)
    output_file.close()
    

def test():
    # program generated content
    pos, dat = dict(), dict()
    r = [(x, y) for x in (30, 66, 120) for y in range(100, 200, 5)]
    for x, y in r:
        posname = "pos%d%d" % (x, y)
        text = "Position %dx%d" % (x, y)
        pos[posname] = (x, y, "Normal")
        dat[posname] = text        
    page = read_template_page("tpl.pdf")
    output = open("out.pdf", "w")
    create_pdf(output, page, pos, dat)
    output.close()

if __name__ == '__main__':
    import os, sys
    if "-test" in sys.argv:
        test()
    else:
        handle_console()

