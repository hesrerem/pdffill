pdffill
=======

pdffill is a Python library/tool to fill any PDF template page with text
and simple graphics. It requires pdfrw (to read pdf) and reportlab (to 
print on and write out PDF). The position of the insert spots and the 
content can either be simple text files or python dictionaries. A common 
use case is generating a PDF using a template and content/decisions from 
an HTML form, which can easily be done with an CGI program.

The ODT source (tpl.odt) and generated PDF (tpl.pdf) of a simple template 
is provided. With the position information (tpl.pos) data (tpl.dat) can be 
put on that PDF template. A sample out.pdf is generated by executing 
  $ python pdffill.py
which accepts commandline arguments and is a shortcut for
  $ python pdffill.py tpl.dat tpl.pos tpl.pdf out.pdf 
In addition, there is a pdffill.cgi and tpl.html which demonstrates the 
usage as CGI-program. tpl.dat is replaced by tplcgi.dat, which includes
more information that is filtered by the CGI-processing and may include
choice-information that won't be rendered but just processed.

Hopefully, the examples are self explanatory. There is no command 
overview. However, the examples should cover all of what is available.

Have fun

Sources
=======
* https://code.google.com/p/pdfrw/, including examples
* http://www.blog.pythonlibrary.org/2012/06/27/reportlab-mixing-fixed-content-and-flowables/
* http://stackoverflow.com/questions/4726011/wrap-text-in-a-table-reportlab
