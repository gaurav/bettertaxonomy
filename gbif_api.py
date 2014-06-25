# A Python script for accessing the GBIF API 0.9
# http://www.gbif.org/developer/species


import requests     # HTTP library
import sys          # So we can print to stderr

# Path to the API.
gbif_api_root = "http://api.gbif.org/v0.9";

# Look up this name on a particular dataset.
def get_matches(name, dataset = None):
    url = gbif_api_root + "/species"

    params={
        'name': name,
        'strict': 'true'
    }

    if dataset is not None:
        params['datasetKey'] = dataset

    try:
        response = requests.get(url, params=params)
    except ConnectionError as e:
        sys.stderr.write("Connection error when querying '%s': %s\n" %
            (url, e)
        )
        return []

    # Throw an exception if something went wrong
    response.raise_for_status() 

    # Parse response
    json = response.json()
    results = json['results']

    return results

# Look up this name using TaxRefine.
def get_matches_from_taxrefine(name):
    url = "http://refine.taxonomics.org/gbifchecklists/reconcile"

    try:
        response = requests.get(url, params = {
            'query': name
        })
    except ConnectionError as e:
        sys.stderr.write("Connection error when querying '%s': %s\n" %
            (url, e)
        )
        return []

    # Throw an exception if something went wrong
    response.raise_for_status()

    # Parse response
    json = response.json()
    result = json['result']

    return result

# Convert a GBIF ID to a URL.
def get_url_for_id(id): 
    # TODO: check that id is a number
    return "http://gbif.org/species/" + str(id)
