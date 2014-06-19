#
# matchers.py
#
# Some standard matchers for use with the MatchController.
# 

import gbif_api
import csv

# The root class of all Matchers, plus some logic for generating the right
# subclass.
class Matcher:
    def name(self):
        raise NotImplementedError("Matcher subclass did not implement name!")
    
    def ready(self):
        raise NotImplementedError("Matcher subclass did not implement ready!")

    def match(self, scname):
        raise NotImplementedError("Matcher subclass did not implement match!")

    def build(config, name): 
        if not "matcher:" + name in config:
            return NullMatcher(name)
        else:
            section = config["matcher:" + name]
            if "gbif_id" in section:
                return GBIFMatcher(name, section['gbif_id'], section)
            elif "file" in section:
                return FileMatcher(name, section['file'], section)
            else:
                return NullMatcher(name)

    def Null(name):
        return NullMatcher(name)

# For testing: a NullMatcher doesn't match anything.
class NullMatcher(Matcher):
    def __init__(self, name):
        self.name = name

    def name(self):
        return self.name

    def ready(self):
        return

    def match(self, scname):
        return None

    def __str__(self):
        return self.name + "*"

# Match this name against GBIF.
class GBIFMatcher(Matcher):
    def __init__(self, name, gbif_id, options):
        if 'name' in options:
            self.name = options['name']
        else:
            self.name = name
        self.gbif_id = gbif_id
        self.options = options

    def name(self):
        return self.name

    def ready(self):
        return

    def match(self, scname):
        matches = gbif_api.get_matches(scname, self.gbif_id)

        if len(matches) == 0:
            return None

        result = matches[0]

        return MatchResult(
            scname,
            result['scientificName'],
            gbif_api.get_url_for_id(result['key']),
            result['accepted'] if 'accepted' in result else "",
            "(GBIF:{}) {}".format(self.name,
                result['publishedIn'] + " " +
                result['datasetKey']
            )
        )

    def __str__(self):
        return self.name + " (GB)"

# Look up this name in a file.
class FileMatcher(Matcher):
    def __init__(self, name, filename, options):
        if 'name' in options:
            self.name = options['name']
        else:
            self.name = name
        self.filename = filename
        self.options = options

        self.namecol = "scientificName"
        if 'column_name' in options:
            self.namecol = options['column_name']

        self.dialect = csv.excel
        if 'dialect' in options:
            self.dialect = csv.get_dialect(options['dialect'])

        self.names = None

    def dialect(self):
        return self.dialect

    def fieldnames(self):
        if self.names == None:
            self.match("Felis tigris")
            return self.fieldnames
        else:
            return self.fieldnames

    def name(self):
        return self.name

    def ready(self):
        return

    def match(self, query_scname):
        if self.names == None:
            self.names = dict()

            csvfile = open(self.filename, "r")
            reader = csv.DictReader(csvfile, dialect=self.dialect)
            self.fieldnames = reader.fieldnames

            row_index = 0
            for row in reader:
                row_index += 1

                scname = row[self.namecol]

                if scname == None:
                    raise RuntimeError('No column "{0:s}" on row {1:d}'.format(
                        self.namecol, row_index
                    ))
                elif scname in self.names:
                    raise RuntimeError('Duplicate scientificName detected: "{0:s}"'.format(scname))
                else:
                    row['_row_index'] = row_index
                    self.names[scname] = row

            csvfile.close()

        if query_scname in self.names:
            row = self.names[query_scname]

            return MatchResult(
                query_scname,
                self.filename + "#" + str(row['_row_index']),
                query_scname,
                row['acceptedName'] if ('acceptedName' in row) else "",
                self.name
            )
        else:
            return MatchResult.Empty()

    def __str__(self):
        return self.name + " (" + self.filename + ")"

# The result of a match. Wraps a bunch of properties of a match.
class MatchResult:
    def __init__(self, query, name_id, matched_name, accepted_name, source):
        self.query = query
        self.name_id = name_id
        self.matched_name = matched_name
        self.accepted_name = accepted_name
        self.source = source

    def __str__(self):
        return "MatchResult(query='{}', matched=[id='{}', name='{}', accepted='{}'], source='{}')".format(
            self.query,
            self.name_id,
            self.matched_name,
            self.accepted_name,
            self.source
        )

    def Empty():
        return None 

