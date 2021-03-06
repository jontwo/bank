#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import fnmatch
import os
import pandas
import re
import six
from datetime import datetime
from dateutil.parser import parse as parse_date
from xlrd.biffh import XLRDError

COLUMN_NAMES = ['Date', 'Type', 'Description', 'Amount', 'Balance']
COLUMN_TYPES = {
    'Date': datetime,
    'Transaction Date': datetime,
    'Type': str,
    'Description': str,
    'Merchant': str,
    'Merchant/Description': str,
    'Amount': float,
    'Balance': float,
    'Balance (£)': float,
    'Debit/Credit': float,
    'Paid out': float,
    'Paid in': float,
    'Billing Amount': float
}
ALIASES = [
    {'Merchant': 'Description'},
    {'Merchant/Description': 'Description'},
    {'Balance (£)': 'Balance'},
    {'Debit/Credit': 'Balance'},
    {'Paid out': 'Amount'},
    {'Billing Amount': 'Amount'},
    {'Transaction Date': 'Date'},
]
YEARFIRST = re.compile(r'^\d{4}')

__all__ = ['ALIASES', 'COLUMN_NAMES', 'COLUMN_TYPES', 'calc_outgoings', 'cleanup_columns',
           'import_file', 'main', 'read_from_csv', 'read_from_excel', 'show_statement',
           'validate', 'write_to_csv']


def cleanup_columns(df):
    # cleanup names
    df.columns = [c.strip() for c in df.columns]
    df.columns = df.columns.str.title()
    for alias in ALIASES:
        df.rename(columns=alias, inplace=True)

    for col in df.columns:
        if df[col].dtype == object or df[col].dtype == str:
            df[col] = df[col].str.strip()

        try:
            if COLUMN_TYPES[col] == float:
                df[col] = pandas.to_numeric(df[col], errors='coerce')
        except KeyError:
            # unknown column name
            pass

        # TODO try and cast column type here
        # vals = df.loc[df[col] == 'D', 'Balance'].str.replace('[^\d\.]','').astype(float)
        try:
            # check if column only contains D or C (debit/credit)
            if df[col].notnull().any() and df[col][df[col].notnull()].isin(['D', 'C']).all():
                # set debit balances to negative
                df.loc[df[col] == 'D', 'Balance'] = -df.loc[df[col] == 'D', 'Balance']
        except (ValueError, KeyError):
            # probably not string type column
            pass

        # remove unnamed columns
        if 'Unnamed' in col:
            del df[col]

    # if there is a 'Paid in', add negative to 'Amount'
    if 'Paid in' in df.columns:
        df.loc[df['Paid in'].notnull(), 'Amount'] = -df.loc[df['Paid in'].notnull(), 'Paid in']
        del df['Paid in']

    # set date column to date type (if found)
    try:
        df['Date'] = pandas.to_datetime(df['Date'], dayfirst=True).dt.date
    except (KeyError, ValueError):
        print('WARNING: Could not parse date column.')


def read_from_excel(filepath, names=None, count=None):
    out_df = pandas.DataFrame(columns=COLUMN_NAMES)
    xl = pandas.ExcelFile(filepath)
    namelist = names or xl.sheet_names
    if count:
        namelist = namelist[:count]
    for sht in namelist:
        print('Reading sheet {}...'.format(sht))
        skip = 0
        while True:
            try:
                df = xl.parse(sht, skiprows=skip, converters=COLUMN_TYPES)
            except XLRDError:
                print('ERROR: sheet not found')
                continue
            except TypeError:
                # try without type converters
                df = xl.parse(sht, skiprows=skip)

            unnamed = [
                n for n in df.columns if isinstance(n, six.string_types) and 'Unnamed' in n
            ]
            if len(unnamed) < len(df.columns) / 2.0:
                # continue if less than half of columns are unnamed
                break
            skip += 1
            if skip > 10:
                # this is just a saga now
                df = xl.parse(sht)
                break

        cleanup_columns(df)
        print('cleaned', df.head())
        out_df = out_df.append(df)
        print('appended', out_df.head())

    # TODO stop it changing column order
    return out_df


def read_from_csv(filepath):
    df = pandas.read_csv(filepath, skipinitialspace=True, skip_blank_lines=True, encoding='utf-8')
    cleanup_columns(df)
    return df


def write_to_csv(df, filepath, remove_duplicates=False, check_columns=True, continue_on_err=False):
    if os.path.exists(filepath):
        # add df to existing data
        df_existing = read_from_csv(filepath)
        if check_columns and not df_existing.columns.str.lower().sort_values().equals(
                df.columns.str.lower().sort_values()):
            print('WARNING: column names do not match')
            print('Existing columns: {}'.format(df_existing.columns))
            print('New columns: {}'.format(df.columns))
            if not continue_on_err:
                return
            # TODO look for mapping if different
            # warn if mapping not found
        data = [df_existing, df]
        out_df = pandas.concat(data, sort=True)
        if remove_duplicates:
            out_df.drop_duplicates(inplace=True)
        out_df.to_csv(filepath, encoding='utf-8', index=False)
    else:
        # just write df
        df.to_csv(filepath, encoding='utf-8', index=False)


def validate(df, continue_on_err=False):
    missing = set(COLUMN_NAMES).difference(set(df.columns))
    if missing:
        print("ERROR: File does not have the following columns: {}".format(missing))
        if not continue_on_err:
            return False

    # check no months missing between start and end
    actual_months = df['Date'].apply(lambda d: d.strftime('%Y-%m')).tolist()
    month_range = pandas.date_range(df['Date'].min(), df['Date'].max(),
                                    freq=pandas.DateOffset(months=1))
    expected_months = [m.strftime('%Y-%m') for m in month_range.tolist()]
    missing = sorted(set(expected_months).difference(set(actual_months)))

    for month in missing:
        print("No entries found in {}".format(month))

    return not missing

    # check balance is correct on each row
    # TODO this needs to handle multiple transactions on the same day
    # (balance is NaN except for the last one)
    # new_balance = df['Balance'].shift()
    # if pandas.isnull(new_balance[0]):
    #     new_balance[0] = 0
    #
    # mask = (df['Amount'] + new_balance) == df['Balance']
    # if not mask.all():
    #     print("Invalid balance(s):")
    # for i in range(len(df[~mask])):
    #     print(pandas.concat([df[~mask].iloc[[i]], df[~mask].iloc[[i]]]))
    #
    # return not(missing or df[~mask])


def import_file(filepath, sheet_names=None, sheet_count=None, output_file=None, unique=False):
    ac = None
    if isinstance(filepath, six.string_types):
        filelist = [filepath]
    else:
        filelist = filepath
    for filename in filelist:
        if fnmatch.fnmatch(os.path.splitext(filename)[1].lower(), '*.csv'):
            print('importing from csv file...')
            ac = read_from_csv(filename)
        elif fnmatch.fnmatch(os.path.splitext(filename)[1].lower(), '*.xls*'):
            print('importing from excel file...')
            ac = read_from_excel(filename, names=sheet_names, count=sheet_count)
        else:
            raise ValueError('import file type {} not supported'.format(filename))

    if ac is None or ac.empty:
        return

    if output_file:
        write_to_csv(ac, output_file, remove_duplicates=unique)
    else:
        print(ac)


def show_statement(filename, date_from=None, date_to=None, date_only=False, output_file=None):
    print('showing statement for ', filename)
    ac = read_from_csv(filename)

    if date_only:
        print('date range:')
        print(ac['Date'].min().strftime('%d %B %Y'))
        print(ac['Date'].max().strftime('%d %B %Y'))
        return

    try:
        if date_from:
            ac = ac.loc[ac['Date'] >= parse_date(date_from,
                                                 dayfirst=not YEARFIRST.match(date_from)).date()]
        if date_to:
            ac = ac.loc[ac['Date'] <= parse_date(date_to,
                                                 dayfirst=not YEARFIRST.match(date_to)).date()]
    except TypeError as exc:
        print('WARNING: Could not set date range.', exc.message)

    if output_file:
        write_to_csv(ac, output_file)
    else:
        for col in ac.columns:
            if col not in COLUMN_NAMES:
                del ac[col]
        ac.sort_values('Date', inplace=True)
        pandas.set_option('display.max_rows', None)
        print(ac)


def calc_outgoings(args):
    print('calc outgoings')
    print(args)


def parse_args():
    parser = argparse.ArgumentParser(description='Bank account statement manager')
    commands = parser.add_mutually_exclusive_group(required=True)
    commands.add_argument('--import_file', '-i', action='store_true',
                          help='Read and reformat a bank statement ')
    commands.add_argument('--calc_outgoings', '-c', action='store_true',
                          help='Calculate outgoings and summarise by type')
    commands.add_argument('--show_statement', '-s', action='store_true',
                          help='Show statement for the given time period')
    commands.add_argument('--validate', '-v', action='store_true',
                          help='Validate csv file')

    parser.add_argument('file', nargs='+', help='csv file(s) to be read')
    parser.add_argument('--output_file', '-o',
                        help='output file name. outputs to stdout if not given.')
    parser.add_argument('--date_from', '-f', help='show records on or after this date')
    parser.add_argument('--date_to', '-t', help='show records on or before this date')
    parser.add_argument('--sheet_names', '-n', nargs='+',
                        help='list of spreadsheet names to be read')
    parser.add_argument('--sheet_count', type=int,
                        help='number of sheets to be read from excel file')
    parser.add_argument('--unique', action='store_true',
                        help='do not add existing rows when importing. unique records only')
    parser.add_argument('--date_only', action='store_true',
                        help='only show date range when showing statement')
    parser.add_argument('--continue_on_error', action='store_true',
                        help='show a warning and continue if there is an error')
    return parser.parse_args()


def main():
    args = parse_args()
    if args.import_file:
        import_file(args.file, sheet_names=args.sheet_names, sheet_count=args.sheet_count,
                    output_file=args.output_file, unique=args.unique)
    elif args.show_statement:
        show_statement(args.file[0], date_from=args.date_from, date_to=args.date_to,
                       date_only=args.date_only, output_file=args.output_file)
    elif args.calc_outgoings:
        calc_outgoings(args)
    elif args.validate:
        for fn in args.file:
            validate(read_from_csv(fn), all_errors=args.continue_on_error)


if __name__ == '__main__':
    main()
