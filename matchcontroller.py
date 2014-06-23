#!/usr/bin/env python3
# 
# matcher.py
# 
# Parses a configuration file, and creates an object that can match
# results.
#

import sys
import configparser
from matchers import Matcher, MatchResult

# A MatcherList
class MatcherList:
    def __init__(self, config, name, variable, condition, matchers_list):
        self.name = name
        self.variable = variable
        self.condition = condition
        self.list_names = map(lambda x: x.strip(), matchers_list)
        self.list_matchers = list(map(lambda x: Matcher.build(config, x), self.list_names))
        self.default = Matcher.Null("No default handler defined")

        # print("MatcherList created with matchers: " + str(list(self.list_matchers)))

    def __len__(self):
        return len(self.list_matchers) + 1

    def test(self, row):
        if(self.variable in row):
            if row[self.variable].lower() == self.condition.lower():
                return True
            else:
                return False
        else:
            # Variable not found!
            return False

    def match(self, scname):
        # print("MatcherList " + self.__str__() + ".match called: " + str(list(self.list_matchers)))
        for matcher in self.list_matchers:
            # print("Matching " + scname + " against " + str(matcher))
            result = matcher.match(scname)
            if result is not None:
                break

        if result is None:
            result = self.default.match(scname)

        return result

    def __str__(self):
        return self.name + ": " + ", ".join([str(matcher) for matcher in self.list_matchers])

class EmptyMatcherList (MatcherList):
    def __init__(self):
        super(EmptyMatcherList, self).__init__(
            None,
            "Empty defaults list",
            None, None, []
        )

class MatchController:
    def __init__(self):
        self.list = []
        self.default = EmptyMatcherList()

    def add(self, matcher):
        self.list.append(matcher)

    def set_default(self, matcher):
        self.default = matcher

    def match(self, scname, row = dict()):
        result = None

        for matchlist in self.list:
            if matchlist.test(row):
                result = matchlist.match(scname)
                if result is not None:
                    break

        if result is None:
            resulf = self.default.match(scname)

        return result

    def matchRows(self, rows, scname_row):
        for row in rows:
            scname = row[scname_row]
            # print(" - scname: " + scname)
            result = None

            for matchlist in self.list:
                # Check matchlist.test(row)
                result = matchlist.match(scname)
                if result is not None:
                    break

            if result is None:
                result = self.default.match(scname)
 
            row[scname_row + '_match'] = result

    def __len__(self):
        return len(self.list)
    
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
    
    test_data = [
        {'scientificName': 'Panthera tigris'},
        {'scientificName': 'Felis tigris'}
    ]
    matcher.match(test_data, 'scientificName')

    print("Results:")
    for row in test_data:
        print(" - " + row['scientificName'] + ": " + str(row['scientificName_match']))
