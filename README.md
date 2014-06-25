# bettertaxonomy

BetterTaxonomy: improved name matching against multiple taxonomic databases.

## Requirements

You need to install [`requests`](http://docs.python-requests.org/). 
Try `pip install requests` or `easy_install requests`.

## Usage

1. Without an internal database.

```
$ python3 bettertaxonomy.py test_names.txt -f latin -c sources.ini
Configuration loaded from sources.ini, 5 match lists configured.
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

 - Processed on 06/25/14 on file test_names.txt in 0:00:05.042998 time.
 - Rows with names processed: 9 (1.78465 rows/second, 0.56033 seconds/row)
 - 4 names (44.44%) were matched against the following sources:
        Catalogue of Life (GB): 1 (25.00%)
        File-based database (./data/LookupClassification.txt): 2 (50.00%)
	Mammal Species of the World, 3rd edition (GB): 1 (25.00%)
 - Names that could not be matched against any checklist: 5 (55.56%)
```

2. With an internal database (which is already matched last):

```
rgnt2-118-209-dhcp:bettertaxonomy vaidyagi$ python3 bettertaxonomy.py test_names.txt -f latin -c sources.ini -i lookupclass-test.txt 
Configuration loaded from sources.ini, 5 match lists configured.
latin,matched_scname,matched_acname,matched_url,matched_source,count,class
Aëronautes,Aëronautes,,./data/LookupClassification.txt#331,Internal database,Aëronautes,Aves
A.,A.,,./data/LookupClassification.txt#76,Internal database,-1,Aves
Arvicolinae,Arvicolinae,,lookupclass-test.txt#1268,internal,1234567891234567891234567890,Mammlia
Eutamias minimus,"Eutamias minimus (Bachman, 1839)","Tamias minimus Bachman, 1839",http://gbif.org/species/119924203,(GBIF:Catalogue of Life)  7ddf754f-d193-4cc9-b351-99906754a03b,10,Mammalia
Panthera tigris,"Panthera tigris Linnaeus, 1758",,http://gbif.org/species/103371328,"(GBIF:Mammal Species of the World, 3rd edition) Syst. Nat. , 10th ed. vol. 1 p. 41 672aca30-f1b5-43d3-8a2b-c1606125fa1b",20,Mammalia
Felis tigris,,,,,30,Mammalia
tiger,,,,,10,Mammalia
Felix tigris,,,,,10,Mammalia
oopsie,,,,,5,Mammalia

 - Processed on 06/25/14 on file test_names.txt in 0:00:09.053734 time.
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
$ python3 bettertaxonomy.py test_names.txt -f latin -c sources.ini -i lookupclass-test.txt 
Configuration loaded from sources.ini, 5 match lists configured.
latin,matched_scname,matched_acname,matched_url,matched_source,count,class
Aëronautes,Aëronautes,,./data/LookupClassification.txt#331,Internal database,Aëronautes,Aves
A.,A.,,./data/LookupClassification.txt#76,Internal database,-1,Aves
Arvicolinae,Arvicolinae,,lookupclass-test.txt#1268,internal,1234567891234567891234567890,Mammlia
Eutamias minimus,"Eutamias minimus (Bachman, 1839)","Tamias minimus Bachman, 1839",http://gbif.org/species/119924203,(GBIF:Catalogue of Life)  7ddf754f-d193-4cc9-b351-99906754a03b,10,Mammalia
Panthera tigris,"Panthera tigris Linnaeus, 1758",,http://gbif.org/species/103371328,"(GBIF:Mammal Species of the World, 3rd edition) Syst. Nat. , 10th ed. vol. 1 p. 41 672aca30-f1b5-43d3-8a2b-c1606125fa1b",20,Mammalia
Felis tigris,Felis tigris,,lookupclass-test.txt#16321,internal,30,Mammalia
tiger,tiger,,lookupclass-test.txt#16322,internal,10,Mammalia
Felix tigris,Felix tigris,,lookupclass-test.txt#16323,internal,10,Mammalia
oopsie,oopsie,,lookupclass-test.txt#16324,internal,5,Mammalia

 - Processed on 06/25/14 on file test_names.txt in 0:00:04.929067 time.
 - Rows with names processed: 9 (1.82590 rows/second, 0.54767 seconds/row)
 - 9 names (100.00%) were matched against the following sources:
	Catalogue of Life (GB): 1 (11.11%)
	File-based database (./data/LookupClassification.txt): 2 (22.22%)
	Mammal Species of the World, 3rd edition (GB): 1 (11.11%)
	internal: 5 (55.56%)
 - Names that could not be matched against any checklist: 0 (0.00%)

```
