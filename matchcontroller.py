#!/usr/bin/env python3
# 
# matchcontroller.py
# 
# Parses a configuration file, and creates a MatchController object that can 
# match multiple MatcherList objects.
#
# The architecture is:
#   -> MatchController: overall controller
#       -> List of MatcherLists (queried first)
#       -> Default MatcherList (queried last)
#
#   -> MatcherList: handles a list of matchers
#       -> variable: a variable to test
#       -> condition: a value the variable must case-insensitively equal
#           e.g. variable = 'genus', condition = 'panthera'
#       -> Test: test whether this MatcherList can be used by attempting to
#           match the condition against the variable in the provided row.
#       -> List of Matchers: queried in turn on the provided row.
#

import configparser
from matchers import Matcher, MatchResult

# A MatcherList is a list of Matchers that are tested in sequence. Once a Matcher
# matches a name, the search is terminated. A MatcherList can have a "condition" 
# set as a combination of a column name and a value in that column; the test()
# method can be used to check whether a row conforms to that condition.
class MatcherList:
    # Creates a MatcherList. Requires:
    #   - config: The ConfigParser that is parsing the configuration file.
    #   - name: The human-readable name of this matcher list.
    #   - The condition, consisting of:
    #       - column_name: The name of the column to be tested.
    #       - column_value: The value in that column that is a matching condition.
    #   - matchers_list: A list of Matchers.
    def __init__(self, config, name, column_name, column_value, matchers_list):
        self.name = name
        self.column_name = column_name
        self.column_value = column_value
        self.list_names = map(lambda x: x.strip(), matchers_list)
        self.list_matchers = list(map(lambda x: Matcher.build(config, x), self.list_names))

    # Returns the number of matchers.
    def __len__(self):
        return len(self.list_matchers)

    # Tests the provided row for the condition defined.
    #
    # Returns:
    #   - true if the condition matches this row
    #   - false if the condition does not match this row
    # 
    # Note that the column name must match case-sensitively, but the value
    # can match case-insensitively.
    def test(self, row):
        if(self.column_name in row):
            if row[self.column_name].lower() == self.column_value.lower():
                return True
            else:
                return False
        else:
            # Variable not found!
            return False

    # Match the scientific name provided. Dispatches the call to each of the
    # matchers, in sequence.
    #
    # Returns:
    #   - if a match was successful: a MatchResult
    #   - if a match was not successful: None
    def match(self, scname):
        for matcher in self.list_matchers:
            result = matcher.match(scname)
            if result is not None:
                break

        return result

    # Represents this MatcherList as a string.
    def __str__(self):
        return self.name + ": " + ", ".join([str(matcher) for matcher in self.list_matchers])

# An EmptyMatcherList is a MatcherList that contains no matchers, and that
# cannot match any result.
class EmptyMatcherList (MatcherList):
    def __init__(self):
        super(EmptyMatcherList, self).__init__(
            None,
            "Empty MatcherList",
            None, None, []
        )

# A MatchController represents a set of MatcherLists and a default matcher;
# it therefore represents an entire configuration file. It is constructed by
# the parseSources() method that is exposed directly from this module.
class MatchController:
    # Create an empty MatchController.
    def __init__(self):
        self.list = []
        self.default = EmptyMatcherList()

    # Add a MatcherList to MatchController.
    def add(self, matcherlist):
        self.list.append(matcherlist)

    # Sets the default MatcherList used when no other MatcherList has a
    # condition.
    def set_default(self, matcher):
        self.default = matcher

    # Attempts to match a name against all of the MatcherLists in this
    # MatchController.
    #   - scname: the scientific name to match.
    #   - row: the row that this scientific name is contained in.
    #
    # Returns:
    #   - if any of the Matchers matched: a MatchResult
    #   - if none of the Matchers matched: None
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

    # Matches a series of rows, using the column name 'scname_row'
    # The MatchResult is stored in a new column named '${scname_row}_match'.
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

    # Returns the number of MatcherLists in this MatchController.
    def __len__(self):
        return len(self.list) + 1
    
    # Returns a string-representation of this MatchController by listing all
    # the MatcherLists in this object.
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

    # Read the [matchers] section.
    matchers = config['matchers']
    keys = matchers.keys()

    matchc = MatchController()

    for key in keys:
        if key == 'default':
            matchc.set_default(MatcherList(config, key, None, None, matchers[key].split(',')))
        else:
            (col_name, col_value) = key.split('~')
            matchc.add(MatcherList(config, key, col_name.strip(), col_value.strip(), matchers[key].split(',')))

    return matchc

# If this module is executed directly, parse the 'sources.ini' file in the current
# directory, display the matchers created, and run some test names through the
# MatchController created.
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
