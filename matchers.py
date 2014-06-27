#
# matchers.py
#
# Some standard matchers for use with the MatchController.
# 

import sys

# The root class of all Matchers. Use Matcher.build(...) to create a new Matcher
# subclass for a given configuration.
class Matcher:
    # Every Matcher has a name.
    def name(self):
        raise NotImplementedError("Matcher subclass did not implement name!")
    
    # Every Matcher can be matched against a scientific name, returning either
    # a MatchResult or None.
    def match(self, scname):
        raise NotImplementedError("Matcher subclass did not implement match!")

    # Creates a configuration for a matcher with a particular name.
    #   - config: a dict() contains configuration options for this Matcher.
    #   - name: the name of this matcher.
    # 
    # Returns: a Matcher
    def build(config, name): 
        if not "matcher:" + name in config:
            raise RuntimeError("No matcher found in the configuration file for '{:s}'!".format(
                name
            ))
        else:
            # Picks a subclass to create based on the configuration provided.
            # Eventually, we might have a "type=gbif" as part of the config, but
            # for now we can just use the field names.
            section = config["matcher:" + name]
            if "gbif_id" in section:
                return GBIFMatcher(name, section['gbif_id'], section)
            elif "file" in section:
                return FileMatcher(name, section['file'], section)
            else:
                return NullMatcher(name)

# For testing: a NullMatcher is a Matcher that doesn't match anything.
class NullMatcher(Matcher):
    def __init__(self, name):
        self.name = name

    def name(self):
        return self.name

    def match(self, scname):
        return None

    def __str__(self):
        return self.name + "*"

# Models the result of a match. Wraps a bunch of properties of a match.
class MatchResult:
    # Creates a MatchResult. Requires:
    #   - matcher: The Matcher object used to match names.
    #   - query: The name being queried.
    #   - name_id: An identifier for this name. Must be a URI/URL.
    #   - matched_name: the matched name for this query. If this differs from
    #       'query', some fuzzy matching has taken place.
    #   - accepted_name: the accepted name for this query.
    #   - source: the source of this name.
    def __init__(self, matcher, query, name_id, matched_name, accepted_name, source):
        self.matcher = matcher
        self.query = query
        self.name_id = name_id
        self.matched_name = matched_name
        self.accepted_name = accepted_name
        self.source = source

    # Returns the MatchResult as a string.
    def __str__(self):
        return "MatchResult(matcher='{}', query='{}', matched=[id='{}', name='{}', accepted='{}'], source='{}')".format(
            self.matcher,
            self.query,
            self.name_id,
            self.matched_name,
            self.accepted_name,
            self.source
        )

    # An empty MatchResult is indistinguishable from None. Because it is None.
    def Empty():
        return None 


# Matches this name against GBIF 
import gbif_api

class GBIFMatcher(Matcher):
    # Creates an object given a GBIF ID and other options.
    # No other options are currently recognized.
    def __init__(self, name, gbif_id, options):
        if 'name' in options:
            self.name = options['name']
        else:
            self.name = name
        self.gbif_id = gbif_id
        self.options = options

    # Returns the name of this matcher, as used in the configuration file.
    def name(self):
        return self.name

    # Matches this name against GBIF.
    def match(self, scname):
        # Query GBIF.
        matches = gbif_api.get_matches(scname, self.gbif_id)

        # Pick the first match.
        if len(matches) == 0:
            return None
        result = matches[0]

        # Set up a publishedIn if GBIF provides this to us.
        published_in = result['publishedIn'] if 'publishedIn' in result else ""

        # Construct a MatchResult to return.
        result = MatchResult(
            self,
            scname,
            gbif_api.get_url_for_id(result['key']),
            result['scientificName'],
            result['accepted'] if 'accepted' in result else "",
            "(GBIF:{}) {}".format(self.name,
                published_in + " " +
                result['datasetKey']
            )
        )

        return result

    # Returns a string object; we use "(GB)" after the name given to us.
    def __str__(self):
        return self.name + " (GB)"

# Look up this name in a file.
import csv

class FileMatcher(Matcher):
    # Creates a FileMatcher given a filename and other
    # configuration options.
    #
    # Recognized options:
    #   - name: The name to be used for this FileMatcher.
    #   - column_name: The column containing scientificNames.
    #   - dialect: The dialect used to read this CSV file.
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

        # TODO: attempt to guess the scientific name column.

        self.dialect = csv.excel
        if 'dialect' in options:
            self.dialect = csv.get_dialect(options['dialect'])

        self.names = None

    # Return the name of this FileMatcher.
    def name(self):
        return self.name

    # Return the column name containing scientific names.
    def column_name(self):
        return self.namecol

    # Return the dialect used to read this file.
    def dialect(self):
        return self.dialect

    # Return the list of fieldnames (header column names) in this file.
    # This will load the entire file into memory, so be careful!
    def fieldnames(self):
        if self.names is None:
            self.match("Felis tigris")
            return self.fieldnames
        else:
            return self.fieldnames

    # Attempts to match the scientific name against this file.
    #
    # Returns: a MatchResult if the name could be matched, otherwise None.
    def match(self, query_scname):
        # self.names is a dict() that forms an index to every row in this
        # file; if it is not set, we load the entire file first.
        if self.names == None:
            self.names = dict()

            csvfile = open(self.filename, "r")
            reader = csv.DictReader(csvfile, dialect=self.dialect)
            self.fieldnames = reader.fieldnames

            row_index = 0
            for row in reader:
                row_index += 1

                scname = row[self.namecol]

                if scname is None:
                    raise RuntimeError('No column "{0:s}" on row {1:d}'.format(
                        self.namecol, row_index
                    ))
                elif scname in self.names:
                    raise RuntimeError('Duplicate scientificName detected: "{0:s}"'.format(scname))
                else:
                    row['_row_index'] = row_index
                    self.names[scname] = row

            csvfile.close()

        # Match the query scientific name against self.names.
        result = None
        if query_scname in self.names:
            row = self.names[query_scname]

            result = MatchResult(
                self,
                query_scname,
                self.filename + "#" + str(row['_row_index']),
                query_scname,
                row['acceptedName'] if ('acceptedName' in row) else "",
                self.name
            )
        else:
            result = None

        return result

    # Returns a string representation of the filename. We use the filename
    # path to distinguish us from others.
    def __str__(self):
        return self.name + " (" + self.filename + ")"

