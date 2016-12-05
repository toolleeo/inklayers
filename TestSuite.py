import unittest
# import logging
# import json
from lxml import etree
import inklayers, inklayersExt
import os

test_drawing_file = 'fishes.svg'
config = {'output': {'filename': '%b-%n.%e', 'slides': [{'include': ['L0']}, {'include': ['L0', 'L1']}, {'include': ['#0-#2']}, {'include': ['#0-#3']}, {'include': ['#0-#4']}, {'include': ['#0-#5']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#6']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#7']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#8']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#9']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#10']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#11']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#12']}, {'exclude': ['L5 msg:greetings', 'L12 msg:reply'], 'include': ['#0-#12']}], 'type': 'pdf'}, 'input': {'filename': 'fishes.svg'}}
config_err = {'output': {'filename': '%b-%n.%e', 'slides': [{'include': ['L0']}, {'include': ['L0', 'L1']}, {'include': ['#0-#2']}, {'include': ['#0-#3']}, {'include': ['#0-#4']}, {'include': ['#0-#5']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#6']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#7']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#8']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#9']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#10']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#11']}, {'exclude': ['L5 msg:greetings'], 'include': ['#0-#12']}, {'exclude': ['L5 msg:greetings', 'L12 msg:reply'], 'include': ['#0-#12']}], 'type': 'pdf'}}
path = os.getcwd()
fileHandler = inklayers.FileHandler()
svg_tree = fileHandler.get_etree(test_drawing_file)
svg_file = inklayers.SVGFile(fileHandler.get_basename(test_drawing_file), svg_tree)


class TestStringParser(unittest.TestCase):

    def test_parse_interval_string_one_value(self):
        intervals = inklayers.StringParser.parse_interval_string(' #0 ')
        self.assertEqual(intervals, [(0, 0)])

    def test_parse_interval_string_one_interval(self):
        intervals = inklayers.StringParser.parse_interval_string(' #0 - #10 ')
        self.assertEqual(intervals, [(0, 10)])

    def test_parse_interval_string_two_values(self):
        intervals = inklayers.StringParser.parse_interval_string(' #0, #10 ')
        self.assertEqual(intervals, [(0, 0), (10, 10)])

    def test_parse_interval_string_two_intervals(self):
        intervals = inklayers.StringParser.parse_interval_string(' #0 - #10 , #100 - #200 ')
        self.assertEqual(intervals, [(0, 10), (100, 200)])

    def test_parse_interval_string_two_values_two_intervals(self):
        intervals = inklayers.StringParser.parse_interval_string('#0,#5-#10,#15,#20-#30')
        self.assertEqual(intervals, [(0, 0), (5, 10), (15, 15), (20, 30)])

    def test_parse_interval_string_wrong_format_1(self):
        intervals = inklayers.StringParser.parse_interval_string('0')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_2(self):
        intervals = inklayers.StringParser.parse_interval_string('#0-1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_3(self):
        intervals = inklayers.StringParser.parse_interval_string('#0,1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_4(self):
        intervals = inklayers.StringParser.parse_interval_string('#0-#1-#2')
        self.assertEqual(intervals, None)

    # This test works now ( previously it expected: [(1, 1)] )
    def test_parse_interval_string_wrong_format_5(self):
        intervals = inklayers.StringParser.parse_interval_string('L1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_6(self):
        intervals = inklayers.StringParser.parse_interval_string('L#1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_7(self):
        intervals = inklayers.StringParser.parse_interval_string('#L1')
        self.assertEqual(intervals, None)

    #
    # Tests for the inclusion/exclusion of layers in one slide
    #
    def test_layer_filtering_no_inclusion(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4']
        filters = {'exclude': ['L2']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, [])

    def test_layer_filtering_no_exclusion(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4']
        filters = {'include': ['L0', 'L2']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L2'])

    # this test works now (previously it expected: ['L3', 'quarto']
    def test_layer_filtering_inclusion_of_labels_with_numbers(self):
        labels = ['primo', 'secondo', 'L3', 'quarto', 'quinto']
        filters = {'include': ['L3']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L3'])

    def test_layer_filtering_inclusion_of_labels_with_numbers2(self):
        labels = ['primo', 'secondo', 'L3', 'quarto', 'quinto']
        filters = {'include': ['L3', 'quinto']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L3', 'quinto'])

    def test_layer_filtering_included_1_interval_exclude_1_label(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4']
        filters = {'include': ['#0-#4'], 'exclude': ['L2']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L1', 'L3', 'L4'])

    def test_layer_filtering_included_2_intervals_exclude_3_labels(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7']
        filters = {'include': ['#0-#4,#6-#7'], 'exclude': ['L0', 'L2', 'L7']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L1', 'L3', 'L4', 'L6'])

    def test_layer_filtering_with_spaces_in_labels(self):
        labels = ['L0 test', 'L1 test 2', 'L2 test 3', 'L3', 'L4', 'L5', 'L6 last', 'L7']
        filters = {'include': ['#0-#4,#6-#7'], 'exclude': ['L0 test', 'L2 test 3', 'L7']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L1 test 2', 'L3', 'L4', 'L6 last'])

    def test_layer_filtering_with_special_characters(self):
        labels = ['L0', 'L1', 'L,2', 'L3', '#1-#2\\name#1-#4', 'L5']
        filters = {'include': ['#0-#2','#1-#2\\name#1-#4'], 'exclude': ['L1']}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L,2', '#1-#2\\name#1-#4'])

    def test_layer_filtering_error_condition(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings',
                  'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'L12 msg:reply']
        filters = {"include": ["#0-#6"], "exclude": ["L5 msg:greetings"]}
        layers = inklayers.StringParser.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6'])


# Tests the inclusion of a number into a list of intervals
    def _test_number(self, n, intervals, condition):
        with self.subTest("%d in %s" + str((n, str(intervals)))):
            isin = inklayers.StringParser.is_number_in_intervals(n, intervals)
            self.assertEqual(isin, condition)

    def test_number_inclusion_1_single_value(self):
        intervals = [(50, 50)]
        self._test_number(49, intervals, False)
        self._test_number(50, intervals, True)
        self._test_number(51, intervals, False)

    def test_number_inclusion_1_interval(self):
        intervals = [(20, 90)]
        # lower value
        self._test_number(19, intervals, False)
        self._test_number(20, intervals, True)
        self._test_number(21, intervals, True)
        # upper value
        self._test_number(89, intervals, True)
        self._test_number(90, intervals, True)
        self._test_number(91, intervals, False)

    def test_number_inclusion_3_single_values(self):
        intervals = [(40, 40), (50, 50), (60, 60)]
        # first interval
        self._test_number(39, intervals, False)
        self._test_number(40, intervals, True)
        self._test_number(41, intervals, False)
        # second interval
        self._test_number(49, intervals, False)
        self._test_number(50, intervals, True)
        self._test_number(51, intervals, False)
        # third interval
        self._test_number(59, intervals, False)
        self._test_number(60, intervals, True)
        self._test_number(61, intervals, False)

    def test_number_inclusion_3_intervals(self):
        intervals = [(20, 30), (40, 50), (60, 70)]
        # first interval
        self._test_number(19, intervals, False)
        self._test_number(20, intervals, True)
        self._test_number(30, intervals, True)
        self._test_number(31, intervals, False)
        # second interval
        self._test_number(39, intervals, False)
        self._test_number(40, intervals, True)
        self._test_number(50, intervals, True)
        self._test_number(51, intervals, False)
        # third interval
        self._test_number(59, intervals, False)
        self._test_number(60, intervals, True)
        self._test_number(70, intervals, True)
        self._test_number(71, intervals, False)

    def test_filter_slide_layer_data(self):
        layers = '#0-#2,L4'
        results = inklayers.StringParser.filter_slide_data(layers)
        self.assertEqual(results, ['#0-#2', 'L4'])
        layers = '#0-#2,L4,This is a name\, ok?,L5,L6'
        results = inklayers.StringParser.filter_slide_data(layers)
        self.assertEqual(results, ['#0-#2', 'L4', 'This is a name, ok?', 'L5', 'L6'])
        layers = 'L1,L2,Name\\with backslash,L5'
        results = inklayers.StringParser.filter_slide_data(layers)
        self.assertEqual(results, ['L1', 'L2', 'Name\\with backslash', 'L5'])


class TestSlideConfiguration(unittest.TestCase):

    args = {}
    slideConf = inklayers.SlideConfiguration(svg_file, config, args)

    def test_load_element_from_config(self):
        infile = self.slideConf.load_element(config, 'input', 'filename')
        self.assertEqual(infile, 'fishes.svg')

    def test_load_element_from_config_error(self):
        with self.assertRaisesRegexp(Exception, 'Config file format error: input -> filename2 not found.'):
            self.slideConf.load_element(config, 'input', 'filename2')

    #def test_load_slides(self):
    #    slides = inklayers.SlideConfiguration.load_element(self.slideConf, config, 'output', 'slides')
    #    inklayers.SlideConfiguration.load_slides(self.slideConf, slides)
    #    self.assertEqual(inklayers.SlideConfiguration.slides, 'fishes.svg')

    def test_check_unique_slide_names(self):
        # Correct, no exception
        slides = [{'name': 'slide1'}, {'name': 'slide2'}]
        self.slideConf.check_unique_slide_names(slides)
        slides = [{'name': 'slide1'}, {'name': 'slide1'}, {}]
        with self.assertRaisesRegexp(Exception, 'Error in slide configuration: two slides with the same name found.'):
            self.slideConf.check_unique_slide_names(slides)

    def test_filter_layers(self):
        filter = ['L0', 'L1']
        layers = ['L1', 'L2']
        # add a layer
        self.slideConf.filter_layers(filter, 'add', layers)
        self.assertEqual(layers, ['L1', 'L2', 'L0'])
        # exclude a layer
        filter = ['L0']
        self.slideConf.filter_layers(filter, 'exclude', layers)
        self.assertEqual(layers, ['L1', 'L2'])

    def test_stacked_slides(self):
        slides = self.slideConf.load_stacked_slides()
        self.assertEqual(slides, [{'include': ['L0']}, {'include': ['L0', 'L1']}, {'include': ['L0', 'L1', 'L2']}, {'include': ['L0', 'L1', 'L2', 'L3']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6', 'L7']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6', 'L7', 'L8']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6', 'L7', 'L8', 'L9']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6', 'L7', 'L8', 'L9', 'L10']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11']}, {'include': ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'L12 msg:reply']}])

    def test_slide_specific_setting(self):
        # Arguments: global setting, config file setting, single slide setting
        # If a global setting is not specified, the slide specific setting is used (if there is one)
        slide = {"include": ["L0"], "type": 'png'}
        setting = self.slideConf.get_slide_specific_setting(slide, None, 'pdf', 'type')
        self.assertEqual(setting, 'png')
        # The global setting overrides the specific setting
        setting = self.slideConf.get_slide_specific_setting(slide, 'jpg', 'pdf', 'type')
        self.assertEqual(setting, 'jpg')
        # Without a global setting and a specific setting, the config file setting is used instead.
        slide = {"include": ["L0"]}
        setting = self.slideConf.get_slide_specific_setting(slide, None, 'pdf', 'type')
        self.assertEqual(setting, 'pdf')
        # The global setting is used
        setting = self.slideConf.get_slide_specific_setting(slide, 'png', 'pdf', 'type')
        self.assertEqual(setting, 'png')

    def test_layers_of_a_slide(self):
        slideToMake = {"include": ["#0-#6"], "exclude": ["L5 msg:greetings"]}
        slideMade = self.slideConf.make_slide(slideToMake)
        layers = slideMade.get_labels()
        self.assertEqual(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6'])

    def test_layers_of_an_empty_slide(self):
        slideToMake = {}
        slideMade = self.slideConf.make_slide(slideToMake)
        layers = slideMade.get_labels()
        self.assertEqual(layers, [])



class TestSlideConfiguration2(unittest.TestCase):

    infile_path, infile = fileHandler.get_path_and_fullname('fishes2.json')
    svg, conf = fileHandler.load_input_file(infile)

    def test_based_on_slide_single(self):
        # Testing the 'moon' slide:
        # {"name": "night sky", "include": ["#0-#6"], "exclude": ["L5 msg:greetings"]},
        # {"name": "moon", "based-on": "night sky", "include": ["#7"]},
        slideC = inklayers.SlideConfiguration(self.svg, self.conf, {})
        layers = slideC.slides[7].get_labels()
        self.assertEquals(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6', 'L7'])

    def test_based_on_slide_multiple(self):
        # Testing the '1star' slide:
        # {"name": "night sky", "include": ["#0-#6"], "exclude": ["L5 msg:greetings"]},
        # {"name": "moon", "based-on": "night sky", "include": ["#7"]},
        # {"name": "1star", "based-on": "moon", "include": ["#8"]},
        slideC = inklayers.SlideConfiguration(self.svg, self.conf, {})
        layers = slideC.slides[8].get_labels()
        self.assertEquals(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6', 'L7', 'L8'])

    def test_slide_with_global_filters(self):
        # Testing the '1star' slide (excluding L1 and adding L9)
        # {"name": "night sky", "include": ["#0-#6"], "exclude": ["L5 msg:greetings"]},
        # {"name": "moon", "based-on": "night sky", "include": ["#7"]},
        # {"name": "1star", "based-on": "moon", "include": ["#8"]},
        slideC = inklayers.SlideConfiguration(self.svg, self.conf, {'exclude': ['L1'], 'add': ['L9']})
        layers = slideC.slides[8].get_labels()
        self.assertEquals(layers, ['L0', 'L2', 'L3', 'L4', 'L6', 'L7', 'L8', 'L9'])




class TestSystem(unittest.TestCase):

    infile_path, infile = fileHandler.get_path_and_fullname('fishes.json')
    svg, conf = fileHandler.load_input_file(infile)

    def test_query(self):
        args = {'infiles': ['fishes.json'], 'inkscape': 'Default', 'exclude': ['L0'], 'stack': False,
                'outfile': None, 'type': 'png', 'split': False, 'outfolder': None, 'add': None, 'extra': ' ',
                'latex': False, 'verbosity': 0, 'debug': True}
        sys = inklayers.InklayersShell(args)
        lines = sys.report_layers_info(self.svg)
        self.assertEquals(lines, ["#0: 'L0'", "#1: 'L1'", "#2: 'L2'", "#3: 'L3'", "#4: 'L4'",
                 "#5: 'L5 msg:greetings'", "#6: 'L6'", "#7: 'L7'", "#8: 'L8'",
                 "#9: 'L9'", "#10: 'L10'", "#11: 'L11'", "#12: 'L12 msg:reply'"])

    def test_extension_layer_parameters_no_filtering(self):
        # tests slide 11 of fishes.svg (using fishes.json as configuration)
        # default layers: ['L0', 'L1', 'L2', 'L3', 'L4', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11']
        class ParserSimulator():
            pass
        options = ParserSimulator()
        options.configFile = self.infile
        options.typeExp = 'None'
        options.namefmtExp = 'None'
        options.addLayers = ''
        options.excludeLayers = ''
        sys = inklayersExt.InklayersExtension(options, self.svg.tree)
        sys.process_input_file(sys.args.get('infiles'))
        layers = []
        for slide in sys.slideConf.slides:
            if slide.id == 11:
                layers = slide.get_labels()
        self.assertEquals(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11'])

    def test_extension_layer_parameters_with_filtering(self):
        # tests slide 11 of fishes.svg (using fishes.json as configuration)
        class ParserSimulator():
            pass
        options = ParserSimulator()
        options.configFile = self.infile
        options.typeExp = 'None'
        options.namefmtExp = 'None'
        options.addLayers = '#2-#4,L5 msg:greetings,L12 msg:reply'    # add an interval and two individual layers
        options.excludeLayers = '#0-#2,L7,L9'                         # exclude an interval and two additional layers
        sys = inklayersExt.InklayersExtension(options, self.svg.tree)
        sys.process_input_file(sys.args.get('infiles'))
        layers = []
        for slide in sys.slideConf.slides:
            #print(slide.get_labels())
            if slide.id == 11:
                layers = slide.get_labels()
        # default layers: ['L0', 'L1', 'L2', 'L3', 'L4', 'L6', 'L7', 'L8', 'L9', 'L10', 'L11']
        # add layers: 2,3,4,5,12
        # exclude layers: 0,1,2,7,9  (exclusion is done afterwards, so #2 is removed)
        self.assertEquals(layers, ['L3', 'L4', 'L6', 'L8', 'L10', 'L11', 'L5 msg:greetings', 'L12 msg:reply'])


if __name__ == '__main__':
    unittest.main()
