# ELD App Backend

A Django backend for an app that manages truck driver trips and generates Electronic Logging Device (ELD) logs.

## Features

- Trip management with route planning
- Rest stop calculation based on Hours of Service (HOS) regulations
- Automatic fueling stop recommendations
- ELD log generation compliant with FMCSA regulations

## Requirements

- Python 3.8+
- Django 5.1+
- Django Rest Framework 3.15+
- OpenRouteService API key (for route calculations)

## Setup

1. Clone the repository:

   ```
   git clone <repository-url>
   cd eld-app-backend
   ```

2. Create and activate a virtual environment:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:

   ```
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   OPENROUTESERVICE_API_KEY=your_openrouteservice_api_key
   ```

5. Run migrations:

   ```
   python manage.py migrate
   ```

6. Start the development server:
   ```
   python manage.py runserver
   ```

## API Endpoints

- `POST /api/trips/`: Create a new trip
- `GET /api/trips/`: List all trips
- `GET /api/trips/<id>/`: Retrieve trip details, including route and ELD logs

## HOS Regulations Implemented

- 11-hour driving limit
- 14-hour on-duty limit
- 70-hour/8-day limit
- 10-hour off-duty requirement
- 30-minute break requirement after 8 hours of driving
