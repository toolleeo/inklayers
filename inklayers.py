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
import pytoml as toml
import glob

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

# parse options
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
            description='''Exports combinations of layers from an SVG file to various formats (PDF, PNG, etc.).''',
            usage="%(prog)s [-h] infiles+ [options]",
            epilog='''

Requirements
    This program requires Inkscape 0.48+ and Python 3.0+
    Tested with Inkscape version 0.91.

Behaviour:
    The program exports any combination of SVG layers to files.
    By default the exported file is in SVG format.
    If Inkscape is found in the system, an automatic conversion to
    Inkscape supported formats (png, pdf, ps, eps) can be done.

    Multiple config file formats are currently supported: JSON and TOML.

    Layers can be referenced by label or index (#0, #1, ...).
    The first layer has index 0.
    Layer's interval is supported. Example format: #1-#9.

    Layers can be selected for inclusion or exclusion.
    If include/exclude options collide, the latest prevails.

    Wildcards for input files are supported.

Examples:
    %(prog)s *.svg -q
    lists the avaiable layers for all the SVG files found in the folder.

    %(prog)s file.json -eL0 -e#2-#4
    exports the slides included in the config file by processing the svg file specified
    and excludes the layers labelled "L0", #2, #3, #4

    %(prog)s file.json -o(format)
    exports the slides included in the config file by processing the svg file specified
    and sets the output filename format (number-basename.extension for example)
    (overrides the config file setting)

    %(prog)s file.json -tpng
    exports the slides included in the config file by processing the svg file specified
    and sets the output file type
    (overrides the config file setting)

    %(prog)s file.svg file-?.svg file2.json -q -v
    lists the avaiable layers on: file.svg and any file starting with file-?.svg
    and also all exports the slides from the file specified in file2.json
    (level-1 verbosity)

''')

p_add = parser.add_argument
p_add('infiles', nargs='+',
      help='SVG, JSON or TOML file, wildcards supported')
p_add('-a', '--add', action='append', default=None,
      help='Add layers to export. Use labels or indexes.')
p_add('-e', '--exclude', action='append', default=None,
      help='Use label or index to determine which objects to exclude from export')
p_add('-o', '--outfile', action='store', default=None, choices=['%b-%n.%e', '%b_%n.%e', '%n-%b.%e'],
      help='Output file format. See documentation for possible formats.')
p_add('-i', '--inkscape', action='store', default=inkscape_prog,   # metavar='path_to_inkscape',
      help='Path to inkscape command line executable')
p_add('-t', '--type', action='store', default=None, choices=['png', 'ps', 'eps', 'pdf'],
      help='Export type (and suffix). pdf by default. See Inkscape --help for supported formats.')
p_add('-X', '--extra', action='append', metavar='Inkscape_Export_Options', default=' ',
      help='Extra options passed through (literally) to inkscape for export. See Inkscape --help for more.')
p_add('-D', '--debug', action='store_true', default=False,
      help='Generates (very) verbose output.')
p_add('-q', '--query', action='store_true', default=False,
      help='List the available layers.')
p_add('-v', '--verbosity', action='count', default=0,
      help='Verbosity level.')
p_add('-s', '--stack', action='store_true', default=False,
      help='Export all layers in stacked mode. Use -e to exclude some layers.')
p_add('-S', '--split', action='store_true', default=False,
      help='Export all layers, split one layer per output file. Use -e to exclude some layers.')
p_add('-l', '--latex', action='store_true', default=False,
      help='Print code for inclusion into LaTeX documents.')


def disp(msg, args, level):
    """ Print function that handles verbosity level.
    """
    try:
        if args.verbosity >= level:
            print(msg)
    except:
        pass


def get_layer_id(infile, layer_name):
    # TODO: the parsing of the file should be done only once, returning all the layers
    # message("exporting from " + infile + " all objects " + ife(args.exclude, 'not ', '') + "matching " + args.xpath)
    parser = etree.XMLParser()   # ns_clean=True)
    intree = etree.parse(infile, parser)
    if (len(parser.error_log) > 0):
        logging.error("Could not parse ", infile, ":")
        logging.debug(parser.error_log)

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


def save_svg(tree, objects, outfile, args={}):
    disp('*** Saving to %s' % outfile, args, 1)
    mytree = deepcopy(tree)
    root = mytree.getroot()
    for x in root:
        if is_layer(x) and not match_label(x, objects):
            root.remove(x)
    try:
        if args.verbosity >= 1:
            print_layers(mytree)
    except:
        pass
    with open(outfile, 'w') as f:
        f.write(etree.tostring(mytree, encoding="unicode", pretty_print=True))


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


def svg2file(base_name, desttype, args):
    """
    Convert base_name.svg into outfile named base_file.ext,
    where ext depends on desttype.
    Args contains the inkscape pathname and arguments.
    """
    if not inkscape_installed(args):
        print('Inkscape command line executable not found.')
        print('Set --inkscape option accordingly.')
        return

    svg_file = base_name + '.svg'
    outfile = base_name + '.' + desttype
    command = args.inkscape + ' --export-' + desttype + ' ' + outfile + ' ' + args.extra + ' ' + svg_file
    disp("Running '%s'" % command, args, 2)
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
    """
    Returns a file name given a file format (ex. %b-%n.%e)
    """
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
    # print('filters: %s keyword %s' % (str(filters), keyword))
    filt = []
    if keyword in filters:
        for i, x in enumerate(filters[keyword]):
            # print("i, x = %s" % x)
            intervals = parse_interval_string(x)
            # print("intervals = %s" % intervals)
            if intervals is not None:
                filt.extend(intervals)
    # print('filt = %s' % filt)
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


def get_filters_by_label(labels, filters, keyword):
    filt = []
    if keyword in filters:
        for x in filters[keyword]:
            if x in labels:
                index = labels.index(x)
                filt.append((index, index))
    return filt


def get_filtered_layer_labels(labels, filters):
    """
    Returns the list of layer's labels by filtering the list
    *labels* by including and excluding the elements specified
    in the *filters* dict.
    The intermediate filters corresponds to numerical intervals.
    """
    # add filters specified by intervals
    include = get_filters(filters, 'include')
    exclude = get_filters(filters, 'exclude')
    # add intervals corresponding to labels
    include.extend(get_filters_by_label(labels, filters, 'include'))
    exclude.extend(get_filters_by_label(labels, filters, 'exclude'))
    # filters labels
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


def etree_test(tree):
    root = tree.getroot()
    print(etree.tostring(root, encoding="unicode", pretty_print=True))
    for x in root:
        print('%s %s' % (x.tag, x.get('{http://www.inkscape.org/namespaces/inkscape}label')))
        print('%s %s' % (x.tag, x.keys()))
        print('%s %s' % (x.tag, x.get('id')))


def load_info_from_config(conf, key1, key2):
    """Loads the settings from the config file
    using the keys provided
    (Examples: the input svg file, the output file type,
    the output file format and the slides)

    Args:
        conf: The config file to be processed
        key1: The key to search for
        key2: The subkey to search for

    Returns:
        The value associated with the keys
        (or an exception message to be catched by the main program)
    """
    try:
        return conf[key1][key2]
    except:
        raise Exception("Config file format error: " + key1 + " -> " + key2 + " not found.")


def process_config_file(conf, args):
    """Manages the generation of svg files and conversions according
    to the desired options.
    Returns the list of generated files.
    """
    infile = load_info_from_config(conf, 'input', 'filename')
    filenames = []
    with open(infile) as f:
        tree = etree.parse(f)
        # etree_test(tree)

        # If a file output format is not specified in the command line, the format in the config file is used.
        # If it's specified, the command line option overrides the config file setting
        if (args.outfile is None):
            outfile = load_info_from_config(conf, 'output', 'filename')
        else:
            outfile = args.outfile
        disp("Output file format: %s" % outfile, args, 2)

        # If a file type is not specified in the command line, the type from the config file is used.
        # If it's specified, the command line option overrides the config file setting
        if (args.type is None):
            dest_type = load_info_from_config(conf, 'output', 'type')
        else:
            dest_type = args.type
        disp("Destination type: %s" % dest_type, args, 2)

        # get slides from config file
        slides = load_info_from_config(conf, 'output', 'slides')

        # process each slide in the config slide
        for index, slide in enumerate(slides):
            # if an output file format is not specified in the command line...
            if args.outfile is None:
                # ...a filename specification in a slide overrides the global one in the config file
                if 'filename' in slide:
                    slide_filename_fmt = slide['filename']
                    disp("Output file format for this slide: %s" % slide_filename_fmt, args, 2)
                else:
                    slide_filename_fmt = outfile
            else:
                slide_filename_fmt = args.outfile
            # if a type is not specified in the command line...
            if args.type is None:
                # ...a type specification in a slide overrides the global one in the config file
                if 'type' in slide:
                    type_slide = slide['type']
                    disp("Destination type for this slide: %s" % type_slide, args, 2)
                else:
                    type_slide = dest_type
            else:
                type_slide = args.type

            (bn, ext) = split_filename(infile)
            # slide filename
            slide_filename = get_filename(slide_filename_fmt, basename=bn, extension='svg', index=index)
            filenames.append(slide_filename)
            (base_name, extension) = split_filename(slide_filename)

            labels = get_layer_labels(get_layer_objects(tree))
            logging.debug('labels %s' % str(labels))
            logging.debug('slide %s' % str(slide))
            layers = get_filtered_layer_labels(labels, slide)
            logging.debug('layers %s' % str(layers))

            if args.add is not None:
                filter_layers_by_parameters(args.add, 'add', layers, tree)

            if args.exclude is not None:
                filter_layers_by_parameters(args.exclude, 'exclude', layers, tree)

            save_svg(tree, layers, slide_filename, args=args)

            # TODO: add support for automatic file extension
            # convert the svg file into the desired format
            # if out['type'] == 'auto':
            #     filetype = get_file_type_from_filename(outfile)
            # else:
            svg2file(base_name, type_slide, args)
    return filenames


def filter_layers_by_parameters(filter, action, layers, tree):
    """
    Modifies the layers of the current slide to add or exclude
    the layers specified in the command line
    Args:
        filter: the layers to add or exclude
        action: how to handle the layers ('add' or 'exclude')
        layers: the layers of the current slide after previous filtering
        tree: the tree structure of the config file

    Returns:
        -
    """
    # get all the labels in the file
    labels_fil = get_layer_labels(get_layer_objects(tree))
    # creates a slide with the layers to include or exclude
    slide_fil = {'include': filter}
    # get the layers as labels from slide_fil
    layers_fil = get_filtered_layer_labels(labels_fil, slide_fil)

    if action == 'add':
        for x in layers_fil:
            if x not in layers:
                disp("*Layer %s added" % x, args, 2)
                layers.append(x)

    if action == 'exclude':
        for x in layers_fil:
            if x in layers:
                disp("*Layer %s excluded" % x, args, 2)
                layers.remove(x)

    return


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


def print_latex_code(filenames):
    for f in filenames:
        print('\\includegraphics[width=1.0\\columnwidth]{%s}' % f)


def get_filenames_from_wildcard(argfiles):
    """
    Given the input files from the command line,
    if wild cards are present extracts the corresponding files
    and add them to the list to return

    Args:
        argfiles: the input files included in the command line arguments

    Returns:
        a list of all the files to process
    """
    infiles = []
    for file in argfiles:
        # if a file has wildcards, process and add results (if any)
        if ('?' in file) or ('*' in file):
            globlist = glob.glob(file)
            for filename in globlist:
                infiles.append(filename)
        # if a file doesn't have wildcards just add it
        else:
            infiles.append(file)
    return infiles



### main
if __name__ == '__main__':
    # handle command-line arguments
    args = parser.parse_args()
    args.infiles = get_filenames_from_wildcard(args.infiles)

    # load verbosity level
    if (args.debug == True):
        args.verbosity = 2
    if (args.verbosity >= 1):
        run = subprocess.check_call
    else:
        run = subprocess.check_output

    # scan all input files
    for infile_arg in args.infiles:
        disp("\nProcessing %s file..." %infile_arg, args, 1)
        ext, ext = split_filename(infile_arg)

        if ext == 'svg':
            if args.query:
                disp("Executing query...", args, 2)
                try:
                    print('\n* Layers in %s' % infile_arg)
                    lines = report_layers_info(infile_arg)
                    for l in lines:
                        print(l)
                    continue
                except Exception as e:
                    print(e)
                    #print("Couldn't get layer info from %s..." % infile_arg)
                    continue
            else:
                disp("Query option not selected, ignoring SVG file...", args, 0)
                continue

        if (ext == 'json') or (ext == 'toml'):
            disp("Loading " + ext.upper() + " file...", args, 2)
            try:
                with open(infile_arg) as config_file:
                    if ext == 'json':
                        conf = json.load(config_file)
                    if ext == 'toml':
                        conf = toml.load(config_file)
                    filenames = process_config_file(conf, args)
                    if args.latex:
                        print_latex_code(filenames)
                        continue
            except Exception as e:
                print(e)
                #print('File %s is not ' + ext + ' or has invalid data.' % infile_arg)
                disp("\nMoving on to the next input file...", args, 2)
                continue

        else:
            print("Invalid file name or format not supported")
            disp("\nMoving on to the next input file...", args, 2)
            continue

    disp("\nAll input files processed. Program completed", args, 1)