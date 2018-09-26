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
from numpy import nan
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

        self.test_df = pandas.DataFrame(ROWS, columns=bank.COLUMN_NAMES)
        self.test_df['Date'] = pandas.to_datetime(self.test_df['Date'], dayfirst=True)

    def tearDown(self):
        try:
            shutil.rmtree(self.out_dir)
        except OSError:
            pass

    def assertEqual(self, first, second, msg=None):
        """Override to avoid pylint no-self-use error"""
        if isinstance(first, pandas.DataFrame) and isinstance(second, pandas.DataFrame):
            assert_frame_equal(first, second)
        else:
            super(BankTest, self).assertEqual(first, second, msg)

    def test_read_csv(self):
        """Read a simple csv file"""
        expected = self.test_df

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

    def test_append_csv_remove_duplicates(self):
        """Add a dataframe to an existing csv file"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        data = [[1, 2, 3]]
        df = pandas.DataFrame(data, columns=['A', 'B', 'C'])
        expected = 'A,B,C\n1,2,3\n'

        bank.write_to_csv(df, outfile, remove_duplicates=True)
        bank.write_to_csv(df, outfile, remove_duplicates=True)

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
        expected = self.test_df

        bank.import_file(self.csv_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True)
        self.assertEqual(actual, expected)

    def test_import_file_csv_array(self):
        """Import a simple csv file with an array argument"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        expected = self.test_df

        bank.import_file([self.csv_in], output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True)
        self.assertEqual(actual, expected)

    def test_read_excel(self):
        """Read a simple Excel file"""
        expected = self.test_df

        actual = bank.read_from_excel(self.xls_in)

        self.assertEqual(actual, expected)

    def test_import_file_excel(self):
        """Import a simple excel file with a string argument"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        expected = self.test_df

        bank.import_file(self.xls_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8', parse_dates=[0], dayfirst=True)
        self.assertEqual(actual, expected)

    def test_cleanup_column_names(self):
        """Check column names are cleaned up properly"""
        df_dirty = pandas.DataFrame([], columns=[u'Merchant', u'Balance (£)',
                                                 u'Other  ', u'Unnamed'])
        df_clean = pandas.DataFrame([], columns=[u'Description', u'Balance', u'Other'])

        bank.cleanup_columns(df_dirty)

        self.assertEqual(df_clean, df_dirty)

    def test_show_statement(self):
        """Import a simple csv file with a string argument"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        expected = self.test_df

        bank.show_statement(self.csv_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True)
        self.assertEqual(actual, expected)

    def test_show_statement_date_range(self):
        """Import a simple csv file with a string argument"""
        outfile = os.path.join(self.out_dir, 'test.csv')
        expected = pandas.DataFrame([ROWS[2]], columns=bank.COLUMN_NAMES)
        expected['Date'] = pandas.to_datetime(expected['Date'], dayfirst=True)

        bank.show_statement(self.csv_in, date_from="1/3/16", date_to="30/4/16", output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True)
        self.assertEqual(actual, expected)

    def test_set_balance_debit(self):
        """Find the column containing 'D' and set the balance column of that row to be negative"""
        actual = pandas.DataFrame([[1, 2, 'D', 3]], columns=['a', 'Balance', 'c', 'd'])
        expected = pandas.DataFrame([[1, -2, 'D', 3]], columns=['a', 'Balance', 'c', 'd'])

        bank.cleanup_columns(actual)

        self.assertEqual(actual, expected)

    def test_set_balance_debit_not_found(self):
        """No columns containing just 'C' or 'D', so balance should be unchanged"""
        data = [
            [1, 2, nan, 3],
            [1, 2, 'D', 3],
            [1, 2, 'D', 3],
            [1, 2, 'E', 3],
        ]
        actual = pandas.DataFrame(data, columns=['a', 'Balance', 'c', 'd'])
        expected = pandas.DataFrame(data, columns=['a', 'Balance', 'c', 'd'])

        bank.cleanup_columns(actual)

        self.assertEqual(actual, expected)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(BankTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
