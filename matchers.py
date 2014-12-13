#
# matchers.py
#
# Some standard matchers for use with the MatchController.
# 

import sys

# Turn to true to activate debug output.
FLAG_DEBUG = False

# The root class of all Matchers. Use Matcher.build(...) to create a new Matcher
# subclass for a given configuration.
class Matcher(object):
    # Every Matcher has a name.
    def name(self):
        raise NotImplementedError("Matcher subclass did not implement name!")
    
    # Every Matcher can be matched against a scientific name, returning either
    # a MatchResult or None.
    def match(self, scname):
        raise NotImplementedError("Matcher subclass did not implement match!")

    # Creates a configuration for a matcher with a particular name.
    #   - self: the Matcher() object (which we don't need).
    #   - config: a dict() contains configuration options for this Matcher.
    #   - name: the name of this matcher.
    # 
    # Returns: a Matcher
    def build(self, config, name): 
        if not config.has_section("matcher:" + name):
            raise RuntimeError("No matcher found in the configuration file for '{:s}'!".format(name))
        else:
            # Picks a subclass to create based on the configuration provided.
            # Eventually, we might have a "type=gbif" as part of the config, but
            # for now we can just use the field names.
            matcher_section = "matcher:" + name
            section = dict(config.items(matcher_section))
            if config.has_option(matcher_section, "recon_url"):
                return ReconciliationMatcher(name, config.get(matcher_section, 'recon_url'), section)
            elif "gbif_id" in section:
                return GBIFMatcher(name, config.get(matcher_section, 'gbif_id'), section)
            elif "gna_id" in section:
                return GNAMatcher(name, re.split('\s*,\s*', config.get(matcher_section, 'gna_id')), section)
            elif "file" in section:
                return FileMatcher(name, config.get(matcher_section, 'file'), section)
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

    # Returns a string object; we use "(GBIF)" after the name given to us.
    def __str__(self):
        return self.name + " (GBIF)"

# Matches this name against GNA's name resolver (http://resolver.globalnames.org/)
import urllib
import urllib2
import json
import re

class GNAMatcher(Matcher):
    # Creates an object given a GNA ID and other options.
    # No other options are currently recognized.
    def __init__(self, name, gna_ids, options):
        if 'name' in options:
            self.name = options['name']
        else:
            self.name = name
        self.gna_ids = gna_ids
        self.options = options

    # Returns the name of this matcher, as used in the configuration file.
    def name(self):
        return self.name

    # Matches this name against the GNA resolver.
    def match(self, scname):
        # Query the GNA resolver.
        stream = urllib2.urlopen("http://resolver.globalnames.org/name_resolvers.json",
            data = urllib.urlencode({
                "names": scname,
                "preferred_data_sources": "|".join(self.gna_ids),
                "best_match_only": "true"
            })
        )
        results = json.load(stream)
        stream.close()

        if FLAG_DEBUG:
            print("QUERY: " + urllib.urlencode({
                "names": scname,
                "preferred_data_sources": "|".join(self.gna_ids),
                "best_match_only": "true"
            }))

        if results['status'] != 'success':
            # TODO: raise error
            return None

        data = results['data']
        if len(data) == 0 or 'results' not in data[0]:
            return None

        matches = data[0]['preferred_results']
        if len(matches) == 0:
            return None

        best_match = matches[0]

        # TODO: what should we do if the best match is a genus?

        # Construct a MatchResult to return.
        result = MatchResult(
            self,
            scname,
            best_match['gni_uuid'],
            best_match['canonical_form'],
            None, # Accepted name
            "GNA:%d (%s)" % (best_match['data_source_id'], best_match['data_source_title'])
        )

        return result

    # Returns a string object; we use "(GNA)" after the name given to us.
    def __str__(self):
        return self.name + " (GNA)"

# ReconciliationMatcher: match against a reconciliation service
class ReconciliationMatcher(Matcher):
    # Creates an object given a recon_url and other options.
    # No other options are currently recognized.
    def __init__(self, name, recon_url, options):
        if 'name' in options:
            self.name = options['name']
        else:
            self.name = name
        self.recon_url = recon_url
        self.options = options

    # Returns the name of this matcher, as used in the configuration file.
    def name(self):
        return self.name

    # Matches this name against the reconciliation service.
    def match(self, scname):
        # Query the reconciliation service.
        matches = gbif_api.get_matches_from_recon_url(self.recon_url, scname)

        # Pick the first match.
        if len(matches) == 0:
            return None
        result = matches[0]

        # Distinguish accepted and use name.
        name = result['name']

        # This only works on TaxRefine, but it's unlikely to show up elsewhere.
        accepted = ""
        if name.find("[=>") != -1: 
            (name, sep, accepted) = name.partition("[=>")

        source = ""
        if "summary" in result:
            summary = result['summary']
            if "accordingTo" in summary:
                accordingTo = summary['accordingTo']
                if type(accordingTo) == dict:
                    source += "According to: " + ", ".join(accordingTo.keys()) + " "
                else:
                    source += "According to: " + str(accordingTo) + " "

            if "publishedIn" in summary:
                publishedIn = summary['publishedIn']
                if type(publishedIn) == dict:
                    source += "Published in: " + ", ".join(publishedIn.keys()) + " "
                else:
                    source += "Published in: " + str(publishedIn) + " "

            if "datasetKey" in summary:
                datasetKey = summary['datasetKey']
                if type(datasetKey) == dict:
                    source += "GBIF datasets: " + ", ".join(datasetKey.keys()) + " "
                else:
                    source += "GBIF datasets: " + str(datasetKey) + " "

        # Construct a MatchResult to return.
        result = MatchResult(
            self,
            scname,
            gbif_api.get_url_for_id(result['id']),
            name,
            accepted,
            "(Recon:{}) {}".format(self.name, source.strip())
        )

        return result

    # Returns a string object; we use "(RECON)" after the name given to us.
    def __str__(self):
        return self.name + " (RECON)"

# Look up this name in a file.
import csv

# Set the maximum field size to ... whatever.
csv.field_size_limit(sys.maxsize)

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
        # TODO: test whether this column actually exists in the source data.

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

            csvfile = open(self.filename, "rb")
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

