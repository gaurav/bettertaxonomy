#
# matchers.py
#
# Some standard matchers for use with the MatchController.
# 

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

