from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from accounts.permissions import IsActiveUser
from django.shortcuts import render
from django.conf import settings
from .services.explore_service import CountryDescriptionService, CityDescriptionService
from .services.explore_service import LandmarkVariationsService, LandmarkDescriptionService
from .clients.geocities_client import GeoDbCitiesClient
from .models import Country
import requests
import random
import json

class LocationPhotos(APIView):
    permission_classes = [IsActiveUser]
    url = 'https://api.unsplash.com/search/photos'

    def get(self, request):
    
        country = request.GET.get('country', '')
        city = request.GET.get('city', '') 
        population = int(request.GET.get('population', '0'))

        country_obj = Country.objects.filter(country_name__iexact=country).first()

        if not country_obj:
            return Response(
                {'error': 'The country does not exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        query_location = self._build_query(country_obj.country_name , city, population)
        print(query_location)

        params = {
            'query': query_location,
            'per_page': 10,
            'client_id': settings.UNSPLASH_API_ACCESS_KEY
        }

        response = requests.get(self.url, params=params)
        data = response.json()
        
        photo_urls = {}
        photo_urls['country'] = country_obj.country_name
        urls = []
        photo_urls['photo_urls'] = []


        if data['results']:
            for result in data['results']:
                urls.append(result['urls']['full'])

        if len(urls) >= 5 :
            photo_urls['photo_urls'] = random.sample(urls, 5)

        photo_urls['count'] = len(photo_urls['photo_urls'])

        return Response(photo_urls, status=status.HTTP_200_OK)

    def _build_query(self, country=None, city=None, population=0):

        if city and country and population > 1000000:
            query_location = city
        elif city and country and population < 1000000:
            query_location = city + ' ' + country
        else:
            query_location = country

        return query_location

class CountryDescriptionAI(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        country = request.GET.get('country', '')

        country_obj = Country.objects.filter(country_name__iexact=country).first()

        if not country_obj:
            return Response(
                {'error': 'The country does not exists.'},
                status = status.HTTP_400_BAD_REQUEST
            )

        service = CountryDescriptionService()
        result = service.generate(country)

        if result['success'] == False:
            return Response(
                result['message'],
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result['message'],
            status=status.HTTP_200_OK
        )

class CountryCities(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        country = request.GET.get('country', '')
        cities = request.GET.get('search', '')

        client = GeoDbCitiesClient(settings.RAPID_API_KEY)

        data = client.search_cities(
            country = country,
            search = cities,
            limit = 10
        )

        no_duplicates = {
            (
                item.get('name', ''),
                item.get('region', '')
            ): item
            for item in data.get('data', [])
        }.values()

        # normalization 
        cities = [
            {
                'id': item['id'],
                'name': item['name'],
                'country': item['country'],
                'region': item.get('region', ''),
                'population': item.get('population', '')
            }
            for item in no_duplicates
        ]

        return Response(
            cities,
            status=status.HTTP_200_OK
        )

class CityDescriptionAI(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        country = request.GET.get('country', '')
        city = request.GET.get('city', '')
        population = int(request.GET.get('population', '0'))

        country_obj = Country.objects.filter(country_name__iexact=country).first()

        if not country_obj:
            return Response(
                {'error': 'The country does not exists.'},
                status = status.HTTP_400_BAD_REQUEST
            )

        service = CityDescriptionService()
        result = service.generate(city, country, population)

        if result['success'] == False:
            return Response(
                result['message'],
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result['message'],
            status=status.HTTP_200_OK
        )

class LandmarkVariationsAI(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        
        landmark = request.GET.get('landmark', '')

        if not landmark:
            return Response(
                {'error': 'Provide a landmark'},
                status = status.HTTP_400_BAD_REQUEST
            )

        service = LandmarkVariationsService()
        result = service.generate(landmark)

        if result['success'] == False:
            return Response(
                result['message'],
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result['message'],
            status=status.HTTP_200_OK
        )

class LandmarkDescriptionAI(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        
        landmark = request.GET.get('landmark', '')
        city = request.GET.get('city', '')
        country = request.GET.get('country', '')

        if not (landmark and city and country):
            return Response(
                {'error': 'Provide a landmark'},
                status = status.HTTP_400_BAD_REQUEST
            )

        service = LandmarkDescriptionService()
        result = service.generate(landmark, city, country)

        if result['success'] == False:
            return Response(
                result['message'],
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result['message'],
            status=status.HTTP_200_OK
        )
        