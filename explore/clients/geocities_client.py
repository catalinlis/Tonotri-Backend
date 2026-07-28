import requests

class GeoDbCitiesClient:
    BASE_URL = 'https://wft-geo-db.p.rapidapi.com/v1/geo/places'

    def __init__(self, api_key):
        self.headers = {
            'X-RapidAPI-Key': api_key,
            'X-RapidAPI-Host': 'wft-geo-db.p.rapidapi.com'
        }

    def search_cities(self, country, search, limit=10):
        params = {
            'countryIds': country,
            'types': 'CITY,ADM2',
            'namePrefix': search,
            'limit': limit,
            'minPopulation': 5000
        }

        response = requests.get(
            self.BASE_URL,
            headers = self.headers,
            params = params,
            timeout = 3
        )

        response.raise_for_status()
        return response.json()