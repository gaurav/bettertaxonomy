# bettertaxonomy

BetterTaxonomy: improved name matching against multiple taxonomic databases.

## Requirements

You need to install [`requests`](http://docs.python-requests.org/). 
Try `pip install requests` or `easy_install requests`.

## Usage

1. Without an internal database.

```
$ python bettertaxonomy.py example/test_names.txt -f latin -c example/sources.ini
Configuration loaded from example/sources.ini, 5 match lists configured.
latin,matched_scname,matched_acname,matched_url,matched_source,count,class
Aëronautes,Aëronautes,,./data/LookupClassification.txt#331,Internal database,Aëronautes,Aves
A.,A.,,./data/LookupClassification.txt#76,Internal database,-1,Aves
Arvicolinae,,,,,1234567891234567891234567890,Mammlia
Eutamias minimus,"Eutamias minimus (Bachman, 1839)","Tamias minimus Bachman, 1839",http://gbif.org/species/119924203,(GBIF:Catalogue of Life)  7ddf754f-d193-4cc9-b351-99906754a03b,10,Mammalia
Panthera tigris,"Panthera tigris Linnaeus, 1758",,http://gbif.org/species/103371328,"(GBIF:Mammal Species of the World, 3rd edition) Syst. Nat. , 10th ed. vol. 1 p. 41 672aca30-f1b5-43d3-8a2b-c1606125fa1b",20,Mammalia
Felis tigris,,,,,30,Mammalia
tiger,,,,,10,Mammalia
Felix tigris,,,,,10,Mammalia
oopsie,,,,,5,Mammalia

 - Processed on 06/25/14 on file example/test_names.txt in 0:00:05.042998 time.
 - Rows with names processed: 9 (1.78465 rows/second, 0.56033 seconds/row)
 - 4 names (44.44%) were matched against the following sources:
        Catalogue of Life (GB): 1 (25.00%)
        File-based database (./data/LookupClassification.txt): 2 (50.00%)
	Mammal Species of the World, 3rd edition (GB): 1 (25.00%)
 - Names that could not be matched against any checklist: 5 (55.56%)
```

2. With an internal database (which is already matched last):

```
rgnt2-118-209-dhcp:bettertaxonomy vaidyagi$ python bettertaxonomy.py example/test_names.txt -f latin -c example/sources.ini -i example/internal.txt 
Configuration loaded from example/sources.ini, 5 match lists configured.
latin,matched_scname,matched_acname,matched_url,matched_source,count,class
Aëronautes,Aëronautes,,./data/LookupClassification.txt#331,Internal database,Aëronautes,Aves
A.,A.,,./data/LookupClassification.txt#76,Internal database,-1,Aves
Arvicolinae,Arvicolinae,,example/internal.txt#1268,internal,1234567891234567891234567890,Mammlia
Eutamias minimus,"Eutamias minimus (Bachman, 1839)","Tamias minimus Bachman, 1839",http://gbif.org/species/119924203,(GBIF:Catalogue of Life)  7ddf754f-d193-4cc9-b351-99906754a03b,10,Mammalia
Panthera tigris,"Panthera tigris Linnaeus, 1758",,http://gbif.org/species/103371328,"(GBIF:Mammal Species of the World, 3rd edition) Syst. Nat. , 10th ed. vol. 1 p. 41 672aca30-f1b5-43d3-8a2b-c1606125fa1b",20,Mammalia
Felis tigris,,,,,30,Mammalia
tiger,,,,,10,Mammalia
Felix tigris,,,,,10,Mammalia
oopsie,,,,,5,Mammalia

 - Processed on 06/25/14 on file example/test_names.txt in 0:00:09.053734 time.
 - Rows with names processed: 9 (0.99406 rows/second, 1.00597 seconds/row)
 - 5 names (55.56%) were matched against the following sources:
	Catalogue of Life (GB): 1 (20.00%)
	File-based database (./data/LookupClassification.txt): 2 (40.00%)
	Mammal Species of the World, 3rd edition (GB): 1 (20.00%)
	internal: 1 (20.00%)
 - Names that could not be matched against any checklist: 4 (44.44%)
```

Once the internal database has been updated, new searches will match against it.

```
$ python bettertaxonomy.py example/test_names.txt -f latin -c example/sources.ini -i example/internal.txt 
Configuration loaded from example/sources.ini, 5 match lists configured.
latin,matched_scname,matched_acname,matched_url,matched_source,count,class
Aëronautes,Aëronautes,,./data/LookupClassification.txt#331,Internal database,Aëronautes,Aves
A.,A.,,./data/LookupClassification.txt#76,Internal database,-1,Aves
Arvicolinae,Arvicolinae,,example/internal.txt#1268,internal,1234567891234567891234567890,Mammlia
Eutamias minimus,"Eutamias minimus (Bachman, 1839)","Tamias minimus Bachman, 1839",http://gbif.org/species/119924203,(GBIF:Catalogue of Life)  7ddf754f-d193-4cc9-b351-99906754a03b,10,Mammalia
Panthera tigris,"Panthera tigris Linnaeus, 1758",,http://gbif.org/species/103371328,"(GBIF:Mammal Species of the World, 3rd edition) Syst. Nat. , 10th ed. vol. 1 p. 41 672aca30-f1b5-43d3-8a2b-c1606125fa1b",20,Mammalia
Felis tigris,Felis tigris,,example/internal.txt#16321,internal,30,Mammalia
tiger,tiger,,example/internal.txt#16322,internal,10,Mammalia
Felix tigris,Felix tigris,,example/internal.txt#16323,internal,10,Mammalia
oopsie,oopsie,,example/internal.txt#16324,internal,5,Mammalia

 - Processed on 06/25/14 on file example/test_names.txt in 0:00:04.929067 time.
 - Rows with names processed: 9 (1.82590 rows/second, 0.54767 seconds/row)
 - 9 names (100.00%) were matched against the following sources:
	Catalogue of Life (GB): 1 (11.11%)
	File-based database (./data/LookupClassification.txt): 2 (22.22%)
	Mammal Species of the World, 3rd edition (GB): 1 (11.11%)
	internal: 5 (55.56%)
 - Names that could not be matched against any checklist: 0 (0.00%)

```

## Configuration file

To use BetterTaxonomy, you need to set up a configuration file. An example file is 
provided [in the distribution](https://github.com/gaurav/bettertaxonomy/blob/develop/example/sources.ini). 
This tells the script which resources to query for species names. 

Each configuration file contains a `matchers` section, which contains a set of 
Matcher Lists. Each Matcher List is activated by a particular condition in the 
format `column-name ~ value`; if the column name for a particular row matches 
the value, that Matcher List is used to process that row. If no condition can 
be matched, the Matcher List marked `default` is used. The example matchers section
looks like the following:

```ini
[matchers]
class ~ mammalia = msw3, itis, col, paleodb, ncbi, file-example, taxrefine
class ~ aves = avibase, itis, col, paleodb, ncbi, file-example, taxrefine
class ~ reptilia = itis, col, reptile_database, paleodb, ncbi, file-example, taxrefine
class ~ amphibia = amphibiaweb, itis, col, paleodb, ncbi, file-example, taxrefine
phylum ~ chordata = fishbase, itis, col, paleodb, ncbi, file-example, taxrefine
default = file-example, taxrefine
```

Each Matcher List consists of a series of matchers. Each matcher must be described in
its own `matcher` section; for example, `file-example` is described in the section
`matcher:file-example`.

```ini
[matcher:file-example]
name = File-based database
file = ./data/LookupClassification.txt
scientificName_column = scientificName
```

The type of a matcher is determined by the settings it contains: `gbif_id` indicates a
GBIF matcher, while `file` indicates a File matcher.

### File matcher

A file matcher matches a name in any file format that 
[Python's CSV module](https://docs.python.org/3/library/csv.html) can accept. It
accepts the following properties:

* `name`: The name of this file matcher.
* `file`: The location of a file to load.
* `dialect`: [The CSV dialect](https://docs.python.org/3/library/csv.html#csv.Dialect) the file uses. Use `excel` for most CSV files, and `excel_tab` for most tab-delimited files.
* `scientificName_column`: The name of the column in the CSV file that contains the scientific name.

An example of a file matcher is as follows:

```ini
[matcher:file-example]
name = File-based database
file = ./data/LookupClassification.txt
scientificName_column = scientificName
```

### GBIF matcher

A GBIF matcher matches a name against a particular checklist on GBIF. It accepts the
following properties:

* `name`: The name of this GBIF matcher.
* `gbif_id`: The UUID that identifies this checklist on the GBIF website. For example, _Mammal Species of the World, 3rd edition_ is [672aca30-f1b5-43d3-8a2b-c1606125fa1b](http://www.gbif.org/dataset/672aca30-f1b5-43d3-8a2b-c1606125fa1b).

An example of a GBIF matcher is as follows:

```ini
[matcher:msw3]
name = Mammal Species of the World, 3rd edition
gbif_id = 672aca30-f1b5-43d3-8a2b-c1606125fa1b
```

### GNA matcher

A GNA matcher uses the [Global Names Architecture Resolver](http://resolver.globalnames.org/) to match names against one or more [checklists imported into GNA](http://resolver.globalnames.org/data_sources).

An example of a GNA matcher is as follows:

```ini
[matcher:msw3_itis_col_paleodb_ncbi]                                            
name = MSW3, ITIS, CoL, PaleoDB, NCBI                                           
gna_id = 174, 3, 1, 172, 4
```
