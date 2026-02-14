import json
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from products.models import Province, City

class Command(BaseCommand):
    help = 'Import provinces and cities from JSON file'

    def handle(self, *args, **kwargs):
        current_file_path = Path(__file__).resolve()
        
        current_dir = current_file_path.parent
        
        json_file_path = current_dir / 'provinces_cities.json'

        try:
            with open(json_file_path, encoding='utf-8') as f:
                data = json.load(f) #

            for item in data:
                province_name = item['name']
                province, created = Province.objects.get_or_create(name=province_name)
                
                for city_name in item['cities']:
                    City.objects.get_or_create(name=city_name, province=province)
            
            self.stdout.write(self.style.SUCCESS('Provinces and cities loaded successfully!'))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found at: {json_file_path}'))