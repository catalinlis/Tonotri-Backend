from .base_service import BaseDescriptionAI
from .schemas import CountrySchema, BigCitySchema, CitySchema, LandmarkSchema

class CountryDescriptionService(BaseDescriptionAI):
    service_name = 'country_description'

    def generate(self, country: str, user=None):
        try:
            prompt = self._build_prompt(country)
            return self._generate_cached(
                parameters={'country': country.strip().casefold()},
                prompt=prompt,
                schema=CountrySchema.get(),
                user=user,
            )

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": f"Request for {country} failed."
            }

    def _build_prompt(self, country: str) -> str:
        return f"""
        Generate structured travel data for {country}.
        Rules:
        - country description in 5 sentences
        - city description in 2 sentences
        - place description in 2 sentences
        - annual events description in 1 sentence
        - exactly 5 cities 
        - exactly 6 top places
        - exactly 9 annual events from this year
        - annual events must be related to culture, music fest or nature
        - annual events must be popular and well-known tourist events
        - events should attract visitors nationally or internationally  
        - short concise descriptions
        - don't use ';' instead use ','
        - no extra fields
        """

class CityDescriptionService(BaseDescriptionAI):
    service_name = 'city_description'

    def generate(self, city: str, country: str, population: int, user=None):
        try:
            population = int(population)
            return self._generate_cached(
                parameters={
                    'city': city.strip().casefold(),
                    'country': country.strip().casefold(),
                    'population': population,
                },
                prompt=self._build_prompt(city, country, population),
                schema=self._get_schema(population),
                user=user,
            )
        
        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": f"Request for {country}, {city} failed."
            }

    def _build_prompt(self, city: str, country: str, population: int) -> str:
        
        if population >= 100000:
            prompt = f"""
                Generate structured travel data for the city of {city}, {country}.

                Rules:
                - city summary in exactly 5 sentences
                - descriptions should be concise and factual
                - don't use ';', use ','
                - no markdown
                - no extra fields
                - population should be the latest approximate official population of the city

                language:
                - primary language spoken in the city.
                
                currency: 
                - official currency used in the country.
                
                annual_events: 
                - 6 important annual events or festivals. Each event must contain: name, month, description (one sentence)

                famous_for:
                - exactly 5 items
                - each description in 1 sentence

                districts:
                - 6 well-known districts
                - each description in 2 sentence
                - known_for should be a short phrase

                top_places:
                - exactly 6 places
                - include the city's most famous attractions
                - each description in 2 sentences
                - category must be one of:
                  Landmark, Museum, Park, Church, Square, Castle, Nature,
                  Entertainment, Shopping, Historic Site, Other

                nightlife_areas:
                - 4 areas
                - summary in 1 sentence
                - best_for should be a short phrase

                shopping_areas:
                - 4 well-known shopping streets, malls or districts

                local_foods:
                - restaurant that represents the food, consult TripAdvisor for this
                - exactly 4 traditional foods or drinks
                - each description in 1 sentence

                transportation:
                - indicate whether the city has airport, metro, tram, bus
                - bike_friendly should reflect how suitable the city is for cycling
                """
        
        else:
            prompt = f"""
                Generate structured travel data for the city of {city}, {country}.

                Rules:
                - summary must contain exactly 5 sentences
                - descriptions should be concise, factual and written in natural English
                - don't use ';', use ','
                - no markdown
                - no extra fields
                - population should be the latest approximate official population of the city
                - best_time_to_visit should be a short recommendation including the season and a brief reason

                language:
                - primary language spoken in the city.
                
                currency: 
                - official currency used in the country.
                
                annual_events: 
                - 3 important annual events or festivals. Each event must contain: name, month, description (one sentence)

                famous_for:
                - 3 items
                - each description in exactly 1 sentence
                - include the city's most recognizable landmarks, culture, history, events or industries

                districts:
                - 2 well-known districts or neighborhoods
                - each description in exactly 2 sentences
                - known_for should be a short phrase of 2-6 words

                top_places:
                - 4 places
                - prioritize the city's most famous attractions
                - avoid duplicate attractions
                - each description in exactly 2 sentences
                - category must be one of:
                  Landmark, Museum, Park, Church, Square, Castle, Nature,
                  Entertainment, Shopping, Historic Site, Other

                local_foods:
                - exactly 2 traditional foods or drinks
                - each description in 1 sentence

                transportation:
                - indicate whether the city has airport, metro, tram, bus
                - bike_friendly should reflect how suitable the city is for cycling
                """

        return prompt

    def _get_schema(self, population: int):
        if population >= 100000:
            return BigCitySchema.get()
        else:
            return CitySchema.get()

class LandmarkVariationsService(BaseDescriptionAI):
    service_name = 'landmark_variations'
    
    def generate(self, landmark: str, user=None):
        try: 
            return self._generate_cached(
                parameters={'landmark': landmark.strip().casefold()},
                prompt=self._build_prompt(landmark),
                schema=self._get_schema(),
                user=user,
            )

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": f"Request for {landmark} failed."
            }

    def _build_prompt(self, landmark: str) -> str:
        return f"""
            You are a landmark identification assistant.
            The field official_name MUST refer to {landmark}. Please provide the official name landmark.
            The city and country MUST correspond to the requested landmark.
            If you are not certain which landmark the user means, return nothing instead of guessing.
            Don't use ';', use ','

            Include:
            - official name
            - city
            - country
        """

    def _get_schema(self):
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                "official_name": { "type": "string" },
                "city": { "type": "string" },
                "country": { "type": "string" }
            },
            "required": [
                "official_name",
                "city",
                "country"
            ]
        }

class LandmarkDescriptionService(BaseDescriptionAI):
    service_name = 'landmark_description'

    def generate(self, landmark: str, city: str, country: str, user=None):
        try: 
            return self._generate_cached(
                parameters={
                    'landmark': landmark.strip().casefold(),
                    'city': city.strip().casefold(),
                    'country': country.strip().casefold(),
                },
                prompt=self._build_prompt(landmark, city, country),
                schema=LandmarkSchema.get(),
                user=user,
            )

        except Exception as e:
            print(e)
            return {
                "success": False,
                "message": f"Request for {landmark} failed."
            }

    def _build_prompt(self, landmark: str, city: str, country: str) -> str:
        return f"""
            You are an expert travel guide and historian. Generate a detailed but concise tourist guide for the given landmark {landmark}, {city}, {country}.

            Your audience is a tourist who is currently visiting the landmark. Provide engaging, accurate, and easy-to-understand information that explains the history, architecture, cultural importance, and what visitors should notice.

            Rules:
            - Follow the JSON schema exactly.
            - Do not invent facts. If information is unknown, return nothing.
            - Avoid repeating information between fields.
            - Use clear English suitable for travelers.
            - Keep descriptions informative but concise.
            - Don't use ';', use ','

            Content requirements:

            summary: Give a short introduction of 7 sentences explaining what the landmark is and why it matters.
            famous_for: Provide 3-5 main reasons it is famous.
            history: Include construction period, creator/builder, original purpose, and exactly 3 important historical events.
            - event: Describe the event in 2 sentences.
            architecture: Describe style, materials, and visible unique features.
            cultural_importance: Explain its meaning and significance.
            interesting_facts: Provide 2-4 memorable facts.
            must_see: Provide 2-5 things visitors should look for with explanations.
            best_time_to_visit: Recommend the best visiting time.
            practical_information: Include useful visitor information, tickets, accessibility, and tips.
            look_around_now: Describe details a tourist can observe while standing in front of the landmark.

            Write like a professional local guide, not like an encyclopedia.
        """
