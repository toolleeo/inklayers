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

if __name__ == '__main__':
    unittest.main()
