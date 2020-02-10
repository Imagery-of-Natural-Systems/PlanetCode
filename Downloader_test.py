#pip install planet
# !pip install requests
# !pip install retrying

from planet import api
from planet.api import filters
from sys import stdout

client = api.ClientV1()
PL_API_KEY = 'd4cc6c146f3546c4922dab52ea5d4225'
# %% Build request example on https://www.planet.com/docs/api-quickstart-examples/step-1-search/
# AOI via http://geojson.io

geo_json_geometry = {
    "type": "Polygon",
    "coordinates": [
        [
            [
                48.47116470336914,
                -17.76863141454526
            ],
            [
                48.55356216430663,
                -17.76863141454526
            ],
            [
                48.55356216430663,
                -17.676245604226583
            ],
            [
                48.47116470336914,
                -17.676245604226583
            ],
            [
                48.47116470336914,
                -17.76863141454526
            ]
        ]
    ]
}

# filter for items the overlap with our chosen geometry
geometry_filter = {
    "type": "GeometryFilter",
    "field_name": "geometry",
    "config": geo_json_geometry
}

# filter images acquired in a certain date range (01/01/18 - 01/02/18)
date_range_filter = {
    "type": "DateRangeFilter",
    "field_name": "acquired",
    "config": {
        "gte": "2018-02-15T00:00:00.000Z",
        "lte": "2018-02-17T00:00:00.000Z"
    }
}

# filter any images which are more than 10% clouds
cloud_cover_filter = {
    "type": "RangeFilter",
    "field_name": "cloud_cover",
    "config": {
        "lte": 0.1,
    }
}

# product type

item_types = ['PSScene4Band', 'REOrthoTile']
asset_type = 'analytic'

# coverage?

# create a filter that combines our geo and date filters
# could also use an "OrFilter"
query = {
    "type": "AndFilter",
    "config": [geometry_filter, date_range_filter, cloud_cover_filter]
}

# build a request for type of image: which one?
request = filters.build_search_request(
    query, item_types
)

# %% Searching data, example on https://www.planet.com/docs/api-quickstart-examples/step-1-search/
# if you don't have an API key configured, this will raise an exception
dataset = client.quick_search(request)

stdout.write('id,cloud_cover,date\n')

# items_iter returns a limited iterator of all results. behind the scenes,
# the client is paging responses from the API
for item in dataset.items_iter(limit=None):
    props = item['properties']
    stdout.write('{0},{cloud_cover},{acquired}\n'.format(item['id'], **props))

# %% download

import urllib.request
import shutil

from requests.auth import HTTPBasicAuth
import os
import time
import requests

for i in item_types:
    request = api.filters.build_search_request(query, [i])  # ,name = None, interval= 'day')
    dataset = client.quick_search(request)
    print(i)
    for item in dataset.items_iter(limit=1):
        print(item['id'])
        session = requests.Session()
        session.auth = (PL_API_KEY, '')
        results = \
            session.get(
                ("https://api.planet.com/data/v1/item-types/" +
                 "{}/items/{}/assets/").format(i, item['id']))
        # extract the activation url from the item for the desired asset
        item_activation_url = results.json()[asset_type]["_links"]["activate"]
        # request activation
        response = session.post(item_activation_url)
        print(response.status_code)
        while response.status_code != 204:
            time.sleep(30)
            response = session.post(item_activation_url)
            response.status_code = response.status_code
            print(response.status_code)
        # assets = client.get_assets(item).get()
        # callback = api.write_to_file(directory=None, callback= None, overwrite= True)
        # body = client.download(assets[asset_type], callback=callback)
        # body.await()
        item_url = 'https://api.planet.com/data/v1/item-types/{}/items/{}/assets'.format(i, item['id'])
        result = requests.get(item_url, auth=HTTPBasicAuth(PL_API_KEY, ''))
        download_url = result.json()[asset_type]['location']  # KeyError: 'location'
        output_file = item['id'] + '_subarea.tif'

        with urllib.request.urlopen(download_url) as response, open(output_file, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)