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
p_add('-q', '--query', action='store_true', default=False,
      help='List the available layers.')
p_add('-v', '--verbosity', default=0,
      help='Verbosity level.')
p_add('-s', '--stack', default=False,
      help='Export all layers in stacked mode. Use -e to exclude some layers.')
p_add('-S', '--split', default=True,
      help='Export all layers, split one layer per output file. Use -e to exclude some layers.')


def debug(*msg):
    """ Utility "print" function that handles verbosity of messages
    """
    if (args.debug):
        print(msg)
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


def get_label(e):
    label = e.get('{http://www.inkscape.org/namespaces/inkscape}label')
    return label


def match_label(e, objects):
    label = get_label(e)
    # print('   Checking label %s in %s' % (label, objects))
    if label in objects:
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
    Convert svg_file, provided with extension, into outfile.
    Args contains the inkscape pathname and arguments.
    """
    if not inkscape_installed(args):
        print('Inkscape command line executable not found.')
        print('Set --inkscape option accordingly.')
        return

    command = args.inkscape + ' --export-' + desttype + ' ' + outfile + ' ' + args.extra + ' ' + svg_file
    print("Running '%s'" % command)
    run(command, shell=True)


def parse_interval_string(s):
    """
    Parse the layer indexing string.
    Intervals can be defined by one number or two numbers separated by dash.
    Each number is prefixed by '#'.
    Different intervals can be separated by comma.
    Returns a list of tuples. Each tuple is the closed interval of layer indexes.
    Examples:

      "#0-#10" -> [(0, 10)]
      "#0,#10" -> [(0, 0), (10, 10)]
      "#0,#10-#15,#30" -> [(0, 0), (10, 15), (30, 30)]
    """
    intervals = []
    for i in s.split(','):
        tokens = i.split('-')
        tokens = [x.strip() for x in tokens]
        try:
            intvals = [int(x[1:]) for x in tokens]
        except Exception:
            return None
        if len(intvals) == 1:
            intervals.append((intvals[0], intvals[0]))
        elif len(intvals) == 2:
            intervals.append((intvals[0], intvals[1]))
        else:
            return None
    return intervals


def get_filename(fmt, basename=None, extension=None, index=None):
    if fmt.find('%b') > 0 and basename is None:
        return None
    if basename is not None:
        fmt = fmt.replace('%b', basename)
    if fmt.find('%e') > 0 and extension is None:
        return None
    if extension is not None:
        fmt = fmt.replace('%e', extension)
    if fmt.find('%n') > 0 and index is None:
        return None
    if index is not None:
        fmt = fmt.replace('%n', str(index))
    return fmt


def get_filters(filters, keyword):
    """
    If no layers are listed, returns an empty list.
    """
    logging.debug('filters: %s keyword %s' % (str(filters), keyword))
    filt = []
    if keyword in filters:
        for x in filters[keyword]:
            intervals = parse_interval_string(x)
            if intervals is not None:
                filt.extend(intervals)
    return filt


def is_number_in_intervals(n, intervals):
    """
    Check whether the numerical value n is included in any interval
    in the intervals list.
    The intervals list has the form [(x1, x2), (y1, y2), ...]
    """
    if any(lower <= n <= upper for (lower, upper) in intervals):
        return True
    else:
        return False


def get_filtered_layer_names(labels, filters):
    include = get_filters(filters, 'include')
    exclude = get_filters(filters, 'exclude')
    print('include = %s' % str(include))
    print('exclude = %s' % str(exclude))
    for i, label in enumerate(labels):
        # exclude those elements that are not included
        if not is_number_in_intervals(i, include):
            labels[i] = None
        # exclude those elements that are explicitly excluded
        if is_number_in_intervals(i, exclude):
            labels[i] = None
    # remove None values
    l = [x for x in labels if x is not None]
    return l


def process_config_file(conf, args):
    try:
        infile = conf['input']['filename']
    except:
        print('JSON format error: input -> filename not found.')
        return
    with open(infile) as f:
        tree = etree.parse(f)
        # root = tree.getroot()
        # print(etree.tostring(root, pretty_print=True))
        # for x in root:
        #     print('%s %s' % (x.tag, x.get('{http://www.inkscape.org/namespaces/inkscape}label')))
        #     print('%s %s' % (x.tag, x.keys()))
        #     # print('%s %s' % (x.tag, x.get('id')))
        try:
            outfile = conf['output']['filename']
        except Exception:
            print('JSON format error: output -> filename not found.')
            return

        try:
            dest_type = conf['output']['type']
        except Exception:
            print('JSON format error: output -> type not found.')
            return

        try:
            slides = conf['output']['slides']
        except Exception:
            print('JSON format error: output -> slides not found.')
            return

        for index, slide in enumerate(slides):
            # a filename specification in a slide overrides the global one
            if 'filename' in slide:
                slide_filename_fmt = slide['filename']
            else:
                slide_filename_fmt = outfile
            # a type specification in a slide overrides the global one
            if 'type' in slide:
                type_slide = slide['type']
            else:
                type_slide = dest_type

            (bn, ext) = split_filename(infile)
            slide_filename = get_filename(slide_filename_fmt, basename=bn, extension='svg', index=index)
            (base_name, extension) = split_filename(slide_filename)
            labels = get_layer_labels(get_layer_objects(tree))
            logging.debug('labels %s' % str(labels))
            logging.debug('slide %s' % str(slide))
            layers = get_filtered_layer_names(labels, slide)
            logging.debug('layers %s' % str(layers))

            save_svg(tree, layers, slide_filename)

            # TODO: add support for automatic file extension
            # convert the svg file into the desired format
            # if out['type'] == 'auto':
            #     filetype = get_file_type_from_filename(outfile)
            # else:
            convert(base_name + '.svg', base_name + '.' + type_slide, type_slide, args)


def get_layer_objects(tree):
    """
    Returns the list of layer objects contained in the XML tree.
    """
    root = tree.getroot()
    layers = [x for x in root if is_layer(x)]
    return layers


def get_layer_labels(objects):
    """
    Returns the list of labels of each layer object.
    """
    labels = [get_label(x) for x in objects if is_layer(x)]
    return labels


def report_layers_info(infile):
    """
    Retrieve information about layers in a SVG file.
    Returns the set of strings to print, already formatted.
    """
    with open(infile) as f:
        tree = etree.parse(f)
        objects = get_layer_objects(tree)
        lines = ["#%d: '%s'" % (i, get_label(x)) for i, x in enumerate(objects) if is_layer(x)]
        return lines

if __name__ == '__main__':
    # handle command-line arguments
    args = parser.parse_args()
    if args.verbosity >= 1:
        run = subprocess.check_call
    else:
        run = subprocess.check_output

    if args.query:
        for infile_arg in args.infiles:
            print('* Layers in %s' % infile_arg)
            lines = report_layers_info(infile_arg)
            for l in lines:
                print(l)
        sys.exit(0)

    for infile_arg in args.infiles:
        # try:
        with open(infile_arg) as config_file:
            conf = json.load(config_file)
            process_config_file(conf, args)
        # except Exception:
        #     print('File %s is not JSON.' % infile_arg)
