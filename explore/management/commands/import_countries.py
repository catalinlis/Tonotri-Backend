import json
from django.core.management.base import BaseCommand
from explore.models import Country

class Command(BaseCommand):
    help = 'Import countries from JSON file'

    def handle(self, *args, **kwargs):
        with open('countries.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        created = 0

        for item in data:
            obj, is_created = Country.objects.get_or_create(
                alpha2=item['alpha2'],
                defaults={
                    'alpha3': item['alpha3'],
                    'country_name': item['en']
                }
            )

            if is_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'{created} countries imported!'))