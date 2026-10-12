from django.test import SimpleTestCase

from .serializers import LandmarkDescriptionQuerySerializer


class ExploreSerializerTests(SimpleTestCase):
    def test_landmark_description_uses_country_field(self):
        serializer = LandmarkDescriptionQuerySerializer(
            data={
                "landmark": "Colosseum",
                "city": "Rome",
                "country": "Italy",
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["country"], "Italy")
