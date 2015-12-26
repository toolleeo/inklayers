#!/usr/bin/env python
"""
svg-export-layers

@link https://github.com/toolleeo/svg-export-layers

Export any combination of SVG layers to files.
By default the exported file is in SVG format.
If Inkscape is found in the system, an automatic conversion to
Inkscape supported formats (png, pdf, ps, eps) can be done.
Tested with Inkscape version 0.91.

Layers can be referenced by label or index (#0, #1, ...).
The first layer has index 0.
Layer's interval is supported. Example format: #1-#9.

Layers can be selected for inclusion or exclusion.
If include/exclude options collide, the latest prevails.

TODO: redefine the license.
 * This software is release under the terms of .................
 *
"""
import argparse
import sys
import subprocess
import json
import logging
from copy import deepcopy
from lxml import etree


# constants (feel free to change these to your favorite defaults)
if (sys.platform == 'win32'):
    inkscape_prog = 'C:\Progra~1\Inkscape\inkscape.com'
else:
    inkscape_prog = 'inkscape'

xpath_namespaces = {'svg': "http://www.w3.org/2000/svg",
                    'sodipodi': "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
                    'inkscape': "http://www.inkscape.org/namespaces/inkscape",
                    'xlink': "http://www.w3.org/1999/xlink",
                    're': "http://exslt.org/regular-expressions"}

# usually not code change below this line is necessary. any improvement suggestions is welcome.
# parse options
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description='''Exports multiple objects from an SVG file to various formats (PNG, SVG, PS, EPS, PDF).''',
                                 usage="%(prog)s [-h] [-p PATTERN] [options] infiles+",
                                 epilog='''requirements
    This program requires Inkscape 0.48+ and Python 2.7+

default behaviour:
    The program exports by default all objects with an ID that has not
    been generated automatically by Inkscape.

    If you provide a custom pattern (-p) or xpath expression (-x), then exclude
    (-e) is by default turned off, that is: your custom pattern or expression is
    used to define wich objects	are *included* unless you specify -e.

examples:

  %(prog)s --pattern '^export' in.svg
     exports all objects with an ID starting with 'export' from in.svg
     to PNG files in the current directory.

  %(prog)s --exclude --xpath '//svg:g | //svg:rect' in.svg
      exports all objects that are no SVG group or rectangle, from in.svg to
      PNG files in current working directory. Namespaces available are: svg,
      inkscape, sodipodi, xlink, re (for regular expressions).
      See http://lxml.de for more on xpath in this program.

  %(prog)s --pattern '^(obj1|obj4)$' --prefix 'FILE_' in1.svg in2.svg
     exports objects with IDs 'obj1' and 'obj4', from both in1 and in2
     files, to PNG files named in1_obj1.png, in1_obj4.png, in2_obj1.png
     and    in2_obj4.png.

  %(prog)s --silent --force --type eps --destdir vector/  ~/*.svg ~/tmp/*.svg
    exports all objects with an ID that does not resemble Inkscape
    default IDs, from any SVG file in user's home and tmp directories,
    to ./vector/ directory as EPS files, with no information displayed and
    overwritting existing files

  %(prog)s --exclude --pattern '[0-9]' --extra '--export-dpi 900' in.svg
    exports all objects with an ID containing no digit, from in.svg file,
    as PNG images with a resolution for    rasterization of 900 dpi. As
    Inkscape uses 90 by default, this results in 10-times bigger images.


Additional examples: https://github.com/berteh/svg-objects-export/wiki

''')

p_add = parser.add_argument
p_add('infiles', nargs='+',
      help='SVG or JSON file, wildcards supported')
p_add('-a', '--add', action='store_true', default=0,
      help='Add layers to export. Use labels or indexes.')
p_add('-e', '--exclude', action='store_true', default=0,
      help='Use label or index to determine which objects to exclude from export')
p_add('-o', '--outfile', default='FILE_',
      help='Output file format. See documentation for possible formats.')
p_add('-i', '--inkscape', default=inkscape_prog,   # metavar='path_to_inkscape',
      help='Path to inkscape command line executable')
p_add('-t', '--type', default='pdf', choices=['png', 'ps', 'eps', 'pdf'],
      help='Export type (and suffix). pdf by default. See Inkscape --help for supported formats.')
p_add('-X', '--extra', metavar='Inkscape_Export_Options', default=' ',
      help='Extra options passed through (literally) to inkscape for export. See Inkscape --help for more.')
p_add('-D', '--debug', action='store_true', default=False,
      help='Generates (very) verbose output.')
p_add('-v', '--verbosity', default=0,
      help='Verbosity level.')
p_add('-s', '--stack', default=False,
      help='Export all layers in stacked mode. Use -e to exclude some layers.')
p_add('-1', '--one', default=True,
      help='Export all layers, one layer per output file. Use -e to exclude some layers.')


def debug(*msg):
    """ Utility "print" function that handles verbosity of messages
    """
    if (args.debug):
        print msg
    return


def get_layer_id(infile, layer_name):
    # TODO: the parsing of the file should be done only once, returning all the layers
    # message("exporting from " + infile + " all objects " + ife(args.exclude, 'not ', '') + "matching " + args.xpath)
    parser = etree.XMLParser()   # ns_clean=True)
    intree = etree.parse(infile, parser)
    if (len(parser.error_log) > 0):
        logging.error("Could not parse ", infile, ":")
        debug(parser.error_log)

    # find the ids
    find_str_ids = "(" + "//svg:g[@inkscape:groupmode='layer']" + ")/@id"
    find_ids = etree.XPath(find_str_ids, namespaces=xpath_namespaces)
    ids = find_ids(intree)
    print(ids)

    # find the labels
    find_str_labels = "(" + "//svg:g[@inkscape:groupmode='layer']" + ")/@inkscape:label"
    find_labels = etree.XPath(find_str_labels, namespaces=xpath_namespaces)
    labels = find_labels(intree)

    index = labels.index(layer_name)
    return ids[index]


def get_id(infile, obj):
    print("obj: %s" % obj)
    if 'layer' in obj:
        obj_id = get_layer_id(infile, obj['layer'])
    print("Returning: %s" % obj_id)
    return obj_id


def get_ids(infile, objs):
    ids = [get_id(infile, o) for o in objs]
    return ids


def get_file_type_from_filename(filename):
    return filename.split('.')[-1]


def find_layers(tree):
    find_str_layers = "(" + "//svg:g[@inkscape:groupmode='layer']" + ")"
    find_layers = etree.XPath(find_str_layers, namespaces=xpath_namespaces)
    layers = find_layers(tree)
    print(layers)
    # for l in layers:
    #     print(etree.tostring(l, pretty_print=True))


def is_layer(e):
    if e.get('{http://www.inkscape.org/namespaces/inkscape}groupmode') == 'layer':
        return True
    else:
        return False


def match_label(e, objects):
    label = e.get('{http://www.inkscape.org/namespaces/inkscape}label')
    # print('   Checking label %s in %s' % (label, objects))
    for o in objects:
        if 'layer' in o:
            if label == o['layer']:
                return True
    return False


def print_layers(tree):
    root = tree.getroot()
    for x in root:
        if is_layer(x):
            print('%s' % (x.get('{http://www.inkscape.org/namespaces/inkscape}label')))
            # print('%s %s' % (x.tag, x.keys()))
            # print('%s %s' % (x.tag, x.get('id')))


def save_svg(tree, objects, outfile):
    print('*** Saving to %s' % outfile)
    mytree = deepcopy(tree)
    root = mytree.getroot()
    # print(etree.tostring(root, pretty_print=True))
    for x in root:
        if is_layer(x) and not match_label(x, objects):
            root.remove(x)
    print_layers(mytree)
    with open(outfile, 'w') as f:
        f.write(etree.tostring(mytree, pretty_print=True))


def inkscape_installed(args):
    """ Verify inkscape path. """
    try:
        run([args.inkscape, "-V"])
        return True
    except Exception:
        return False


def split_filename(fname):
    """
    Split filename into basename (optional path included) and extension.
    """
    index = fname.rfind('.')
    if index >= 0:
        basename = fname[:index]
        extension = fname[index + 1:]
        return basename, extension
    else:
        return None, None


def convert(svg_file, outfile, desttype, args):
    """
    Convert svg_file, provided with extension, into desttype with same basename.
    Args contains the inkscape pathname and arguments.
    """
    if not inkscape_installed(args):
        print('Inkscape command line executable not found.')
        print('Set --inkscape option accordingly.')
        return

    command = args.inkscape + ' --export-' + desttype + ' ' + outfile + ' ' + args.extra + ' ' + svg_file
    print("Running '%s'" % command)
    run(command, shell=True)


def process_config_file(conf, args):
    infile = conf['input']
    with open(infile) as f:
        tree = etree.parse(f)
        # root = tree.getroot()
        # print(etree.tostring(root, pretty_print=True))
        # for x in root:
        #     print('%s %s' % (x.tag, x.get('{http://www.inkscape.org/namespaces/inkscape}label')))
        #     print('%s %s' % (x.tag, x.keys()))
        #     # print('%s %s' % (x.tag, x.get('id')))

        for out in conf['output']:
            outfile = out['filename']
            (base_name, extension) = split_filename(outfile)
            print('%s : %s . %s' % (outfile, base_name, extension))
            save_svg(tree, out['objects'], base_name + '.svg')

            # convert the svg file into the desired format
            # if out['type'] == 'auto':
            #     filetype = get_file_type_from_filename(outfile)
            # else:
            desttype = out['type']
            convert(base_name + '.svg', outfile, desttype, args)


if __name__ == '__main__':
    # handle command-line arguments
    args = parser.parse_args()
    if args.verbosity >= 1:
        run = subprocess.check_call
    else:
        run = subprocess.check_output

    for infile_arg in args.infiles:
        try:
            with open(infile_arg) as config_file:
                conf = json.load(config_file)
            process_config_file(conf, args)
        except Exception:
            print('File %s is not JSON.' % infile_arg)
