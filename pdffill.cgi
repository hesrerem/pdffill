#!/usr/bin/python
import sys, os
sys.path.append(os.path.dirname(__file__)) # find pdffill.py
os.chdir(os.path.dirname(__file__)) # find tpl.html
import cgi
import re
import traceback
import pdffill


DEBUG = True

# Definition of keys and default filenames
TPLPDF, TPLPOS, TPLDAT, TPLHTML = 'tplpdf', 'tplpos', 'tpldat', 'tpthtml'
DEFAULTS = {
    TPLPDF: "tpl.pdf",    # the PDF template to be filled out
    TPLPOS: "tpl.pos",    # where are the fill-ins to be put
    TPLDAT: "tplcgi.dat", # the fill-ins, default values
    TPLHTML: "tpl.html",  # the HTML-form to query the fill-ins
    }
TEMPLATE_FOLDER = '' # current folder is default

# HTTP-Header for PDF-file download
HEADER = """Content-Type: application/pdf
Content-Disposition: attachement; filename=%(title)s\n"""

def form_processing(form, dat):
    "template specific, modify dat (remove not add), can/should be changed"
    # classical check boxes
    for check_key in ('check_veg', 'check_meat', 'check_you'):
        if check_key not in form:
            del dat[check_key]
    # evaluate the checkboxes
    del dat['dont1' if 'check_dodont1' in form else 'do1']
    del dat['do2' if 'check_dodont2' in form else 'dont2']
    # evaluate the radio buttons
    keep = form["radio_pens"] if "radio_pens" in form else None
    for key in ("one", "two", "many"):
        if key != keep:
            del dat[key]
    return None


def filename_default(key, form):
    "provides an ok filename based on form values or defaults"
    if key not in form:
        if key not in DEFAULTS:
            raise Exception("No value nor default for %s" % key)
        return DEFAULTS[key]
    value = form[key]
    if not re.search("^[a-zA-Z0-9_\.-]+$", value): # sanity
        raise Exception("Use sensible filenames, break in attempt?")
    filename = os.path.join(TEMPLATE_FOLDER, value)
    if not os.path.exists(filename):
        raise Exception("Filename does not exist, break in attempt?")
    return filename

def handle_cgi(form):
    "handles a CGI-Request producing an pdf if all works well"
    tplpdf = filename_default(TPLPDF, form)
    tplpos = filename_default(TPLPOS, form)
    tpldat = filename_default(TPLDAT, form) 
    page = pdffill.read_template_page(tplpdf)
    pos = pdffill.read_pos(tplpos)
    try: 
        dat = pdffill.read_dat(tpldat)
    except:
        dat = dict()
    # copy fitting names from form to dat
    for name in pos:
        # no default treatment for selection keys
        if (name.startswith("check") or
            name.startswith("radio") or
            name.startswith("select")):
            continue
        if name in form:
            dat[name] = form[name]
            del form[name] # already processed
    # do the template specific stuff
    form_processing(form, dat)
    # output
    dic = dict([('title', tplpdf)])
    print(HEADER % dic)
    pdffill.create_pdf(sys.stdout, page, pos, dat)
    sys.stdout.close() # it is a PDF-page, that's it


# use a classical dictionary of either list of str or values
fieldstorage = cgi.FieldStorage()
form = dict()
for key in fieldstorage:
    form[key] = fieldstorage.getvalue(key)

# either show html form or render pdf
if ("REQUEST_METHOD" in os.environ and
    os.environ["REQUEST_METHOD"] == "POST"): # render pdf, evaluate form
    try:
        handle_cgi(form)
    except Exception, err:
        exc_type, exc_value, exc_tb = sys.exc_info()
        tb = traceback.format_exception(exc_type, exc_value, exc_tb)
        print('Content-Type: text/plain\n')
        if DEBUG:
            print(''.join(tb))
            for k in os.environ:
                print('%s: %s' % (k, os.environ[k]))
        else:
            print ('ERROR: ')                
else: # show form (defaults only from file)
    print('Content-Type: text/html\n')
    tpldat = filename_default(TPLDAT, form)     
    tpldat = pdffill.read_dat(tpldat)
    htmlform = file(filename_default(TPLHTML, form)).read()
    print(htmlform % tpldat)

