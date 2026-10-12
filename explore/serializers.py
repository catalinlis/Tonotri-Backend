from rest_framework import serializers

class CountryQuerySerializer(serializers.Serializer):
    country = serializers.CharField(max_length=100, trim_whitespace=True)

class LocationQuerySerializer(CountryQuerySerializer):
    city = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True,
    )
    population = serializers.IntegerField(required=False, default=0, min_value=0)

class CountryCitiesQuerySerializer(serializers.Serializer):
    country = serializers.CharField(min_length=2, max_length=2)
    search = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default="",
        trim_whitespace=True
    )

    def validate_country(self, value):
        return value.upper()

class CityQuerySerializer(LocationQuerySerializer):
    city = serializers.CharField(max_length=100, trim_whitespace=True)

class LandmarkQuerySerializer(serializers.Serializer):
    landmark = serializers.CharField(max_length=150, trim_whitespace=True)

class LandmarkDescriptionQuerySerializer(LandmarkQuerySerializer):
    city = serializers.CharField(max_length=100, trim_whitespace=True)
    country = serializers.CharField(max_length=100, trim_whitespace=True)

