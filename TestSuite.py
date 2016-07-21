import unittest
# import logging
# import json
from lxml import etree
import inklayers

__author__ = 'Tullio Facchinetti'


test_drawing_file = 'fishes.svg'


class TestSuite(unittest.TestCase):
    def test_split_correct_filename(self):
        (basename, extension) = inklayers.split_filename('test.svg')
        self.assertEqual(basename, 'test')
        self.assertEqual(extension, 'svg')

    def test_label_collection(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings',
                  'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'L12 msg:reply']
        with open(test_drawing_file) as f:
            tree = etree.parse(f)
            o = inklayers.get_layer_objects(tree)
            l = [inklayers.get_label(x) for x in o]
            self.assertEqual(labels, l)

    def test_query_output(self):
        lines = ["#0: 'L0'", "#1: 'L1'", "#2: 'L2'", "#3: 'L3'", "#4: 'L4'",
                 "#5: 'L5 msg:greetings'", "#6: 'L6'", "#7: 'L7'", "#8: 'L8'",
                 "#9: 'L9'", "#10: 'L10'", "#11: 'L11'", "#12: 'L12 msg:reply'"]
        l = inklayers.report_layers_info(test_drawing_file)
        self.assertEqual(lines, l)

    # Tests for the filename specification format

    def test_get_filename_no_formatters(self):
        fdata = inklayers.get_filename('test.svg')
        self.assertEqual(fdata, 'test.svg')

    def test_get_filename_with_basename(self):
        fdata = inklayers.get_filename('%b.svg', basename='test')
        self.assertEqual(fdata, 'test.svg')

    def test_get_filename_with_extension(self):
        fdata = inklayers.get_filename('test.%e', extension='svg')
        self.assertEqual(fdata, 'test.svg')

    def test_get_filename_with_index(self):
        fdata = inklayers.get_filename('test-%n.svg', index=100)
        self.assertEqual(fdata, 'test-100.svg')

    def test_get_filename_with_all_formatters(self):
        fdata = inklayers.get_filename('%b-%n.%e', basename='test', extension='svg', index=100)
        self.assertEqual(fdata, 'test-100.svg')

    # Tests for the interval specification format

    def test_parse_interval_string_one_value(self):
        intervals = inklayers.parse_interval_string(' #0 ')
        self.assertEqual(intervals, [(0, 0)])

    def test_parse_interval_string_one_interval(self):
        intervals = inklayers.parse_interval_string(' #0 - #10 ')
        self.assertEqual(intervals, [(0, 10)])

    def test_parse_interval_string_two_values(self):
        intervals = inklayers.parse_interval_string(' #0, #10 ')
        self.assertEqual(intervals, [(0, 0), (10, 10)])

    def test_parse_interval_string_two_intervals(self):
        intervals = inklayers.parse_interval_string(' #0 - #10 , #100 - #200 ')
        self.assertEqual(intervals, [(0, 10), (100, 200)])

    def test_parse_interval_string_two_values_two_intervals(self):
        intervals = inklayers.parse_interval_string('#0,#5-#10,#15,#20-#30')
        self.assertEqual(intervals, [(0, 0), (5, 10), (15, 15), (20, 30)])

    def test_parse_interval_string_wrong_format_1(self):
        intervals = inklayers.parse_interval_string('0')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_2(self):
        intervals = inklayers.parse_interval_string('#0-1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_3(self):
        intervals = inklayers.parse_interval_string('#0,1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_4(self):
        intervals = inklayers.parse_interval_string('#0-#1-#2')
        self.assertEqual(intervals, None)

    # This test works now ( previously it expected: [(1, 1)] )
    def test_parse_interval_string_wrong_format_5(self):
        intervals = inklayers.parse_interval_string('L1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_6(self):
        intervals = inklayers.parse_interval_string('L#1')
        self.assertEqual(intervals, None)

    def test_parse_interval_string_wrong_format_7(self):
        intervals = inklayers.parse_interval_string('#L1')
        self.assertEqual(intervals, None)


    # Tests for the inclusion/exclusion of layers in one slide

    def test_layer_filtering_no_inclusion(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4']
        filters = {'exclude': ['L2']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, [])

    def test_layer_filtering_no_exclusion(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4']
        filters = {'include': ['L0', 'L2']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L2'])

    # this test works now (previously it expected: ['L3', 'quarto']
    def test_layer_filtering_inclusion_of_labels_with_numbers(self):
        labels = ['primo', 'secondo', 'L3', 'quarto', 'quinto']
        filters = {'include': ['L3']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L3'])

    def test_layer_filtering_inclusion_of_labels_with_numbers2(self):
        labels = ['primo', 'secondo', 'L3', 'quarto', 'quinto']
        filters = {'include': ['L3', 'quinto']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L3', 'quinto'])

    def test_layer_filtering_included_1_interval_exclude_1_label(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4']
        filters = {'include': ['#0-#4'], 'exclude': ['L2']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L1', 'L3', 'L4'])

    def test_layer_filtering_included_2_intervals_exclude_3_labels(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L7']
        filters = {'include': ['#0-#4,#6-#7'], 'exclude': ['L0', 'L2', 'L7']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L1', 'L3', 'L4', 'L6'])

    def test_layer_filtering_with_spaces_in_labels(self):
        labels = ['L0 test', 'L1 test 2', 'L2 test 3', 'L3', 'L4', 'L5', 'L6 last', 'L7']
        filters = {'include': ['#0-#4,#6-#7'], 'exclude': ['L0 test', 'L2 test 3', 'L7']}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L1 test 2', 'L3', 'L4', 'L6 last'])

    def test_layer_filtering_error_condition(self):
        labels = ['L0', 'L1', 'L2', 'L3', 'L4', 'L5 msg:greetings',
                  'L6', 'L7', 'L8', 'L9', 'L10', 'L11', 'L12 msg:reply']
        filters = {"include": ["#0-#6"], "exclude": ["L5 msg:greetings"]}
        layers = inklayers.get_filtered_layer_labels(labels, filters)
        self.assertEqual(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6'])


    # Tests the inclusion of a number into a list of intervals

    def _test_number(self, n, intervals, condition):
        with self.subTest("%d in %s" + str((n, str(intervals)))):
            isin = inklayers.is_number_in_intervals(n, intervals)
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


    # Tests the loading of information from config files
    def test_load_info_from_config(self):
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            key1 = 'input'
            key2 = 'filename'
            ret = inklayers.load_info_from_config(conf, key1, key2)
            self.assertEqual(ret, 'fishes.svg')

    def test_load_info_from_config_error(self):
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            key1 = 'inpu'
            key2 = 'filename'
            self.assertRaises(Exception, inklayers.load_info_from_config, conf, key1, key2)

    # Tests the loading of settings that can be overriden by command line parameters
    def test_overridable_setting(self):
        type = 'png' # type specified in command line
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            dest_type = inklayers.get_overridable_setting(type, conf, 'output', 'type')
            self.assertEqual(dest_type, 'png')

    def test_overridable_setting_no_overriding(self):
        type = None  # nothing specified in command line
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            dest_type = inklayers.get_overridable_setting(type, conf, 'output', 'type')
            self.assertEqual(dest_type, 'pdf')

    def test_overridable_setting_wrong_keys(self):
        type = None
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            self.assertRaises(Exception, inklayers.get_overridable_setting, type, conf, 'input', 'type')

    # Tests the loading of slide specific settings (a different file type for example)
    def test_slide_specific_setting(self):
        slide = {"include": ["L0"], "type": 'png'}
        key = 'type'
        global_type = 'pdf'
        setting = inklayers.get_slide_specific_setting(slide, key, global_type)
        self.assertEqual(setting, 'png')

    def test_slide_specific_setting_missing(self):
        slide = {"include": ["L0"]}
        key = 'type'
        global_type = 'pdf'
        setting = inklayers.get_slide_specific_setting(slide, key, global_type)
        self.assertEqual(setting, global_type)

    # Tests the retrieval of layers from a slide
    def test_get_layers_from_slide(self):
        slide = {"include": ["#0-#6"], "exclude": ["L5 msg:greetings"]}
        with open('fishes.svg') as f:
            tree = etree.parse(f)
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        layers = inklayers.get_layers_from_slide(slide, slides, tree)
        self.assertEqual(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6'])

    def test_get_layers_from_empty_slide(self):
        slide = {}
        with open('fishes.svg') as f:
            tree = etree.parse(f)
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        layers = inklayers.get_layers_from_slide(slide, slides, tree)
        self.assertEqual(layers, [])

    def test_get_layers_from_slide_with_wrong_layers(self):
        slide = {"include": ["#20-#26"]}
        with open('fishes.svg') as f:
            tree = etree.parse(f)
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        layers = inklayers.get_layers_from_slide(slide, slides, tree)
        self.assertEqual(layers, [])

    def test_unique_slide_names(self):
        slides = [
            {"name": "day sky", "include": ["L0", "L1"]},
            {"name": "sun", "include": ["#0-#2"]},
            {"name": "red fish", "include": ["#0-#3"]},
            {"name": "both fishes", "include": ["#0-#4"]},
            {"name": "day chat", "include": ["#0-#5"]}]
        ret = inklayers.check_unique_slide_names(slides)
        self.assertEqual(ret, None)

    def test_unique_slide_names_failed(self):
        slides = [
            {"name": "day sky", "include": ["L0", "L1"]},
            {"name": "sun", "include": ["#0-#2"]},
            {"name": "sun", "include": ["#0-#3"]},
            {"name": "both fishes", "include": ["#0-#4"]},
            {"name": "day chat", "include": ["#0-#5"]}]
        self.assertRaises(Exception, inklayers.check_unique_slide_names, slides)

    # Tests the based-on option
    def test_based_on_none(self):
        slide = {"include": ["L0"]}
        with open('fishes.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        inc = []
        exc = []
        counter = slides.__len__()
        s = inklayers.check_based_on(slide, slides, inc, exc, counter)
        self.assertEqual(s, slide)

    def test_based_on_one(self):
        slide = {"name": "moon", "based-on": "night sky", "include": ["#7"]}
        with open('fishes2.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        inc = []
        exc = []
        counter = slides.__len__()
        s = inklayers.check_based_on(slide, slides, inc, exc, counter)
        self.assertEqual(s, {"name": "night sky", "include": ["#0-#6"], "exclude": ["L5 msg:greetings"]})

    def test_based_on_one_error_self(self):
        slide = {"name": "moon", "based-on": "moon", "include": ["#7"]}
        slides = [
			{"name": "day chat", "include": ["#0-#5"]},
			{"name": "night sky", "include": ["#0-#6"], "exclude": ["L5 msg:greetings"]},
			{"name": "moon", "based-on": "moon", "include": ["#7"]}]
        inc = []
        exc = []
        counter = slides.__len__()
        self.assertRaises(Exception, inklayers.check_based_on, slide, slides, inc, exc, counter)

    def test_based_on_one_error_loop(self):
        slide = {"name": "moon", "based-on": "night sky", "include": ["#7"]}
        slides = [
			{"name": "day chat", "include": ["#0-#5"]},
			{"name": "night sky", "based-on": "moon", "include": ["#0-#6"], "exclude": ["L5 msg:greetings"]},
			{"name": "moon", "based-on": "night sky", "include": ["#7"]}]
        inc = []
        exc = []
        counter = slides.__len__()
        self.assertRaises(Exception, inklayers.check_based_on, slide, slides, inc, exc, counter)

    def test_based_on_multiple(self):
        slide = {"name": "1star", "based-on": "moon", "include": ["#8"]}
        with open('fishes2.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        inc = []
        exc = []
        counter = slides.__len__()
        s = inklayers.check_based_on(slide, slides, inc, exc, counter)
        self.assertEqual(s, {'include': ['#0-#6'], 'exclude': ['L5 msg:greetings'], 'name': 'night sky'})

    def test_get_layers_from_slide_with_based_on(self):
        slide = {"name": "1star", "based-on": "moon", "include": ["#8"]}
        with open('fishes.svg') as f:
            tree = etree.parse(f)
        with open('fishes2.json') as config_file:
            conf = inklayers.json.load(config_file)
            slides = inklayers.load_info_from_config(conf, 'output', 'slides')
        layers = inklayers.get_layers_from_slide(slide, slides, tree)
        self.assertEqual(layers, ['L0', 'L1', 'L2', 'L3', 'L4', 'L6', 'L7', 'L8'])

    # checks the filtering of the current slide due to command line parameters
    def test_filter_layers_by_command_line_parameters_include(self):
        layers = ['L3', 'Layer_a', 'LB', 'LC', 'LZ'] # the layers of the current slide
        action = 'add'
        layers_fil = ['L5'] # this is obtained by get_filtered_layer_labels() already tested above
        if action == 'add':
            for x in layers_fil:
                if x not in layers:
                    layers.append(x)
        self.assertEqual(layers, ['L3', 'Layer_a', 'LB', 'LC', 'LZ', 'L5'])

    def test_filter_layers_by_command_line_parameters_exclude(self):
        layers = ['L3', 'Layer_a', 'LB', 'LC', 'LZ']
        action = 'exclude'
        layers_fil = ['LB', 'L9']
        if action == 'exclude':
            for x in layers_fil:
                if x in layers:
                    layers.remove(x)
        self.assertEqual(layers, ['L3', 'Layer_a', 'LC', 'LZ'])





if __name__ == '__main__':
    unittest.main()
