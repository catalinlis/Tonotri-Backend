import requests


class UnsplashClient:
    """Retrieve location photo URLs from Unsplash."""

    SEARCH_URL = 'https://api.unsplash.com/search/photos'

    def __init__(self, access_key, session=None):
        self.access_key = access_key
        self.session = session or requests

    def search_photo_urls(self, query, per_page=10):
        """Return full-size photo URLs matching a search query."""

        response = self.session.get(
            self.SEARCH_URL,
            params={
                'query': query,
                'per_page': per_page,
                'client_id': self.access_key,
            },
            timeout=10,
        )
        response.raise_for_status()

        return [
            result['urls']['full']
            for result in response.json().get('results', [])
            if result.get('urls', {}).get('full')
        ]
