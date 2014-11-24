#!/usr/bin/env python3
#
# bettertaxonomy.py - matching multiple taxonomic sources
# 
# Better Taxonomy is a script for matching multiple taxonomic sources: 
# it can match names from a CSV file against other CSV files, against
# GBIF checklists, and against TaxRefine. It also manages an internal
# list, that is automatically updated with names that could not be 
# matched. Use sources.example.ini to create a configuration file.
# 
# Find out more at https://github.com/gaurav/bettertaxonomy
# 

import argparse
import datetime
import csv
import sys
import codecs

import matchcontroller
import matchers

#
# INITIALIZATION
#

# Start a timer.
time_start = datetime.datetime.now()

# Store a single timestamp for all operations.
timestamp = datetime.datetime.now().strftime("%x")

# Read and parse the command line.
cmdline = argparse.ArgumentParser(description = 'Match taxonomic names')

cmdline.add_argument('input', 
    nargs='?',
    help = 'A CSV or plain text file containing taxonomic names. Defaults to stdin.')

cmdline.add_argument('-fieldname',
    type=str,
    help='The field containing scientific names to match',
    default = 'scientificName')

cmdline.add_argument('-config',
    type=str,
    help='Configuration file (see sources.example.ini for an example)')

cmdline.add_argument('-internal',
    nargs='?',
    type=str,
    help='Internal list of name corrections (must be a CSV file)')

args = cmdline.parse_args()

# Set up the input stream.
input = None
if args.input is None:
    #sys.stdin = codecs.getreader("utf-8")(sys.stdin)
    input = sys.stdin
else:
    #input = codecs.open(args.input, "r", "utf-8")
    input = open(args.input, "r")

# Load the config file.
config_file = args.config
if config_file is None:
    config_file = "sources.example.ini"

matchcontrol = matchcontroller.parseSources(config_file)

sys.stderr.write("Configuration loaded from {:s}, {:d} match lists configured:\n\t{:s}".format(
    config_file, len(matchcontrol), str(matchcontrol)
))

# Load the internal list.
if args.internal is None:
    internal_list = matchers.NullMatcher("internal")
else:
    internal_list = matchers.FileMatcher("internal", args.internal, dict(
        dialect = "excel"
    ))
    internal_fieldname = internal_list.column_name()

#
# READ INPUT FILE
# 

# All three counts here are by row, not unique names.
row_count = 0
match_count = 0
unmatched_count = 0
match_count_by_matcher = dict()

# Store names that could not be matched.
unmatched = []

# Figure out the file type of the input file.
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

# Create new columns in the output file to store:
# - matched_scname: The name that was matched in the database.
# - matched_acname: The accepted name as reported by the database.
# - matched_url: A URL to this entry in the database.
# - matched_source: The source as reported by the database.
output_header = header[:]
output_header.insert(output_header.index(args.fieldname) + 1, 'matched_scname')
output_header.insert(output_header.index(args.fieldname) + 2, 'matched_acname')
output_header.insert(output_header.index(args.fieldname) + 3, 'matched_url')
output_header.insert(output_header.index(args.fieldname) + 4, 'matched_source')

# Create a csv.writer for writing this file to output.
output = csv.DictWriter(sys.stdout, output_header, dialect)
output.writeheader()

#
# MATCH ROWS
#

for row in reader:
    # Find the scientific name.
    name = row[args.fieldname].strip()

    # Initialize matched names.
    matched_scname = None
    matched_acname = None
    matched_url = None
    matched_source = None

    # Step 1. Use the MatchController generated from the configuration file.
    match = matchcontrol.match(name, row)
    if match is not None:
        # Match!
        match_count += 1

        matched_scname = match.matched_name
        matched_acname = match.accepted_name
        matched_url = match.name_id
        matched_source = match.source
        matched_matcher = match.matcher

        # Store count by matcher.
        matcher_name = str(match.matcher)
        if matcher_name in match_count_by_matcher:
            match_count_by_matcher[matcher_name] += 1
        else:
            match_count_by_matcher[matcher_name] = 1

    else:
        # Step 2. Match against the internal file.
        match = internal_list.match(name)

        if match is not None:
            # Match!
            match_count += 1

            matched_scname = match.matched_name
            matched_acname = match.accepted_name
            matched_url = match.name_id
            matched_source = match.source
            matched_matcher = match.matcher

            # Store count by matcher.
            if "internal" in match_count_by_matcher:
                match_count_by_matcher["internal"] += 1
            else:
                match_count_by_matcher["internal"] = 1            

        else:
            # Step 3. No match found. Store it for later.
            unmatched.append(name)
            unmatched_count += 1

    # scname and acname might be dicts, with (key: key_count) pairs.
    if type(matched_scname) == dict:
        matched_scname = sorted(matched_scname, key=matched_scname.get)[0]
    if type(matched_acname) == dict:
        matched_acname = sorted(matched_acname, key=matched_acname.get)[0]

    # Add details to the row we're writing out.
    try:
        row['matched_scname'] = matched_scname.encode("utf-8") if matched_scname is not None else ""
        row['matched_acname'] = matched_acname.encode("utf-8") if matched_acname is not None else ""
        row['matched_url'] = matched_url.encode("utf-8") if matched_url is not None else ""
        row['matched_source'] = matched_source.encode("utf-8") if matched_source is not None else ""
    except UnicodeDecodeError as e:
        raise RuntimeError("Could not decode unicode name from source " + matched_source.encode('utf-8') + ": " + str(e))

    # Write out the row.
    output.writerow(row)
    row_count+=1

#
# ADD UNMATCHED NAMES TO INTERNAL LIST
# 

if args.internal and len(unmatched) > 0:
    fieldnames = internal_list.fieldnames

    # Open the internal file in append mode, and a DictWriter to
    # write to it. Use the headers from loading this file earlier.
    internal_file = open(args.internal, mode="a")
    writer = csv.DictWriter(internal_file, fieldnames, dialect=csv.excel)
    
    # Create new row with all the other columns.
    row = dict()
    for colname in fieldnames:
        row[colname] = None

    # For each name, replace the name in the row and
    # write it out.
    for name in unmatched:
        row[internal_fieldname] = name.encode("utf-8") if name is not None else ""
        writer.writerow(row)

    internal_file.close()

#
# REPORT ON THE RESULTS
#

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

# Write report.
sys.stderr.write("""
 - Processed on %s on file %s in %s time.
 - Rows with names processed: %d (%.5f rows/second, %.5f seconds/row)
 - %d names (%.2f%%) were matched against the following sources:
%s
 - Names that could not be matched against any checklist: %d (%.2f%%)
""" % (
    timestamp,
    input.name,
    str(time_taken),
    row_count, 
        ((float(row_count)/time_taken.total_seconds())),
        1/((float(row_count)/time_taken.total_seconds())),
    match_count, ((float(match_count)/row_count * 100)),
    "\n".join(match_summary),
    unmatched_count, (float(unmatched_count)/row_count * 100),
))
