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

## Publishing messages to the queue

Publishing pending outbox messages requires both the Celery worker and Celery Beat to be running. Beat schedules the publishing task, and the worker executes it; starting only the development server is not enough.

With your virtual environment activated, run these commands in separate terminals from the directory containing `manage.py`:

```bash
celery -A TonotriBackend worker -l info -P solo
```

```bash
celery -A TonotriBackend beat -l info
```

Redis and the configured database must be available, and migrations must be applied. Alternatively, start the services with Docker Compose:

```bash
docker compose up -d --build redis celery celery-beat
```

Run only one Beat scheduler per deployment. See the [outbox publishing documentation](core/outbox/README.md) for more details.
