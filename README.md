# Tonotri-Backend
The backend service powering Tonotri, an AI-powered travel and social platform that helps users discover cities, explore destinations, and connect through shared travel experiences.

# Features

- Explore countries and cities
- AI-generated travel guides and recommendations
- City and location photos
- User authentication and authorization
- Social features (posts, comments, likes) - to be done
- Messaging and notifications - to be done
- RESTful API built with Django REST Framework

# Tech Stack

- Python
- Django / Django REST Framework
- PostgreSQL
- OpenAI API
- Redis
- External APIs

# Installation

Clone the repository:

```bash
git clone https://github.com/your-username/Tonotri-Backend.git
cd Tonotri-Backend
```

Create a virtual environment:

```bash
python -m venv .venv
```
Activate it:

Windows: 
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Apply migrations:
```bash
python manage.py migrate
```

Run the development server:
```bash
python manage.py runserver
```
