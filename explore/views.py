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
from .models import AIUsageEvent
from django.db.models import Count, Sum
from .serializers import (
    CityQuerySerializer,
    CountryCitiesQuerySerializer,
    CountryQuerySerializer,
    LandmarkDescriptionQuerySerializer,
    LandmarkQuerySerializer,
    LocationQuerySerializer,
)
import requests
import random
import json

class LocationPhotos(APIView):
    permission_classes = [IsActiveUser]
    url = 'https://api.unsplash.com/search/photos'

    def get(self, request):
        input_serializer = LocationQuerySerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        country = input_serializer.validated_data['country']
        city = input_serializer.validated_data['city']
        population = input_serializer.validated_data['population']

        country_obj = Country.objects.filter(country_name__iexact=country).first()

        if not country_obj:
            return Response(
                {'error': 'The country does not exists.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        query_location = self._build_query(country_obj.country_name , city, population)

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
        input_serializer = CountryQuerySerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        country = input_serializer.validated_data['country']

        country_obj = Country.objects.filter(country_name__iexact=country).first()

        if not country_obj:
            return Response(
                {'error': 'The country does not exists.'},
                status = status.HTTP_400_BAD_REQUEST
            )

        service = CountryDescriptionService()
        result = service.generate(country, user=request.user)

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
        input_serializer = CountryCitiesQuerySerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        country = input_serializer.validated_data['country']
        cities = input_serializer.validated_data['search']

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
        input_serializer = CityQuerySerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        country = input_serializer.validated_data['country']
        city = input_serializer.validated_data['city']
        population = input_serializer.validated_data['population']

        country_obj = Country.objects.filter(country_name__iexact=country).first()

        if not country_obj:
            return Response(
                {'error': 'The country does not exists.'},
                status = status.HTTP_400_BAD_REQUEST
            )

        service = CityDescriptionService()
        result = service.generate(city, country, population, user=request.user)

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
        input_serializer = LandmarkQuerySerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        landmark = input_serializer.validated_data['landmark']

        service = LandmarkVariationsService()
        result = service.generate(landmark, user=request.user)

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
        input_serializer = LandmarkDescriptionQuerySerializer(data=request.query_params)
        input_serializer.is_valid(raise_exception=True)
        landmark = input_serializer.validated_data['landmark']
        city = input_serializer.validated_data['city']
        country = input_serializer.validated_data['country']

        service = LandmarkDescriptionService()
        result = service.generate(landmark, city, country, user=request.user)

        if result['success'] == False:
            return Response(
                result['message'],
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            result['message'],
            status=status.HTTP_200_OK
        )


class AIUsageSummary(APIView):
    permission_classes = [IsActiveUser]

    def get(self, request):
        events = AIUsageEvent.objects.filter(user=request.user)
        totals = events.aggregate(
            input_tokens=Sum('input_tokens'),
            cached_input_tokens=Sum('cached_input_tokens'),
            output_tokens=Sum('output_tokens'),
            estimated_cost_usd=Sum('estimated_cost_usd'),
        )
        by_service = list(
            events.values('service')
            .annotate(
                requests=Count('id'),
                estimated_cost_usd=Sum('estimated_cost_usd'),
            )
            .order_by('service')
        )

        return Response({
            'requests': events.count(),
            'input_tokens': totals['input_tokens'] or 0,
            'cached_input_tokens': totals['cached_input_tokens'] or 0,
            'output_tokens': totals['output_tokens'] or 0,
            'estimated_cost_usd': str(totals['estimated_cost_usd'] or 0),
            'by_service': [
                {
                    **item,
                    'estimated_cost_usd': str(item['estimated_cost_usd']),
                }
                for item in by_service
            ],
        })
        
