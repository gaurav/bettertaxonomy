#!/usr/bin/env python

import argparse
import datetime
import gbif_api
import csv
import sys

# Read the command line.
cmdline = argparse.ArgumentParser(description = 'Match species names')
cmdline.add_argument('input', 
    nargs='*', 
    type=argparse.FileType('r'),
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

# Load the entire internal list, if it exists.
internal_corrections = dict()
ic_fieldnames = None
if args.internal:
    reader = csv.DictReader(open(args.internal, "r"), dialect=csv.excel)
    ic_fieldnames = reader.fieldnames
    row_index = 0
    for row in reader:
        row_index+=1
        scname = row['scientificName']
        if scname == None:
            raise RuntimeError('No scientific name on row {0:d}'.format(row_index))
        elif scname in internal_corrections:
            raise RuntimeError('Duplicate scientificName detected: "{0:d}"'.format(scname))
        else:
            internal_corrections[scname] = row

# Read list of names and match them.
# TODO: add a cache for duplicate names.

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
        print "Error: could not find field '{0:s}' in file".format(args.fieldname)
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
        if name in internal_corrections:
            matched_scname = internal_corrections[name].get('correctName')
            matched_acname = internal_corrections[name].get('correctAcceptedName')
            matched_url = "//internal"
            matched_source = "internal (as of " + timestamp + ")"

            count_internal+=1
        else:
            # Try Mammal Species of the World.
            matches = gbif_api.get_matches(name, '672aca30-f1b5-43d3-8a2b-c1606125fa1b')
            if len(matches) > 0:
                # print matches[0];
                matched_scname = matches[0]['scientificName']
                if 'accepted' in matches[0].keys():
                    matched_acname = matches[0]['accepted']
                matched_url = gbif_api.get_url_for_id(matches[0]['nubKey'])
                matched_source = ("GBIF API queried for Mammal Species "
                    "of the World ('672aca30-f1b5-43d3-8a2b-c1606125fa1b') on " +
                    timestamp)

                count_msw+=1
            else: 
                # Try TaxRefine.
                matches = gbif_api.get_matches_from_taxrefine(name)
                if len(matches) > 0:
                    # print matches[0]
                    matched_scname = matches[0]['summary']['scientificName']
                    if 'accepted' in matches[0]['summary'].keys():
                        matched_acname = matches[0]['summary']['accepted']
                    matched_url = gbif_api.get_url_for_id(matches[0]['id'])
                    matched_source = "TaxRefine/GBIF API queried on " + timestamp

                    count_taxrefine+=1
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
        for k,v in row.items():
            # print k
            if v is not None:
                row[k] = v.encode('utf8')
        output.writerow(row)
        row_count+=1

if args.internal and len(unmatched_names) > 0:
    internal_file = open(args.internal, mode="a")
    writer = csv.DictWriter(internal_file, ic_fieldnames, dialect=csv.excel)
    
    dict_row = dict()
    for colname in ic_fieldnames:
        dict_row[colname] = None

    for name in unmatched_names:
        dict_row['scientificName'] = name
        writer.writerow(dict_row)

    internal_file.close()

# Report.
filenames = []
for file in args.input:
    filenames.append(file.name)

sys.stderr.write("""
 - Processed on %s on file(s) %s
 - Rows with names processed: %d
 - Names matched against the internal database: %d (%.2f%%)
 - Names matched against Mammal Species of the World: %d (%.2f%%)
 - Names matched against TaxRefine: %d (%.2f%%)
 - Names that could not be matched against any checklist: %d (%.2f%%)
""" % (
    timestamp,
    ', '.join(filenames),
    row_count,
    count_internal, (float(count_internal)/row_count * 100),
    count_msw, (float(count_msw)/row_count * 100),
    count_taxrefine, (float(count_taxrefine)/row_count * 100),
    count_unmatched, (float(count_unmatched)/row_count * 100),
))
