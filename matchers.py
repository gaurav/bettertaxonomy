#
# matchers.py
#
# Some standard matchers for use with the MatchController.
# 

import gbif_api

# The result of a match.
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

    def query(self):
        return self.query

    def matched_name(self):
        return self.matched_name
        
    def name_id(self):
        return self.name_id

    def source(self):
        return self.source
        
    def Empty():
        return None 

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

class FileMatcher(Matcher):
    def __init__(self, name, filename, options):
        if 'name' in options:
            self.name = options['name']
        else:
            self.name = name
        self.filename = filename
        self.options = options

    def name(self):
        return self.name

    def ready(self):
        return

    def match(self, scname):
        return None

    def __str__(self):
        return self.name + " (FL)"

