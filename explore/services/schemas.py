class CountrySchema:
    @staticmethod
    def get():
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'country': {'type': 'string'},
                'summary': {'type': 'string'},
                'best_time_to_visit': {'type': 'string'},
                'currency': {'type': 'string'},
                'language': {'type': 'string'},
                'top_cities': {
                    'type': 'array',
                    'minItems': 5,
                    'maxItems': 5,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'},
                        },
                        'required': ['name', 'description']
                    }
                },
                'top_places': {
                    'type': 'array',
                    'minItems': 6,
                    'maxItems': 6,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'},
                            'category': {'type': 'string'},
                            'recommended_days': {'type': 'integer'}
                        },
                        'required': ['name', 'description', 'category', 'recommended_days']
                    }
                },
                'annual_events': {
                    'type': 'array',
                    'minItems': 9,
                    'maxItems': 9,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties':{
                            'name': {'type':'string'},
                            'city': {'type': 'string'},
                            'description': {'type': 'string'},
                            'period': {'type': 'string'},
                            'category': {'type': 'string'}
                        },
                        'required': ['name', 'city', 'description', 'period', 'category']
                    }
                },
                'travel_tips': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            },
            'required': [
                'country',
                'summary',
                'best_time_to_visit',
                'currency',
                'language',
                'top_cities',
                'top_places',
                'annual_events',
                'travel_tips'
            ]
        }


class BigCitySchema:

    @staticmethod
    def get():
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'city': {'type': 'string'},
                'country': {'type': 'string'},
                'summary': {'type': 'string'},
                'population': {'type': 'integer'},
                'best_time_to_visit': {'type': 'string'},
                'currency': {'type': 'string'},
                'language': {'type': 'string'},
                'annual_events': {
                    'type': 'array',
                    'minItems': 6,
                    'maxItems': 6,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties':{
                            'name': {'type':'string'},
                            'description': {'type': 'string'},
                            'period': {'type': 'string'},
                            'category': {'type': 'string'}
                        },
                        'required': ['name', 'description', 'period', 'category']
                    }
                },
                'famous_for': {
                    'type': 'array',
                    'minItems': 5,
                    'maxItems': 5,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'}
                        },
                        'required': [
                            'name',
                            'description'
                        ]
                    }
                },
                'districts': {
                    'type': 'array',
                    'minItems': 6,
                    'maxItems': 6,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'},
                            'known_for': {'type': 'string'}
                        },
                        'required': [
                            'name',
                            'description',
                            'known_for'
                        ]
                    }
                },
                'top_places': {
                    'type': 'array',
                    'minItems': 6,
                    'maxItems': 6,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'},
                            'category': {'type': 'string'}
                        },
                        'required': [
                            'name',
                            'description',
                            'category'
                        ]
                    }
                },
                'nightlife_areas': {
                    'type': 'array',
                    'minItems': 4,
                    'maxItems': 4,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': { 'type': 'string' },
                            'summary': { 'type': 'string' },
                            'best_for': { 'type': 'string' }
                        },
                        'required': [
                            'name',
                            'summary',
                            'best_for'
                        ]
                    }
                },
                'shopping_areas': {
                    'type': 'array',
                    'min_items': 4,
                    'max_items': 4,
                    'items': { 
                        'type': 'object', 
                        'additionalProperties': False,
                        'properties': {
                            'name': { 'type': 'string' },
                            'description': { 'type': 'string' }
                        },
                        'required': [
                            'name',
                            'description'
                        ]
                    },
                },
                'local_foods': {
                    'type': 'array',
                    'minItems': 4,
                    'maxItems': 4,
                    'items': { 
                        'type': 'object', 
                        'additionalProperties': False,
                        'properties': {
                            'name': { 'type': 'string' },
                            'description': { 'type': 'string' }
                        },
                        'required': [
                            'name',
                            'description'
                        ]
                    },
                },
                'transportation': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'airport': { 'type': 'boolean' },
                        'metro': { 'type': 'boolean' },
                        'tram': { 'type': 'boolean' },
                        'bus': { 'type': 'boolean' },
                        'bike_friendly': { 'type': 'boolean' }
                    },
                    'required': [ 
                        'airport',
                        'metro',
                        'tram',
                        'bus',
                        'bike_friendly'
                    ]
                },
                'travel_tips': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            },
            'required': [
                'city',
                'country',
                'summary',
                'population',
                'best_time_to_visit',
                'currency',
                'language',
                'annual_events',
                'famous_for',
                'districts',
                'top_places',
                'nightlife_areas',
                'shopping_areas',
                'local_foods',
                'transportation',
                'travel_tips'
            ]
        }


class CitySchema:
    
    @staticmethod
    def get():
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'city': { 'type': 'string' },
                'country': { 'type': 'string' },
                'summary': { 'type': 'string' },
                'population': { 'type': 'integer' },
                'best_time_to_visit': { 'type': 'string' },
                'currency': {'type': 'string'},
                'language': {'type': 'string'},
                'annual_events': {
                    'type': 'array',
                    'minItems': 3,
                    'maxItems': 3,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties':{
                            'name': {'type':'string'},
                            'description': {'type': 'string'},
                            'period': {'type': 'string'},
                            'category': {'type': 'string'}
                        },
                        'required': ['name', 'description', 'period', 'category']
                    }
                },
                'famous_for': {
                    'type': 'array',
                    'minItems': 3,
                    'maxItems': 3,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': { 'type': 'string' },
                            'description': { 'type': 'string' },
                        },
                        'required': [ 'name', 'description' ]
                    }
                },
                'districts': {
                    'type': 'array',
                    'minItems': 2,
                    'maxItems': 2,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': { 'type': 'string' },
                            'description': { 'type': 'string' },
                            'known_for': { 'type': 'string' }
                        },
                        'required': [ 'name', 'description', 'known_for' ]
                    }
                },
                'top_places': {
                    'type': 'array',
                    'minItems': 4,
                    'maxItems': 4,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': { 'type': 'string' },
                            'description': { 'type': 'string' },
                            'category': { 
                                'type': 'string',
                                'enum': [
                                    'Landmark',
                                    'Museum',
                                    'Park',
                                    'Church',
                                    'Square',
                                    'Castle',
                                    'Nature',
                                    'Entertainment',
                                    'Shopping',
                                    'Historic Site',
                                    'Other'
                                ]    
                            }
                        },
                        'required': [ 'name', 'description', 'category' ]
                    }
                },
                'local_foods': {
                    'type': 'array',
                    'minItems': 2,
                    'maxItems': 2,
                    'items': {
                        'type': 'object',
                        'additionalProperties': False,
                        'properties': {
                            'name': {'type': 'string'},
                            'description': {'type': 'string'},
                        },
                        'required': ['name', 'description']
                    }
                },
                'transportation': {
                    'type': 'object',
                    'additionalProperties': False,
                    'properties': {
                        'airport': { 'type': 'boolean' },
                        'metro': { 'type': 'boolean' },
                        'tram': { 'type': 'boolean' },
                        'bus': { 'type': 'boolean' },
                        'bike_friendly': { 'type': 'boolean' }
                    },
                    'required': [ 
                        'airport',
                        'metro',
                        'tram',
                        'bus',
                        'bike_friendly'
                    ]
                },
                'travel_tips': {
                    'type': 'array',
                    'items': {'type': 'string'}
                }
            },
            'required': [
                'city',
                'country',
                'summary',
                'population',
                'best_time_to_visit',
                'language',
                'currency',
                'annual_events',
                'famous_for',
                'districts',
                'top_places',
                'local_foods',
                'transportation',
                'travel_tips'
            ]
        }

class LandmarkSchema:
    @staticmethod
    def get():
        return {
            'type': 'object',
            'additionalProperties': False,
            'properties': {
                'official_name': { 'type': 'string' },
                'summary': { 'type': 'string' },
                'famous_for': {
                    'type': 'array',
                    'items': { 'type': 'string' },
                    'minItems': 3,
                    'maxItems': 5
                },
                'history': {
                    'type': 'object',
                    'properties': {
                        'construction_period': { 'type': 'string' },
                        'built_by': { 'type': 'string' },
                        'original_purpose': { 'type': 'string' },
                        'historical_events': {
                            'type': 'array',
                            'minItems': 3,
                            'maxItems': 3,
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'year': { 'type': 'string' },
                                    'event': { 'type': 'string' }
                                },
                                'required': [
                                    'year',
                                    'event'
                                ],
                                'additionalProperties': False
                            }
                        }
                    },
                    'required': [ 
                        'construction_period', 
                        'built_by',
                        'original_purpose',
                        'historical_events'  
                    ],
                    'additionalProperties': False
                },
                'architecture': {
                    'type': 'object',
                    'properties': {
                        'style': { 'type': 'string' },
                        'materials': { 
                            'type': 'array',
                            'items': { 'type': 'string' },
                            'minItems': 2,
                            'maxItems': 6
                        },
                        'notable_features': {
                            'type': 'array',
                            'items': { 'type': 'string' },
                            'minItems': 2,
                            'maxItems': 5
                        }
                    },
                    'required': [
                        'style',
                        'materials',
                        'notable_features'
                    ],
                    'additionalProperties': False
                },
                'cultural_importance': { 'type': 'string' },
                'interesting_facts': {
                    'type': 'array',
                    'items': { 'type': 'string' },
                    'minItems': 2,
                    'maxItems': 4
                },
                'must_see': {
                    'type': 'array',
                    'minItems': 2,
                    'maxItems': 5,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': { 'type': 'string' },
                            'description': { 'type': 'string' }
                        },
                        'required': [
                            'name',
                            'description'
                        ],
                        'additionalProperties': False
                    }
                },
                'best_time_to_visit': { 'type': 'string' },
                'practical_information': {
                    'type': 'object',
                    'properties': {
                        'opening_hours': { 'type': 'string' },
                        'ticket_information': { 'type': 'string' },
                        'accessibility': { 'type' : 'string' },
                        'visitor_tips': {
                            'type': 'array',
                            'items': { 'type': 'string' },
                            'minItems': 2,
                            'maxItems': 4
                        },
                    },
                    'required': [
                            'opening_hours',
                            'ticket_information',
                            'accessibility',
                            'visitor_tips'
                    ],
                    'additionalProperties': False
                },
                'look_around_now': {
                    'type': 'array',
                    'description': 'Specific details a tourist should observe while standing in front of the landmark.',
                    'items': {
                        'type': 'string'
                    },
                    'minItems': 2,
                    'maxItems': 5
                },
            },
            'required': [
                'official_name',
                'summary',
                'famous_for',
                'history',
                'architecture',
                'cultural_importance',
                'interesting_facts',
                'must_see',
                'look_around_now',
                'best_time_to_visit',
                'practical_information',
            ]
        }