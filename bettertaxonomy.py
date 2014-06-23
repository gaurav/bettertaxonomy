#!/usr/bin/env python3

import argparse
import codecs
import datetime
import csv
import sys

import matchcontroller
import matchers # TODO remove
import gbif_api

# Start a timer.
time_start = datetime.datetime.now()

# Read the command line.
cmdline = argparse.ArgumentParser(description = 'Match species names')
cmdline.add_argument('-config',
    type=str,
    help='Configuration file (see sources.example.txt for an example)')
cmdline.add_argument('input', 
    nargs='*', 
    type=argparse.FileType(mode='r', encoding='utf-8'),
    help='A CSV or plain text file containing species names',
    default = [sys.stdin])
# TODO: Add support for multiple fieldnames.
cmdline.add_argument('-fieldname',
    type=str,
    help='The field containing scientific names to match',
    default = 'scientificName')
cmdline.add_argument('-internal',
    nargs='?',
    type=str,
    help='Internal list of name corrections (must be a CSV file)')

args = cmdline.parse_args()

# Load the config file.
config_file = args.config
if config_file is None:
    config_file = "sources.example.ini"

matchcontrol = matchcontroller.parseSources(config_file)

sys.stderr.write("Configuration loaded from {:s}, {:d} match lists configured.\n".format(
    config_file, len(matchcontrol)
))

# Load the entire internal list, if it exists.
internal_list = matchers.FileMatcher("internal_list", args.internal, dict(
    dialect = "excel"
))

# timestamp: a single timestamp for all operations.
timestamp = datetime.datetime.now().strftime("%x")

# unmatched_names: a list of names that could not be matched.
unmatched_names = []

row_count = 0

count_internal = 0
count_msw = 0
count_taxrefine = 0
count_unmatched = 0

for input in args.input:
    # Try to Sniff the CSV type; otherwise, assume it's a plain-text
    # tab-delimited file (excel_tab).
    try:
        dialect = csv.Sniffer().sniff(input.read(1024), delimiters="\t,;|")
        input.seek(0)
        # print "Dialect identified: " + str(dialect)
        reader = csv.DictReader(input, dialect=dialect)
        # print "Reader object: " + str(reader)
        header = reader.fieldnames
    except csv.Error as e:
        input.seek(0)
        header = [input.readline().rstrip()]
        dialect = csv.excel_tab
        reader = csv.DictReader(input, dialect=dialect, fieldnames=header)

    # By this point, we have a dialect, an input, and a reader.
 
    # Check for a field with names.
    if header.count(args.fieldname) == 0:
        # print "Error: could not find field '{}' in file".format(args.fieldname)
        print("Error: could not find field '{}' in file".format(args.fieldname))
        exit(1)
    
    # Create new columns for output:
    # - matched_scname: The name that was matched in the database.
    # - matched_acname: The accepted name as reported by the database.
    # - matched_url: A URL to this entry in the database.
    # - matched_source: The source as reported by the database.
    output_header = header[:]
    output_header.insert(output_header.index(args.fieldname) + 1, 'matched_scname')
    output_header.insert(output_header.index(args.fieldname) + 2, 'matched_acname')
    output_header.insert(output_header.index(args.fieldname) + 3, 'matched_url')
    output_header.insert(output_header.index(args.fieldname) + 4, 'matched_source')
   
    # Create a csv.writer for rewriting this file to output.
    # sys.stdout = codecs.getwriter(sys.stdout.encoding)(sys.stdout)
    output = csv.DictWriter(sys.stdout, output_header, dialect)
    output.writeheader()

    # Match rows. For now, try three databases: internal, GBIF:MSW, and TaxRefine.
    for row in reader:
        # print "To start with: " + str(row)
        name = row[args.fieldname]

        matched_scname = None
        matched_acname = None
        matched_url = None
        matched_source = None

        # Process the internal corrections.
        match = matchcontrol.match(name, row)
        if match is not None:
            matched_scname = match.matched_name
            matched_acname = match.accepted_name
            matched_url = match.name_id
            matched_source = match.source

            count_internal+=1
        else:
            unmatched_names.append(name)

            count_unmatched+=1

        # scname and acname might be dicts, with (key: key_count) pairs.
        if type(matched_scname) == dict:
            matched_scname = sorted(matched_scname, key=matched_scname.get)[0]
        if type(matched_acname) == dict:
            matched_acname = sorted(matched_acname, key=matched_acname.get)[0]

        row['matched_scname'] = matched_scname
        row['matched_acname'] = matched_acname
        row['matched_url'] = matched_url
        row['matched_source'] = matched_source

        # print "Row to write: " + str(row)
        output.writerow(row)
        row_count+=1

# TODO: switch this to use the 'internal' file from the config, or
# to use our 'internal' in the config, or something.
if args.internal and len(unmatched_names) > 0:
    fieldnames = internal_list.fieldnames()

    internal_file = open(args.internal, mode="a")
    writer = csv.DictWriter(internal_file, fieldnames, dialect=csv.excel)
    
    dict_row = dict()
    for colname in fieldnames:
        dict_row[colname] = None

    for name in unmatched_names:
        dict_row['scientificName'] = name
        writer.writerow(dict_row)

    internal_file.close()

# Report.
time_taken = (datetime.datetime.now() - time_start)

filenames = []
for file in args.input:
    filenames.append(file.name)

sys.stderr.write("""
 - Processed on %s on file(s) %s in %s time:
 - Rows with names processed: %d (%.5f/second)
 - Names matched against the internal database: %d (%.2f%%)
 - Names matched against Mammal Species of the World: %d (%.2f%%)
 - Names matched against TaxRefine: %d (%.2f%%)
 - Names that could not be matched against any checklist: %d (%.2f%%)
""" % (
    timestamp,
    ', '.join(filenames),
    str(time_taken),
    row_count, ((float(row_count)/time_taken.total_seconds())),
    count_internal, (float(count_internal)/row_count * 100),
    count_msw, (float(count_msw)/row_count * 100),
    count_taxrefine, (float(count_taxrefine)/row_count * 100),
    count_unmatched, (float(count_unmatched)/row_count * 100),
))
