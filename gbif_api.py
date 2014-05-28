# A Python script for accessing the GBIF API 0.9
# http://www.gbif.org/developer/species

# HTTP lib
import requests

gbif_api_root = "http://api.gbif.org/v0.9";

def get_matches(name, dataset = None):
    url = gbif_api_root + "/species"

    params={
        'name': name,
        'strict': 'true'
    }

    if dataset is not None:
        params['datasetKey'] = dataset

    response = requests.get(url, params=params)

    # Throw an exception if something went wrong
    response.raise_for_status() 

    # Parse response
    json = response.json()
    results = json['results']

    return results

# TaxRefine

def get_matches_from_taxrefine(name, datasets = []):
    url = "http://refine.taxonomics.org/gbifchecklists/reconcile"

    response = requests.get(url, params = {
        'query': name
    })

    # Throw an exception if something went wrong
    response.raise_for_status()

    # Parse response
    json = response.json()
    result = json['result']

    return result

def get_url_for_id(id): 
    # TODO: check that id is purely number
    return "http://gbif.org/species/" + str(id)
