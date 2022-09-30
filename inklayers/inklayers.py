#!/usr/bin/env python
"""
inklayers

@link https://github.com/toolleeo/inklayers

Export any combination of SVG layers to files.
"""
import subprocess
import sys
import os
from lxml import etree
import argparse
import pathlib
import semantic_version
import glob
import re
import json
import pytoml as toml
import configparser
from copy import deepcopy
from math import log10


# The subfolder used to save/export files. It's relative to the input file.
output_subfolder = '/output/'

def get_commandLine():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='''Exports combinations of layers from an SVG file to various formats (PDF, PNG, etc.).''',
                                     usage="%(prog)s [-h] infiles+ [options]",
    )

    p_add = parser.add_argument
    p_add('infiles', nargs='+',
          help='SVG, JSON or TOML file, wildcards supported')
    p_add('-a', '--add', action='append', default=None,
          help='Add layers to export. Use labels or indexes.')
    p_add('-e', '--exclude', action='append', default=None,
          help='Use label or index to determine which objects to exclude from export')
    p_add('-o', '--outfile', action='store', default='%b-%n.%e',
          help='Output file format. See documentation for possible formats.')
    p_add('-i', '--inkscape', action='store', default='Default',
          help='Path to inkscape command line executable')
    p_add('-t', '--type', action='store', default=None, choices=['png', 'ps', 'eps', 'pdf'],
          help='Export type (and suffix). pdf by default. See Inkscape --help for supported formats.')
    p_add('-X', '--extra', action='store', metavar='Inkscape_Export_Options', default=' ',
          help='Extra options passed through (literally) to inkscape for export. See Inkscape --help for more.')
    p_add('-D', '--debug', action='store_true', default=False,
          help='Generates (very) verbose output.')
    p_add('-l', '--list', action='store_true', default=False,
          help='List the available layers.')
    p_add('-v', '--verbosity', action='count', default=0,
          help='Verbosity level.')
    p_add('-out', '--outfolder', action='store', default=None)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--stack', action='store_true', default=False,
                       help='Export all layers in stacked mode. Use -e to exclude some layers.')
    group.add_argument('-S', '--split', action='store_true', default=False,
                       help='Export all layers, split one layer per output file. Use -e to exclude some layers.')
    c_line = parser.parse_args()
    d = vars(c_line)
    return d


class StringParser:
    """
    Service class used to contain a few methods regarding string manipulation.
    """
    @staticmethod
    def get_filters(filters, keyword):
        """
        If no layers are listed, returns an empty list.
        """
        # print('filters: %s keyword %s' % (str(filters), keyword))
        filt = []
        if keyword in filters:
            for i, x in enumerate(filters[keyword]):
                # print("i, x = %s" % x)
                intervals = StringParser.parse_interval_string(x)
                # print("intervals = %s" % intervals)
                if intervals is not None:
                    filt.extend(intervals)
        # print('filt = %s' % filt)
        return filt

    @staticmethod
    def parse_interval_string(s):
        """Parse the layer indexing string.

        Intervals can be defined by one number or two numbers separated by dash.
        Each number is prefixed by '#'.
        Different intervals can be separated by comma.

        Returns a list of tuples.
        Each tuple is the closed interval of layer indexes.

        Examples:
          "#0-#10" -> [(0, 10)]
          "#0,#10" -> [(0, 0), (10, 10)]
          "#0,#10-#15,#30" -> [(0, 0), (10, 15), (30, 30)]
        """
        intervals = []
        for i in s.split(','):
            tokens = i.split('-')
            tokens = [x.strip() for x in tokens]
            for x in tokens:
                if x[0] != '#':
                    return None
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def get_filtered_layer_labels(labels, filters):
        """
        Returns the list of layer's labels by filtering the list
        *labels* by including and excluding the elements specified
        in the *filters* dict.
        The intermediate filters corresponds to numerical intervals.
        """
        # add filters specified by intervals
        include = StringParser.get_filters(filters, 'include')
        exclude = StringParser.get_filters(filters, 'exclude')
        # add intervals corresponding to labels
        def get_filters_by_label(labels, filters, keyword):
            filt = []
            if keyword in filters:
                for x in filters[keyword]:
                    if x in labels:
                        index = labels.index(x)
                        filt.append((index, index))
            return filt
        include.extend(get_filters_by_label(labels, filters, 'include'))
        exclude.extend(get_filters_by_label(labels, filters, 'exclude'))
        # filters labels
        for i, label in enumerate(labels):
            # exclude those elements that are not included
            if not StringParser.is_number_in_intervals(i, include):
                labels[i] = None
            # exclude those elements that are explicitly excluded
            if StringParser.is_number_in_intervals(i, exclude):
                labels[i] = None
        # remove None values
        l = [x for x in labels if x is not None]
        return l

    @staticmethod
    def filter_slide_data(layers_data):
        """Fixes the slide data from the config file.

        Checks for escaped characters and splits based on the comma character.
        Returns a list containing the results.
        """
        test = re.split(r'(?<!\\),', layers_data)
        results = [t.replace('\,', ',') for t in test]
        return results


class FileHandler:
    """
    Handles the loading of slide configuration from input files and the creation of
    svg file instances along with a few filename operations.
    """
    def get_path_and_fullname(self, file):
        """
        Returns the path and the fullname (path + filename) of a file
        """
        path = os.path.dirname(file)
        if path == '':
            path = os.getcwd()
            file = path + '/' + file
        return path, file

    def get_basename(self, filename):
        bn, ext = os.path.splitext(filename)
        return bn

    def get_extension(self, filename):
        bn, ext = os.path.splitext(filename)
        return ext

    def get_etree(self, filename):
        with open(filename) as f:
            return etree.parse(f)

    def load_input_file(self, filename):
        """
        Returns an svg file object instance and a dictionary containing the slide configuration.
        """
        # disp("Loading " + ext.upper() + " file...", args, 2)
        svg_name = ''
        conf = None
        ext = self.get_extension(filename)

        with open(filename) as infile:
            if ext == '.svg':
                # TODO:  check if the SVG file has slide configuration included
                # conf = None
                # raise Exception('Unable to load config from svg file. Function not yet supported.')
                conf = {}
                svg_name = filename
            if ext == '.json':
                conf = json.load(infile)
                svg_name = conf['input']['filename']
            if ext == '.toml':
                conf = toml.load(infile)
                svg_name = conf['input']['filename']
            if ext == '.ini':
                conf = self._load_conf_from_ini(infile)
                svg_name = conf['input']['filename']
            elif ext not in ['.svg', '.json', '.toml', '.ini']:
                raise Exception('File type "{}" not supported'.format(ext))

        if os.path.dirname(svg_name) == '':
            full_svg_name = os.path.dirname(filename) + '/' + svg_name
        else:
            full_svg_name = svg_name
        svg_tree = self.get_etree(full_svg_name)
        svg_base_name = self.get_basename(svg_name)
        return SVGFile(svg_base_name, svg_tree), conf


    def _load_conf_from_ini(self, infile):
        """
        Retrieves the configuration from the ini file. Supports different versions of Python.
        """
        try:
            config = configparser.ConfigParser()
        except:
            config = ConfigParser.ConfigParser()
            config.readfp(infile)
            return self._process_ini_conf(config)
        config.read_file(infile)
        return self._process_ini_conf(config)


    def _process_ini_conf(self, config):
        """
        Handles the parsing of ini files. Returns a dictionary with the config file data.
        """
        conf = {'input': {'filename': None}, 'output': {'type': None, 'filename': None, 'slides': []}}
        conf['input']['filename'] = config.get('input', 'filename')
        conf['output']['type'] = config.get('output', 'type')
        conf['output']['filename'] = config.get('output', 'filename', raw=True)
        slide_sections = [section for section in config.sections() if str(section).startswith('slide_')]
        slide_sections = sorted(slide_sections)

        for slide in slide_sections:
            elements = config.items(slide, raw=True)
            slide_data = dict(elements)
            if 'include' in slide_data:
                slide_data['include'] = StringParser.filter_slide_data(slide_data.get('include'))
            if 'exclude' in slide_data:
                slide_data['exclude'] = StringParser.filter_slide_data(slide_data.get('exclude'))
            conf['output']['slides'].append(slide_data)
        return conf


class Layer():
    """
    Represents the layer object contained in a svg file or in a slide.
    """
    def __init__(self, obj):
        self.id = obj.get('id')
        self.label = Layer.get_label_from_obj(obj)

    @staticmethod
    def is_layer(e):
        if e.get('{http://www.inkscape.org/namespaces/inkscape}groupmode') == 'layer':
            return True
        else:
            return False

    @staticmethod
    def get_label_from_obj(e):
        label = e.get('{http://www.inkscape.org/namespaces/inkscape}label')
        return label

    def get_layer_labels(self, objects):
        """
        Returns the list of labels of each layer object passed as argument.
        """
        labels = [Layer.get_label_from_obj(x) for x in objects if Layer.is_layer(x)]
        return labels

    def get_label(self):
        return self.label

    @staticmethod
    def match_label(e, objects):
        label = Layer.get_label_from_obj(e)
        # print('   Checking label %s in %s' % (label, objects))
        if label in objects:
            return True
        return False


class Slide:
    """
    Contains everything related to a slide: id, filename, label, type, layers, elementTree data
    """
    def __init__(self, id, fname_fmt, label, type, layers, root):
        self.id = id
        self.filename = ''
        self.fname_fmt = fname_fmt
        self.name = label
        self.type = type # exported file extension
        self.layers = layers
        self.root = root

    def get_layers(self):
        """
        Returns: a list containing all the layer objects of the slide
        """
        return self.layers

    def get_labels(self):
        """
        Returns: a list containing all the layer labels of the slide
        """
        return [layer.get_label() for layer in self.layers]

    def update_layers(self, layers, root):
        """
        Updates the layer objects included in the slide
        """
        self.layers = layers
        self.root = root



class SlideConfiguration:
    """
    It aggregates all data regarding the slides to export.
    Given a dictionary extracted from the config file and optional settings from the user
    it creates a slide configuration to be used for exporting slides to files.
    """
    def __init__(self, svg_file, config, options):
        self.options = options
        self.svg_file = svg_file
        self.fname_fmt = self.load_element(config, 'output', 'filename')
        self.type = self.load_element(config, 'output', 'type')
        self.slides = []
        self.load_slides(self.load_element(config, 'output', 'slides'))

    def load_element(self, conf, key1, key2):
        """Loads the settings found in the config file
        using the keys provided.
        """
        try:
            return conf[key1][key2]
        except KeyError:
            raise KeyError("Config file format error: " + key1 + " -> " + key2 + " not found.")

    def load_slides(self, slides):
        """
        Loads the slides from the config file dictionary.
        Uses a specific method for stacked mode if required and proceeds by adding an id
        to each slide and by processing the slides.
        """
        self.check_unique_slide_names(slides)
        if self.options.get('stack'):
            slides = self.load_stacked_slides()
        for index, slide in enumerate(slides):
            slide['id'] = index
        self.process_slides(slides)
        # Sorts the slides by ID (if based-on is used they may be created in a different order sometimes).
        self.slides.sort(key=lambda x: x.id)
        # Sets the slide filenames. If a specific name is used for a slide, the index in the file names is not skipped
        # but kept for the next one that doesn't use a specific name
        bn = self.svg_file.basefilename
        for index, slide in enumerate(self.slides):
            if '%n' in slide.fname_fmt:
                fnumber = str(index).zfill(1 + int(log10(len(self.slides))))
            else:
                fnumber = None
            slide.filename = StringParser.get_filename(slide.fname_fmt, basename=bn, extension='svg', index=fnumber)

    def check_unique_slide_names(self, slides):
        """
        Verifies if a slide name is repeated more than once
        (That would cause a problem with based-on slides)
        """
        names = [slide.get('name') for slide in slides if slide.get('name') != None]
        if names == []:
            return
        count = [names.count(name) for name in set(names)]
        for x in count:
            if x > 1:
                raise Exception("Error in slide configuration: two slides with the same name found.")

    def process_slides(self, slides):
        """
        Process and make the slides adding them to a list in the slide configuration object.
        This method may be executed more than once depending on the number of 'based-on' slides.
        """
        old_count = len(slides)
        def madeNames(): # Returns the names of the slides already created (required by the based-on slides)
            return [slide.name for slide in self.slides if slide.name != '']

        for slide in slides:
            # If a slide is not based on another one or it is but the other was already created then make it now
            # (otherwise wait the next execution of this method)
            if 'based-on' not in slide or ('based-on' in slide and slide.get('based-on') in madeNames()):
                createdSlide = self.make_slide(slide)
                self.slides.append(createdSlide)

        madeIDs = [slide.id for slide in self.slides] # the IDs of the already created slides
        slides = [slide for slide in slides if slide['id'] not in madeIDs] # the slides remaining to be created
        new_count = len(slides)

        if new_count != 0 and new_count != old_count: # if there are slides remaining execute the method again
            self.process_slides(slides)
        # if there are slides left and no more slides were created in this iteration then there must be an error
        if new_count == old_count:
            raise Exception('Error in slide configuration. Wrong based-on names or circular based-on detected.')
        # Filter the slides using global parameters (specified by command line or gui)
        def filter_with_globals(param, action):
            for slide in self.slides:
                layers = slide.get_labels()
                self.filter_layers(param, action, layers)
                root = self.svg_file.get_filtered_obj(layers)
                layer_objs = self.svg_file.get_filtered_layer_objs(layers)
                slide.update_layers(layer_objs, root)
        if self.options.get('add') is not None:
            filter_with_globals(self.options.get('add'), 'add')
        if self.options.get('exclude') is not None:
            filter_with_globals(self.options.get('exclude'), 'exclude')

    def make_slide(self, slide):
        """
        Creates the slide
        """
        # Check if the slide has specific settings (a different file name/format or type/extension)
        fname_fmt = self.get_slide_specific_setting(slide, self.options.get('outfile'), self.fname_fmt, 'filename')
        type = self.get_slide_specific_setting(slide, self.options.get('type'), self.type, 'type')
        # Set the slide label
        slide_label = slide.get('name') if 'name' in slide else ''

        labels = self.svg_file.get_labels()
        layers = []
        # Load the layers. If a slide is based-on another do the appropriate filtering.
        if 'based-on' in slide:
            for madeSlide in self.slides:
                if slide.get('based-on') == madeSlide.name:
                    for layer in madeSlide.layers:
                        layers.append(layer.get_label())
                    if 'include' in slide:
                        slide_inc = [elem for elem in slide.get('include')]
                        self.filter_layers(slide_inc, 'add', layers)
                    if 'exclude' in slide:
                        slide_exc = [elem for elem in slide.get('exclude')]
                        self.filter_layers(slide_exc, 'exclude', layers)
        else:
            layers = StringParser.get_filtered_layer_labels(labels, slide)

        root = self.svg_file.get_filtered_obj(layers)
        layer_objs = self.svg_file.get_filtered_layer_objs(layers)
        return Slide(slide.get('id'), fname_fmt, slide_label, type, layer_objs, root)

    def filter_layers(self, filter, action, layers):
        """
        Filter a list of layers using include and exclude.
        Required for global parameters and based-on mechanism.
        """
        # get all the labels in the file
        labels_fil = self.svg_file.get_labels()
        # creates a slide with the layers to include or exclude
        slide_fil = {'include': filter}
        # get the layers as labels from slide_fil
        layers_fil = StringParser.get_filtered_layer_labels(labels_fil, slide_fil)
        if action == 'add':
            for layer in layers_fil:
                if layer not in layers:
                    layers.append(layer)
        if action == 'exclude':
            for layer in layers_fil:
                if layer in layers:
                    layers.remove(layer)

    def get_slide_specific_setting(self, slide, global_setting, config_setting, slide_setting):
        """
        Used to check if a slide has a specific setting (name format or type).
        If a global setting was specified in command line or gui it always overrides other settings.
        Otherwise the config file general setting is used, unless the slide has a specific setting.
        """
        if global_setting is not None:
            return global_setting
        else:
            if slide_setting in slide:
                return slide.get(slide_setting)
            else:
                return config_setting

    def load_stacked_slides(self):
        """
        Reads the svg file structure to obtain the image layers and builds the slides using the layers in stacked mode
        Example: [{"include" : "L1"}, {"include" : ["L1", "L2"]}, {"include" : ["L1", "L2", "L3"]}]
        """
        labels = self.svg_file.get_labels()
        slide_number = len(labels)
        slides = []
        def get_stacked_labels(counter):
            layers = []
            for i, label in enumerate(labels):
                if i <= counter:
                    layers.append(label)
                else:
                    break
            return layers
        for i in range(slide_number):
            slide = {"include": get_stacked_labels(i)}
            slides.append(slide)
        return slides


class SVGFile():
    """
    Represents the SVG file object used for slide configurations.
    """
    def __init__(self, basefilename, tree):
        self.basefilename = basefilename
        self.tree = tree
        self.layers = self._load_layers()

    def _load_layers(self):
        """
        Returns the list of layer objects contained in the XML tree.
        """
        layers = []
        root = self.tree.getroot()
        layers = [Layer(obj) for obj in root if Layer.is_layer(obj)]
        return layers

    def get_labels(self):
        """
        Returns: a list of the labels belonging to the layers in the file
        """
        labels = []
        for layer in self.layers:
            labels.append(layer.get_label())
        return labels

    def get_filtered_layer_objs(self, labels):
        """
        Returns: the layer objects corresponding to the labels passed as argument.
        """
        layer_objs = []
        for label in labels:
            for layer in self.layers:
                if layer.get_label() == label:
                    layer_objs.append(layer)
                    break
        return layer_objs

    def get_filtered_obj(self, layers):
        """
        Returns: the elementTree object that includes the layers passed as argument.
        """
        mytree = deepcopy(self.tree)
        root = mytree.getroot()
        for x in root:
            if Layer.is_layer(x) and not Layer.match_label(x, layers):
                root.remove(x)
        return root


class InklayersSystem():

    def __init__(self, args):
        self.args = args
        self.set_verbosity()
        self.run = self.set_subprocess()
        self.inkPath, self.version = self.verify_inkscape()
        self.fileHandler = FileHandler()

    def set_verbosity(self):
        if self.args.get('debug'):
            self.args['verbosity'] = 2

    def set_subprocess(self):
        if self.args.get('verbosity') >= 1:
            run = subprocess.check_call
        else:
            run = subprocess.check_output
        return run

    def verify_inkscape(self):
        """
        Fix inkscape path and attempt to execute to verify it.
        """
        inkPath = self.args.get('inkscape')
        if inkPath == 'Default':
            if (sys.platform == 'win32'):
                inkPath = 'C:\Progra~1\Inkscape\inkscape.com'
            else:
                inkPath = 'inkscape'
        try:
            self.run([inkPath, "-V"])
            output = subprocess.check_output([inkPath, '-V'])
        except FileNotFoundError:
            raise FileNotFoundError('Inkscape command line executable not found.\nSet --inkscape option accordingly.')
        version_str = str(output).split(' ')[1]
        numbers = version_str.split('.')
        # handle version format such as 1.2 (wrong semantic versioning format)
        if len(numbers) >= 3:
            version = semantic_version.Version(version_str)
        else:
            if len(numbers) == 2:
                version = semantic_version.Version(major=int(numbers[0]), minor=int(numbers[1]), patch=0)
            elif len(numbers) == 1:
                version = semantic_version.Version(major=int(numbers[0]), minor=0, patch=0)
        return inkPath, version


    def process_input_file(self, infile):
        """
        Given an input file, it loads the config data and svg_file object and
        creates a slide configuration object.
        """
        self.infile_path, infile = self.fileHandler.get_path_and_fullname(infile)
        svg_file, configFile = self.fileHandler.load_input_file(infile)
        self.slideConf = SlideConfiguration(svg_file, configFile, self.filtered_arguments())


    def filtered_arguments(self):
        """
        Filters the arguments and returns only the ones needed for the slide configuration
        """
        options = {}
        add = self.args.get('add')
        exclude = self.args.get('exclude')
        options['add'] = StringParser.filter_slide_data(add[0]) if add is not None else add
        options['exclude'] = StringParser.filter_slide_data(exclude[0]) if exclude is not None else exclude
        options['outfile'] = self.args.get('outfile')
        options['type'] = self.args.get('type')
        options['split'] = self.args.get('split')
        options['stack'] = self.args.get('stack')
        return options


class InklayersShell(InklayersSystem):

    def __init__(self, args):
        InklayersSystem.__init__(self, args)

    def fix_wildcard_names(self):
        """
        If an input file has wildcards, find results and add them to the input files
        """
        infiles = []
        for file in self.args.get('infiles'):
            if ('?' in file) or ('*' in file):
                globlist = glob.glob(file)
                for filename in globlist:
                    infiles.append(filename)
            else:
                infiles.append(file)
        self.args['infiles'] = infiles


    def process_files(self):
        """
        Process the input files. If the list option was not used it also exports them to files.
        If an exception is raised on a file, the error message is printed and the processing continues
        to the next file.
        """
        self.disp('**Processing input files', 2)
        for infile in self.args.get('infiles'):
            self.disp('\n**Processing: %s' %infile, 1)
            self.process_input_file(infile)
            self.disp('Processing done successfully', 1)
            if not self.args.get('list'):
                self.disp('**Saving: %s' % infile, 1)
                self.save_files()
                self.disp('**Printing latex code: ', 1)
                self.print_latex_code(infile)
        self.disp('\nProcessing completed.', 1)


    def process_input_file(self, infile):
        """
        Overrides the superclass version.
        Process the input file. Load the file and the configuration included in the file.
        If the list option was specified print the layer information.
        Otherwise load the slide configuration into a SlideConfiguration object.
        """
        self.infile_path, infile = self.fileHandler.get_path_and_fullname(infile)
        if self.args.get('list'):
            svg_file, configFile = self.fileHandler.load_input_file(infile)
            lines = (self.report_layers_info(svg_file))
            for l in lines:
                print(l)
        else:
            svg_file, configFile = self.fileHandler.load_input_file(infile)
            self.slideConf = SlideConfiguration(svg_file, configFile, self.filtered_arguments())

    def save_files(self):
        """
        Reads all the files loaded in the slide configuration and attempts to save them.
        If the split option was specified, it saves each slide layer to a different file.
        Otherwise the default method is used: each slide is saved to a single file.
        """
        for slide in self.slideConf.slides:
            if self.args.get('split'):
                self.disp('\n**Saving slide in splitted mode', 1)
                for i, layer in enumerate(slide.layers):
                    b = self.fileHandler.get_basename(slide.filename)
                    filename = b + '-split-' + str(i) + '.svg'
                    layer_root = self.slideConf.svg_file.get_filtered_obj(layer.get_label())
                    self.save_svg(filename, layer_root)
                    self.svg2file(slide, filename)
            else:
                self.disp('\n**Saving slide in standard mode', 2)
                self.save_svg(slide.filename, slide.root)
                self.svg2file(slide)

    def save_svg(self, name, root):
        """
        Saves the slide to a .svg file with an appropriate name.
        """
        p = pathlib.Path(self.infile_path + output_subfolder)
        p.mkdir(parents=True, exist_ok=True)
        filename = self.infile_path + output_subfolder + name
        command = etree.tostring(root, encoding="unicode", pretty_print=True)
        with open(filename, 'w') as f:
            f.write(command)

    def format_inkscape_command(self, slide_type, svg_file, outfile, extra_args=''):
        """Builds the command to call inkscape depending on its version."""
        if self.version.major == 0 and self.version.minor > 91:
            command = '{} --export-{} {} {} {}'.format(self.inkPath, slide_type, outfile, extra_args, svg_file)
        elif self.version.major >= 1:
            command = '{} --export-type={} {} -o {} {}'.format(self.inkPath, slide_type, svg_file, outfile, extra_args)
        return command

    def svg2file(self, slide, filename='slide'):
        """
        Uses the inkscape executable to export the file to the specified format. Extra arguments are supported.
        The filename passed as argument can be the slide filename or the specific layer name for split mode.
        """
        if filename == 'slide':
            filename = slide.filename
        p = pathlib.Path(self.infile_path + output_subfolder)
        p.mkdir(parents=True, exist_ok=True)
        outpath = self.infile_path + output_subfolder
        svg_file = outpath + filename
        base_name, ext = os.path.splitext(filename)
        outfile = outpath + base_name + '.' + slide.type
        command = self.format_inkscape_command(slide.type, svg_file, outfile, self.args.get('extra'))
        self.disp("Running '%s'" % command, 2)
        self.run(command, shell=True)

    def report_layers_info(self, svg_file):
        """
        Retrieve information about layers in a SVG file.
        Returns the set of strings to print, already formatted.
        """
        lines = ["#%d: '%s'" % (i, x.get_label()) for i, x in enumerate(svg_file.layers)]
        return lines

    def print_latex_code(self, infile):
        """Print code for inclusion into LaTeX documents.
        """
        latex_basename = self.fileHandler.get_basename(infile)
        outpath = self.infile_path + output_subfolder
        fullpath = outpath + latex_basename + '.inc.tex'
        with open(fullpath, 'w') as latex_file:
            for i, slide in enumerate(self.slideConf.slides):
                base_name, ext = os.path.splitext(slide.filename)
                slide_name = base_name + '.' + slide.type
                latex_file.write('\\includegraphics<{}|handout:0>[width=1.0\\columnwidth]{{{}}}%\n'.format(i + 1, slide_name))

    def disp(self, msg, level):
        """
        Print function that handles verbosity level.
        """
        if self.args.get('verbosity') >= level:
            print(msg)


def main():
    # load command line arguments, initialize system
    prog = InklayersShell(get_commandLine())
    prog.fix_wildcard_names()
    # process input files & export/save
    prog.process_files()


if __name__ == '__main__':
    main()




