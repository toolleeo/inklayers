#!/usr/bin/env python
"""
This extension is used to export slides to files.
A slide is a combination of layers of an SVG file.
The inklayers module is used for all the processing, this file only works
as an interface between inkscape and the other module.
By executing inklayers.py from a commandline more advanced options are avaiable.
"""
import os
import inkex
import sys
#sys.path.insert(0, 'C:/Users/Fabio/inklayers/')

output_subfolder = '/output/'

from inklayers import InklayersSystem


class OptionHandler(inkex.Effect):
    """
    Handles the parameters passed by the Inkscape extension GUI.
    """
    def __init__(self):
        inkex.Effect.__init__(self)

        self.OptionParser.add_option("--tab", action="store",
                                     type="string", dest="tab")

        self.OptionParser.add_option("--configFile", action="store",
                                     type="string", dest="configFile",
                                     default=None, help="")

        self.OptionParser.add_option("--typeExp", action="store",
                                     type="string", dest="typeExp",
                                     default=None, help="")

        self.OptionParser.add_option("--namefmtExp", action="store",
                                     type="string", dest="namefmtExp",
                                     default=None, help="")

        self.OptionParser.add_option("--addLayers", action="store",
                                     type="string", dest="addLayers",
                                     default='', help="")

        self.OptionParser.add_option("--excludeLayers", action="store",
                                     type="string", dest="excludeLayers",
                                     default='', help="")

        #self.OptionParser.add_option("--ignore", action="store",
        #                             type="inkbool", dest="ignore",
        #                             default=None, help="")


    def effect(self):
        """
        Creates an instance of Inklayers and passes the options in the correct format
        and the svg root related to the currently opened document.
        """
        svg_root = self.document.getroot()
        program = InklayersExtension(self.options, svg_root)
        try:
            program.process_file()
        except Exception as e:
            raise e


class InklayersExtension(InklayersSystem):
    """
    A version of Inklayers to be used as Inkscape extension.
    """
    def __init__(self, options, svg_root):
        InklayersSystem.__init__(self, self.parse_options(options))
        self.svg_root = svg_root

    def parse_options(self, options):
        """
        Returns: a dictionary containing the arguments in the correct format for Inklayers
        """
        args = {}
        args['infiles'] = options.configFile
        args['type'] = None if options.typeExp == 'None' else options.typeExp
        args['outfile'] = None if options.namefmtExp == 'None' else options.namefmtExp
        args['add'] = None if options.addLayers == '' else [options.addLayers]
        args['exclude'] = None if options.excludeLayers == '' else [options.excludeLayers]
        args['inkscape'] = 'Default'
        args['debug'] = True
        args['verbosity'] = 0
        args['extra'] = ' '
        return args


    def process_file(self):
        """
        Uses the superclass method to process an input file.
        """
        self.process_input_file(self.args.get('infiles'))

        if self.config_file_is_correct():
            self.save_file()
        else:
            raise Exception("The config file doesn't refer to the currently opened file.")

    def config_file_is_correct(self):
        """
        Verifies if the config file used is related to the currently opened file in Inkscape.
        """
        h1 = self.slideConf.svg_file.tree.getroot()
        h2 = self.svg_root
        if h1.tag == h2.tag and h1.attrib == h2.attrib and h1.tail == h2.tail:
            return True
        else:
            return False
        #return etree.tostring(h1) == etree.tostring(h2)


    def save_file(self):
        """
        Save the slides to svg files before exporting.
        """
        from lxml import etree
        for slide in self.slideConf.slides:
            filename = self.infile_path + output_subfolder + slide.filename
            command = etree.tostring(slide.root, pretty_print=True)
            with open(filename, 'w') as f:
                f.write(command)
            inkex.errormsg(str(filename) + ' saved.')
            self.svg2file(slide)


    def svg2file(self, slide):
        """
        Launches the inkscape executable to export the slides in the desired format.
        """
        outpath = self.infile_path + output_subfolder
        svg_file = outpath + slide.filename
        base_name, ext = os.path.splitext(slide.filename)
        outfile = outpath + base_name + '.' + slide.type
        command = self.inkPath + ' --export-' + slide.type + ' ' + outfile + ' ' + self.args.get('extra') + ' ' + svg_file
        self.run(command, shell=True)
        inkex.errormsg(str(outfile) + ' exported.')


if __name__ == '__main__':

    try:
        e = OptionHandler()
        e.affect()
        inkex.errormsg("The files have been exported.")

    except Exception as e:
        #import traceback
        #inkex.errormsg(str(traceback.print_exc()))
        inkex.errormsg(str(e))




