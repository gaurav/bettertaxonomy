# matcher.py
# 
# Parses a configuration file, and creates an object that can match
# results.
#

import configparser

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
        return None

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

# A MatcherList
class MatcherList:
    def __init__(self, config, name, variable, condition, list):
        self.name = name
        self.variable = variable
        self.condition = condition
        self.list_names = map(lambda x: x.strip(), list)
        self.list_matchers = map(lambda x: Matcher.build(config, x), self.list_names)
        self.default = NullMatcher("No default handler defined")

    def __str__(self):
        return self.name + ": " + ", ".join([str(matcher) for matcher in self.list_matchers])

class EmptyMatcherList (MatcherList):
    def __init__(self):
        super(EmptyMatcherList, self).__init__(
            None,
            "Empty defaults list",
            None, None, []
        )

# A MatchController
class MatchController:
    def __init__(self):
        self.list = []
        self.default = EmptyMatcherList()

    def add(self, matcher):
        self.list.append(matcher)

    def set_default(self, matcher):
        self.default = matcher

    def __str__(self):
        str_list = [str(i) for i in self.list]

        if len(self.list) == 0:
            return "Empty MatchController with default: " + str(self.default)
        else:
            return "MatchController consisting of " + str(len(self.list)) + " matchers:\n   - " + \
                "\n   - ".join(str_list) + \
                "\n   - " + str(self.default)

# Parses a .ini file and creates a sequence of matchers that follow
# the sequence in the file.
def parseSources(*filenames):
    config = configparser.ConfigParser()
    config.read(filenames, encoding='utf8')

    matchers = config['matchers']
    keys = matchers.keys()

    matchc = MatchController()

    for key in keys:
        if key == 'default':
            matchc.set_default(MatcherList(config, key, None, None, matchers[key].split(',')))
        else:
            (var, cond) = key.split('~')
            matchc.add(MatcherList(config, key, var.strip(), cond.strip(), matchers[key].split(',')))

    return matchc

# If called directly, parse the 'sources.ini' file in the current
# directory and 
if __name__ == '__main__':
    matcher = parseSources('sources.ini')
    print(matcher)
