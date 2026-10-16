import random
from django.conf import settings
from explore.clients.unsplash_client import UnsplashClient
from .photo_cache import UnsplashPhotoCache


class LocationPhotoService:
    SEARCH_RESULT_COUNT = 10
    PHOTO_COUNT = 5

    def __init__(self, client=None, cache=None, sampler=None):
        self.client = client or UnsplashClient(settings.UNSPLASH_API_ACCESS_KEY)
        self.cache = cache or UnsplashPhotoCache()
        self.sampler = sampler or random.sample

    def get_photo_urls(self, query):
        request_hash = self.cache.request_hash(query, self.PHOTO_COUNT)
        cached = self.cache.get(request_hash)
        if cached is not None:
            return cached

        urls = self.client.search_photo_urls(
            query,
            per_page=self.SEARCH_RESULT_COUNT,
        )
        selected_urls = (
            self.sampler(urls, self.PHOTO_COUNT)
            if len(urls) >= self.PHOTO_COUNT
            else []
        )
        self.cache.set(request_hash, selected_urls)
        return selected_urls
