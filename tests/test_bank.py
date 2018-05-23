#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for bank statement reader
author: Jon Morris
date: May 2018
"""

from __future__ import print_function
import os
import shutil
import tempfile
import unittest
import uuid
import pandas
from pandas.util.testing import assert_frame_equal
import bank

ROWS = [[u'1/1/16', u'A', u'Item 1', 1.00, 1.00],
        [u'16/1/16', u'A', u'Item 2', 2.50, 3.50],
        [u'10/3/16', u'A', u'Item 3', 2.00, 5.50],
        [u'10/11/16', u'B', u'Item 4', -2.00, 3.50]]


class BankTest(unittest.TestCase):
    """Tests for bank application"""
    @classmethod
    def setUpClass(cls):
        cls.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        cls.csv_in = os.path.join(cls.data_dir, 'statement.csv')
        cls.xls_in = os.path.join(cls.data_dir, 'statement.xlsx')

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def shortDescription(cls):
        """Hide docstrings from nose"""
        pass

    def setUp(self):
        self.out_dir = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        os.mkdir(self.out_dir)

    def tearDown(self):
        try:
            shutil.rmtree(self.out_dir)
        except OSError:
            pass


    def test_read_csv(self):
        """Read a simple csv file"""
        expected = pandas.DataFrame(ROWS, columns=bank.COLUMN_NAMES)

        actual = bank.read_from_csv(self.csv_in)

        assert_frame_equal(actual, expected)

    def test_write_csv(self):
        """Write a simple dataframe to csv"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        data = [[1, 2, 3]]
        df = pandas.DataFrame(data, columns=['A', 'B', 'C'])
        expected = 'A,B,C\n1,2,3\n'

        bank.write_to_csv(df, outfile)

        with open(outfile, 'rb') as fcsv:
            actual = fcsv.read()
            self.assertEqual(actual, expected)

    def test_append_csv(self):
        """Add a dataframe to an existing csv file"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        data = [[1, 2, 3]]
        df = pandas.DataFrame(data, columns=['A', 'B', 'C'])
        expected = 'A,B,C\n1,2,3\n1,2,3\n'

        bank.write_to_csv(df, outfile)
        bank.write_to_csv(df, outfile)

        with open(outfile, 'rb') as fcsv:
            actual = fcsv.read()
            self.assertEqual(actual, expected)

    def test_import_file_bad_filetype(self):
        """Try to import a file of the wrong type"""
        filename = 'test.pdf'

        with self.assertRaises(ValueError):
            bank.import_file(filename)

    def test_import_file_csv_string(self):
        """Import a simple csv file with a string argument"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        expected = pandas.DataFrame(ROWS, columns=bank.COLUMN_NAMES)

        bank.import_file(self.csv_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        assert_frame_equal(actual, expected)

    def test_import_file_csv_array(self):
        """Import a simple csv file with an array argument"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        expected = pandas.DataFrame(ROWS, columns=bank.COLUMN_NAMES)

        bank.import_file([self.csv_in], output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        assert_frame_equal(actual, expected)

    def test_read_excel(self):
        """Read a simple Excel file"""
        expected = pandas.DataFrame(ROWS, columns=bank.COLUMN_NAMES)
        expected['Date'] = pandas.to_datetime(expected['Date'], dayfirst=True)

        actual = bank.read_from_excel(self.xls_in)

        assert_frame_equal(actual, expected)

    @unittest.skip('not implemented')
    def test_import_file_excel(self):
        pass

    def test_cleanup_column_names(self):
        """Check column names are cleaned up properly"""
        df_dirty = pandas.DataFrame([], columns=[u'Merchant', u'Balance (£)',
                                                 u'Other  ', u'Unnamed'])
        df_clean = pandas.DataFrame([], columns=[u'Description', u'Balance', u'Other'])

        bank.cleanup_column_names(df_dirty)

        assert_frame_equal(df_clean, df_dirty)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(BankTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
