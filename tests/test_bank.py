"""Unit tests for bank statement reader."""

import os
import re
from copy import deepcopy

import pandas
import pytest
import simplejson as json
from numpy import nan
from pandas.testing import assert_frame_equal

import bank

ROWS = [['1/1/16', 'A', 'Item 1', 1.00, 1.00],
        ['16/1/16', 'A', 'Item 2', 2.50, 3.50],
        ['10/3/16', 'A', 'Item 3', 2.00, 5.50],
        ['10/11/16', 'B', 'Item 4', -2.00, 3.50]]
CONFIG = {
    'categories': {'Item 1': 'Food', 'Item 2': 'Entertainment', 'Item 4': 'Entertainment',
                   'Item 5': 'Petrol'},
    'regexes': {},
    'version': ''
}
EMPTY_CONFIG = {'categories': {}, 'regexes': {}, 'version': ''}


class TestBank:
    """Tests for bank application"""
    @pytest.fixture
    def data_dir(self):
        return os.path.join(os.path.dirname(__file__), 'data')

    @pytest.fixture
    def csv_in(self, data_dir):
        return os.path.join(data_dir, 'statement.csv')

    @pytest.fixture
    def xls_in(self, data_dir):
        return os.path.join(data_dir, 'statement.xlsx')

    @pytest.fixture
    def in_df(self):
        df = pandas.DataFrame(ROWS, columns=bank.COLUMN_NAMES)
        df['Date'] = pandas.to_datetime(df['Date'], dayfirst=True).dt.date
        yield df

    @staticmethod
    def _get_config(path, contents):
        path = os.path.join(path, '.bankjson')
        with open(path, mode='w') as fp:
            json.dump(contents, fp)
        return path

    @pytest.fixture
    def config_path(self, tmp_path):
        return self._get_config(tmp_path, deepcopy(CONFIG))

    @pytest.fixture
    def empty_config_path(self, tmp_path):
        return self._get_config(tmp_path, deepcopy(EMPTY_CONFIG))

    @staticmethod
    def assert_file_equal(filepath, expected, msg=None):
        """Compares a file to expected text."""
        with open(filepath, mode='r', newline='') as fcsv:
            actual = fcsv.read()
            assert actual == expected, msg

    def test_read_csv(self, in_df, csv_in):
        """Read a simple csv file"""
        expected = in_df

        actual = bank.read_from_csv(csv_in)

        assert_frame_equal(actual, expected)

    def test_write_csv(self, tmp_path):
        """Write a simple dataframe to csv"""
        outfile = os.path.join(tmp_path, 'test.csv')
        data = [[1, 2, 3]]
        df = pandas.DataFrame(data, columns=['A', 'B', 'C'])
        expected = 'A,B,C\n1,2,3\n'

        bank.write_to_csv(df, outfile)

        self.assert_file_equal(outfile, expected)

    def test_append_csv(self, tmp_path):
        """Add a dataframe to an existing csv file"""
        outfile = os.path.join(tmp_path, 'test.csv')
        data = [[1, 2, 3]]
        df = pandas.DataFrame(data, columns=['A', 'B', 'C'])
        expected = 'A,B,C\n1,2,3\n1,2,3\n'

        bank.write_to_csv(df, outfile)
        bank.write_to_csv(df, outfile)

        self.assert_file_equal(outfile, expected)

    def test_append_csv__remove_duplicates(self, tmp_path):
        """Add a dataframe to an existing csv file"""
        outfile = os.path.join(tmp_path, 'test.csv')
        data = [[1, 2, 3]]
        df = pandas.DataFrame(data, columns=['A', 'B', 'C'])
        expected = 'A,B,C\n1,2,3\n'

        bank.write_to_csv(df, outfile, remove_duplicates=True)
        bank.write_to_csv(df, outfile, remove_duplicates=True)

        self.assert_file_equal(outfile, expected)

    def test_import_file__bad_filetype(self):
        """Try to import a file of the wrong type"""
        filename = 'test.pdf'

        with pytest.raises(ValueError, match="import file type test.pdf not supported"):
            bank.import_file(filename)

    def test_import_file__csv_string(self, tmp_path, in_df, csv_in):
        """Import a simple csv file with a string argument"""
        outfile = os.path.join(tmp_path, 'test.csv')
        expected = in_df

        bank.import_file(csv_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True).dt.date
        assert_frame_equal(actual, expected)

    def test_import_file__csv_array(self, tmp_path, in_df, csv_in):
        """Import a simple csv file with an array argument"""
        outfile = os.path.join(tmp_path, 'test.csv')
        expected = in_df

        bank.import_file([csv_in], output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True).dt.date
        assert_frame_equal(actual, expected)

    def test_read_excel(self, in_df, xls_in):
        """Read a simple Excel file"""
        expected = in_df

        actual = bank.read_from_excel(xls_in)

        assert_frame_equal(actual, expected)

    def test_import_file__excel(self, tmp_path, in_df, xls_in):
        """Import a simple excel file with a string argument"""
        outfile = os.path.join(tmp_path, 'test.csv')
        expected = in_df

        bank.import_file(xls_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True).dt.date
        assert_frame_equal(actual, expected)

    def test_cleanup_column_names(self):
        """Check column names are cleaned up properly"""
        df_dirty = pandas.DataFrame([], columns=['Merchant', 'Balance (£)',
                                                 'Other  ', 'Unnamed'])
        df_clean = pandas.DataFrame([], columns=['Description', 'Balance', 'Other'])
        # cleanup will change the datatype of this column
        df_clean['Balance'] = pandas.to_numeric(df_clean['Balance'], errors='coerce')

        bank.cleanup_columns(df_dirty)

        assert_frame_equal(df_clean, df_dirty)

    def test_show_statement(self, tmp_path, in_df, csv_in):
        """Show the complete statement from  a simple csv file"""
        outfile = os.path.join(tmp_path, 'test.csv')
        expected = in_df

        bank.show_statement(csv_in, output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True).dt.date
        assert_frame_equal(actual, expected)

    def test_show_statement__date_range(self, tmp_path, csv_in):
        """Show the statement within a date range from  a simple csv file"""
        outfile = os.path.join(tmp_path, 'test.csv')
        expected = pandas.DataFrame([ROWS[2]], columns=bank.COLUMN_NAMES)
        expected['Date'] = pandas.to_datetime(expected['Date'], dayfirst=True).dt.date

        bank.show_statement(csv_in, date_from="1/3/16", date_to="30/4/16", output_file=outfile)

        actual = pandas.read_csv(outfile, encoding='utf-8')
        actual['Date'] = pandas.to_datetime(actual['Date'], dayfirst=True).dt.date
        assert_frame_equal(actual, expected)

    def test_set_balance__debit(self):
        """Find the column containing 'D' and set the balance column of that row to be negative"""
        actual = pandas.DataFrame([[1, 2, 'D', 3]], columns=['a', 'Balance', 'c', 'd'])
        expected = pandas.DataFrame([[1, -2, 'D', 3]], columns=['A', 'Balance', 'C', 'D'])

        bank.cleanup_columns(actual)

        assert_frame_equal(actual, expected)

    def test_set_balance__debit__not_found(self):
        """No columns containing just 'C' or 'D', so balance should be unchanged"""
        data = [
            [1, 2, nan, 3],
            [1, 2, 'D', 3],
            [1, 2, 'D', 3],
            [1, 2, 'E', 3],
        ]
        actual = pandas.DataFrame(data, columns=['a', 'Balance', 'c', 'd'])
        expected = pandas.DataFrame(data, columns=['A', 'Balance', 'C', 'D'])

        bank.cleanup_columns(actual)

        assert_frame_equal(actual, expected)

    def test_validate__ok(self):
        """Validate a simple csv file"""
        rows = [['1/1/16', 'A', 'Item 1', 1.00, 1.00],
                ['31/1/16', 'A', 'Balance', '', 3.50],
                ['6/2/16', 'C', 'Item 2', 2.00, 5.50],
                ['1/3/16', 'A', 'Balance', '', 7.00],
                ['10/2/16', 'A', 'Item 5', 1.50, 7.00],
                ['15/1/16', 'A', 'Item 2', 2.50, 3.50],
                ['10/4/16', 'B', 'Item 4', -2.00, 5.00]]
        test_df = pandas.DataFrame(rows, columns=bank.COLUMN_NAMES)
        test_df['Date'] = pandas.to_datetime(test_df['Date'], dayfirst=True).dt.date

        assert bank.validate(test_df)

    def test_validate__bad_date(self, in_df):
        """Validate a csv file with months missing"""
        assert not bank.validate(in_df)

    @pytest.mark.skip("Not implemented")
    def test_validate__bad_balance(self):
        """Validate a simple csv file"""
        rows = [['1/1/16', 'A', 'Item 1', 1.00, 1.00],
                ['16/1/16', 'A', 'Item 2', 2.50, 3.50],
                ['10/2/16', 'A', 'Balance', '', 5.50],
                ['10/3/16', 'B', 'Item 4', -2.00, 3.50]]
        test_df = pandas.DataFrame(rows, columns=bank.COLUMN_NAMES)
        test_df['Date'] = pandas.to_datetime(test_df['Date'], dayfirst=True).dt.date

        assert not bank.validate(test_df)

    def test_calc_outgoings(self, config_path, csv_in, mocker, capsys):
        """Calculate the total outgoings for each category in the config"""
        exp_regex = re.compile(
            r'Total outgoings for 01 January 2016 to 10 November 2016 \(£\):\n'
            r'Entertainment\s+0.50\nFood\s+1.00\nOther\s+2.00$'
        )
        mocker.patch('bank.bank.CONFIG_PATH', config_path)
        bank.calc_outgoings(csv_in)

        captured = capsys.readouterr()
        assert captured.err == ""
        assert exp_regex.match(captured.out)

    def test_calc_outgoings__show_unknown(self, config_path, csv_in, mocker, capsys):
        """Calculate outgoings and show which items are not in the config"""
        expected = 'The following items do not have a category:\nItem 3\n'
        mocker.patch('bank.bank.CONFIG_PATH', config_path)
        bank.calc_outgoings(csv_in, show_unknown=True)

        captured = capsys.readouterr()
        assert captured.err == ""
        assert expected in captured.out

    def test_calc_outgoings__add_categories(self, empty_config_path, csv_in, mocker):
        """Calculate outgoings and add new items to the config"""
        # mock user input of two items
        mock_input = mocker.MagicMock(spec=input)
        mock_input.side_effect = ['Food', 'Entertainment', 'q']
        expected = {'categories': {'Item 1': 'Food', 'Item 2': 'Entertainment'},
                    'regexes': {},
                    'version': bank.__version__}

        mocker.patch('bank.bank.CONFIG_PATH', empty_config_path)
        mocker.patch('builtins.input', mock_input)
        bank.calc_outgoings(csv_in, add_categories=True)

        with open(empty_config_path) as fp:
            actual = json.load(fp)
        assert actual == expected

    def test_calc_outgoings__add_regex(self, empty_config_path, csv_in, mocker):
        """Calculate outgoings and add new regex to the config"""
        # mock user input of two items
        mock_input = mocker.MagicMock(spec=input)
        mock_input.side_effect = ['r', 'Item***', r'Item\s+\d+', 'Entertainment', 'q']
        expected = {'categories': {},
                    'regexes': {r'Item\s+\d+': 'Entertainment'},
                    'version': bank.__version__}

        mocker.patch('bank.bank.CONFIG_PATH', empty_config_path)
        mocker.patch('builtins.input', mock_input)
        bank.calc_outgoings(csv_in, add_categories=True)

        with open(empty_config_path) as fp:
            actual = json.load(fp)
        assert actual == expected

    def test_calc_outgoings__wildcards(self, csv_in, tmp_path, mocker, capsys):
        """Calculate outgoings with wildcards in the config"""
        exp_regex = re.compile(
            r'Total outgoings for 01 January 2016 to 10 November 2016 \(£\):\n'
            r'Stuff\s+3.50\nOther\s+0.00$'
        )
        config_path = self._get_config(tmp_path, {'categories': {},
                                                  'regexes': {"Item.*": "Stuff"},
                                                  'version': bank.__version__})
        mocker.patch('bank.bank.CONFIG_PATH', config_path)
        bank.calc_outgoings(csv_in)

        captured = capsys.readouterr()
        assert captured.err == ""
        assert exp_regex.match(captured.out)

    @pytest.mark.parametrize("regex, item, valid", [
        (r".*", "anything", True),
        (r"any.*", "anything", True),
        (r"\d+", "numbers", False),
        (r"\d+\s+num.*", "123\t\tnumbers", True),
        (r"++++", "invalid", False),
    ])
    def test_is_valid_regex(self, regex, item, valid, capsys):
        assert bank.is_valid_regex(regex, item) == valid
        captured = capsys.readouterr()
        assert bool(re.search(r"Regex.*not.*", captured.out)) != valid
