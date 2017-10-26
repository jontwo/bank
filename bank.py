#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse
import fnmatch
import os
import pandas
import six

column_names = [u'Date', u'Type', u'Description', u'Amount', u'Balance']


def read_from_excel(filepath, names=None, count=None):
    out_df = pandas.DataFrame(columns=column_names)
    xl = pandas.ExcelFile(filepath)
    namelist = names or xl.sheet_names
    if count:
        namelist = namelist[:count]
    # TODO names from wildcard
    for sht in namelist:
        skip = 0
        while True:
            df = xl.parse(sht, skiprows=skip)
            unnamed = [n for n in df.columns if isinstance(n, six.string_types) and 'Unnamed' in n]
            if len(unnamed) < len(df.columns) / 2.0:
                # continue if less than half of columns are unnamed
                break
            skip += 1
            if skip > 10:
                # this is just a saga now
                df = xl.parse(sht)
                break

        # cleanup column names
        for c in df.columns:
            if 'Unnamed' in c:
                del df[c]
        df.rename(columns={u'Balance (£)': u'Balance'}, inplace=True)
        df.rename(columns={u'Paid out': u'Amount'}, inplace=True)
        df.columns = [c.strip() for c in df.columns]

        out_df = out_df.append(df)
    return out_df


def read_from_csv(filepath):
    return pandas.read_csv(filepath, skipinitialspace=True, skip_blank_lines=True,
                           encoding='utf-8')


def write_to_csv(df, filepath):
    if os.path.exists(filepath):
        # add df to existing data
        data = []
        data.append(read_from_csv(filepath))
        data.append(df)
        out_df = pandas.concat(data)
        out_df.to_csv(filepath, encoding='utf-8', index=False)
    else:
        # just write df
        df.to_csv(filepath, encoding='utf-8', index=False)


def import_file(args):
    ac = None
    if isinstance(args.file, six.string_types):
        filelist = [args.file]
    else:
        filelist = args.file
    for filename in filelist:
        if fnmatch.fnmatch(os.path.splitext(filename)[1].lower(), '*.csv'):
            print('importing from csv file...')
        elif fnmatch.fnmatch(os.path.splitext(filename)[1].lower(), '*.xls*'):
            print('importing from excel file...')
            ac = read_from_excel(filename, names=args.sheet_names, count=args.sheet_count)
        else:
            raise ValueError('import file type {} not supported'.format(filename))

    if ac is None or len(ac) == 0:
        return

    if args.output_file:
        write_to_csv(ac, args.output_file)
    else:
        print(ac)


def show_statement(args):
    print('show statement')
    print(args)


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

    parser.add_argument('file', nargs='+', help='csv file(s) to be read')
    parser.add_argument('--output_file', '-o', help='output file name. outputs to '
                        'stdout if not given.')
    parser.add_argument('--time_period', '-t', help='time period to show')
    parser.add_argument('--sheet_names', '-n', nargs='+', help='list of spreadsheet names '
                        'to be read')
    parser.add_argument('--sheet_count', type=int, help='number of sheets to be read from excel file')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    if args.import_file:
        import_file(args)
    elif args.show_statement:
        show_statement(args)
    elif args.calc_outgoings:
        calc_outgoings(args)
