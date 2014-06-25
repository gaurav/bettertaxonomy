#!/usr/bin/env python3

import argparse
import codecs
import datetime
import csv
import sys

import matchcontroller
import matchers
import gbif_api

# Start a timer.
time_start = datetime.datetime.now()

# timestamp: a single timestamp for all operations 
timestamp = datetime.datetime.now().strftime("%x")

# Read the command line.
cmdline = argparse.ArgumentParser(description = 'Match species names')

cmdline.add_argument('-config',
    type=str,
    help='Configuration file (see sources.example.ini for an example)')

cmdline.add_argument('input', 
    type=argparse.FileType(mode='r', encoding='utf-8'),
    help='A CSV or plain text file containing species names',
    default = [sys.stdin])

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

# Load the internal list.
if args.internal is None:
    internal_list = matchers.NullMatcher("internal")
else:
    internal_list = matchers.FileMatcher("internal", args.internal, dict(
        dialect = "excel"
    ))

# All three counts here are by row, not unique names.
row_count = 0
match_count = 0
unmatched_count = 0
match_count_by_matcher = dict()
unmatched = []

# Figure out the file type of the input file.
input = args.input

try:
    # Try to sniff the file format.
    dialect = csv.Sniffer().sniff(input.read(1024), delimiters="\t,;|")
    input.seek(0)
    reader = csv.DictReader(input, dialect=dialect)
    header = reader.fieldnames

except csv.Error as e:
    # If the sniff fails, read it as a tab-delimited file ("csv.excel_tab")
    input.seek(0)
    header = [input.readline().rstrip()]
    dialect = csv.excel_tab
    reader = csv.DictReader(input, dialect=dialect, fieldnames=header)

# Check that the fieldname exists.
if header.count(args.fieldname) == 0:
    sys.stderr.write("Error: could not find field '{}' in file\n".format(args.fieldname))
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
        match_count += 1

        matched_scname = match.matched_name
        matched_acname = match.accepted_name
        matched_url = match.name_id
        matched_source = match.source
        matched_matcher = match.matcher

        if match.matcher in match_count_by_matcher:
            match_count_by_matcher[match.matcher] += 1
        else:
            match_count_by_matcher[match.matcher] = 1

    else:
        match = internal_list.match(name)

        if match is not None:
            match_count += 1

            matched_scname = match.matched_name
            matched_acname = match.accepted_name
            matched_url = match.name_id
            matched_source = match.source
            matched_matcher = match.matcher

            if "internal" in match_count_by_matcher:
                match_count_by_matcher["internal"] += 1
            else:
                match_count_by_matcher["internal"] = 1            

        else:
            unmatched.append(name)
            unmatched_count += 1

    # scname and acname might be dicts, with (key: key_count) pairs.
    if type(matched_scname) == dict:
        matched_scname = sorted(matched_scname, key=matched_scname.get)[0]
    if type(matched_acname) == dict:
        matched_acname = sorted(matched_acname, key=matched_acname.get)[0]

    # Add details to the row we're writing out.
    row['matched_scname'] = matched_scname
    row['matched_acname'] = matched_acname
    row['matched_url'] = matched_url
    row['matched_source'] = matched_source

    # print "Row to write: " + str(row)
    output.writerow(row)
    row_count+=1

# All unmatched names should be added to the internal_list.
if args.internal and len(unmatched) > 0:
    fieldnames = internal_list.fieldnames

    internal_file = open(args.internal, mode="a")
    writer = csv.DictWriter(internal_file, fieldnames, dialect=csv.excel)
    
    dict_row = dict()
    for colname in fieldnames:
        dict_row[colname] = None

    for name in unmatched:
        dict_row['scientificName'] = name
        writer.writerow(dict_row)

    internal_file.close()

# Report.
time_taken = (datetime.datetime.now() - time_start)

# Summarize sources.
match_summary = []

for matcher in match_count_by_matcher:
    match_summary.append("\t{:s}: {:d} ({:.2f}%)".format(
        str(matcher),
        match_count_by_matcher[matcher],
        float(match_count_by_matcher[matcher])/match_count * 100
    ))
match_summary.sort()

sys.stderr.write("""
 - Processed on %s on file %s in %s time.
 - Rows with names processed: %d (%.5f rows/second, %.5f seconds/row)
 - %d names (%.2f%%) were matched against the following sources:
%s
 - Names that could not be matched against any checklist: %d (%.2f%%)
""" % (
    timestamp,
    args.input.name,
    str(time_taken),
    row_count, 
        ((float(row_count)/time_taken.total_seconds())),
        1/((float(row_count)/time_taken.total_seconds())),
    match_count, ((float(match_count)/row_count * 100)),
    "\n".join(match_summary),
    unmatched_count, (float(unmatched_count)/row_count * 100),
))
