import os
import requests
import datetime
from django.conf import settings
from django.utils import timezone
from .models import Trip, Stop

def get_coordinates(location):
    """
    Convert a location string to coordinates using OpenRouteService geocoding API.
    Returns a tuple of (longitude, latitude).
    """
    api_key = settings.OPENROUTESERVICE_API_KEY
    if not api_key:
        raise ValueError("OpenRouteService API key is not set")

    # If location is already in coordinate format (e.g., "-73.935242,40.730610"), return it
    if ',' in location and all(part.replace('.', '').replace('-', '').isdigit() for part in location.split(',')):
        lon, lat = location.split(',')
        return float(lon), float(lat)

    # Otherwise, geocode the location
    url = f"https://api.openrouteservice.org/geocode/search"
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    params = {
        'text': location,
        'size': 1
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise ValueError(f"Failed to geocode location: {response.text}")

    data = response.json()
    if not data.get('features') or len(data['features']) == 0:
        raise ValueError(f"No coordinates found for location: {location}")

    # Extract coordinates (longitude, latitude)
    coordinates = data['features'][0]['geometry']['coordinates']
    return coordinates[0], coordinates[1]

def calculate_route(origin, destination):
    """
    Calculate a route between two locations using OpenRouteService API.
    Returns a dictionary with distance (in meters), duration (in seconds), and waypoints.
    """
    api_key = settings.OPENROUTESERVICE_API_KEY
    if not api_key:
        raise ValueError("OpenRouteService API key is not set")

    # Convert locations to coordinates if they're not already
    origin_coords = get_coordinates(origin)
    destination_coords = get_coordinates(destination)

    url = "https://api.openrouteservice.org/v2/directions/driving-hgv"
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json; charset=utf-8'
    }
    data = {
        'coordinates': [origin_coords, destination_coords],
        'instructions': True,
        'format': 'geojson'
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise ValueError(f"Failed to calculate route: {response.text}")

    route_data = response.json()

    # Extract relevant information
    features = route_data.get('features', [])
    if not features:
        raise ValueError("No route found")

    properties = features[0].get('properties', {})
    segments = properties.get('segments', [])
    if not segments:
        raise ValueError("No route segments found")

    # Get total distance (in meters) and duration (in seconds)
    distance = segments[0].get('distance', 0)  # meters
    duration = segments[0].get('duration', 0)  # seconds

    # Get waypoints
    geometry = features[0].get('geometry', {})
    waypoints = geometry.get('coordinates', [])

    return {
        'distance': distance,
        'duration': duration,
        'waypoints': waypoints
    }

def meters_to_miles(meters):
    """Convert meters to miles"""
    return meters * 0.000621371

def seconds_to_hours(seconds):
    """Convert seconds to hours"""
    return seconds / 3600

def generate_stops_for_trip(trip):
    """
    Generate stops for a trip, including pickup, dropoff, rest stops, and fuel stops.
    """
    # Calculate route from current location to pickup
    try:
        current_to_pickup = calculate_route(trip.current_location, trip.pickup_location)
        pickup_to_dropoff = calculate_route(trip.pickup_location, trip.dropoff_location)
    except ValueError as e:
        raise ValueError(f"Error calculating route: {str(e)}")

    # Convert distances to miles and durations to hours
    current_to_pickup_distance = meters_to_miles(current_to_pickup['distance'])
    current_to_pickup_duration = seconds_to_hours(current_to_pickup['duration'])

    pickup_to_dropoff_distance = meters_to_miles(pickup_to_dropoff['distance'])
    pickup_to_dropoff_duration = seconds_to_hours(pickup_to_dropoff['duration'])

    # Calculate total distance and update trip
    total_distance = current_to_pickup_distance + pickup_to_dropoff_distance
    trip.total_distance = total_distance
    trip.save()

    # Initialize variables
    stops = []
    current_time = trip.start_time
    current_driving_hours = 0
    current_duty_hours = 0
    sequence = 1

    # Add pickup stop
    pickup_arrival_time = current_time + datetime.timedelta(hours=current_to_pickup_duration)
    stops.append(Stop(
        trip=trip,
        location=trip.pickup_location,
        type='pickup',
        arrival_time=pickup_arrival_time,
        duration=1.0,  # 1 hour for pickup
        sequence=sequence
    ))

    # Update time and hours
    current_time = pickup_arrival_time + datetime.timedelta(hours=1)
    current_driving_hours += current_to_pickup_duration
    current_duty_hours += current_to_pickup_duration + 1  # Driving + pickup time
    sequence += 1

    # Check if we need a rest stop after pickup
    if current_driving_hours >= 8:
        # Add a 30-minute break after 8 hours of driving
        stops.append(Stop(
            trip=trip,
            location=trip.pickup_location,  # Break at the pickup location
            type='break',
            arrival_time=current_time,
            duration=0.5,  # 30 minutes
            sequence=sequence
        ))
        current_time += datetime.timedelta(hours=0.5)
        current_duty_hours += 0.5
        current_driving_hours = 0  # Reset driving hours after break
        sequence += 1

    # Check if we need a rest stop during the drive to dropoff
    remaining_drive_time = pickup_to_dropoff_duration
    current_location = trip.pickup_location

    # If the remaining drive time would exceed 11 hours of driving or 14 hours on duty,
    # we need to add rest stops
    while remaining_drive_time > 0:
        # How much more driving can be done before hitting limits
        driving_limit = min(11 - current_driving_hours, 14 - current_duty_hours)

        if driving_limit <= 0 or current_duty_hours >= 14:
            # Need a 10-hour rest period (8 hours in sleeper berth + 2 hours off duty)
            stops.append(Stop(
                trip=trip,
                location=current_location,
                type='rest',
                arrival_time=current_time,
                duration=10.0,
                sequence=sequence
            ))
            current_time += datetime.timedelta(hours=10)
            current_driving_hours = 0
            current_duty_hours = 0
            sequence += 1
            continue

        if driving_limit < remaining_drive_time:
            # Drive as much as allowed, then add a rest stop
            # For simplicity, we'll assume we can find a rest stop at the right time
            drive_time = driving_limit
            remaining_drive_time -= drive_time

            # Update current location (simplified - in reality would need to find a point along the route)
            # Here we just use the dropoff location as a placeholder
            current_location = trip.dropoff_location

            current_time += datetime.timedelta(hours=drive_time)
            current_driving_hours += drive_time
            current_duty_hours += drive_time

            # Add a rest stop
            stops.append(Stop(
                trip=trip,
                location=current_location,
                type='rest',
                arrival_time=current_time,
                duration=10.0,  # 10-hour rest period
                sequence=sequence
            ))
            current_time += datetime.timedelta(hours=10)
            current_driving_hours = 0
            current_duty_hours = 0
            sequence += 1
        else:
            # Can complete the remaining drive without a rest
            current_time += datetime.timedelta(hours=remaining_drive_time)
            current_driving_hours += remaining_drive_time
            current_duty_hours += remaining_drive_time
            remaining_drive_time = 0

    # Add fuel stops if the total distance is over 1000 miles
    # For simplicity, we'll add one fuel stop for every 1000 miles
    fuel_stops_needed = int(total_distance / 1000)
    if fuel_stops_needed > 0:
        # Simplified: add fuel stops at equal intervals
        for i in range(fuel_stops_needed):
            # Calculate a position along the route (simplified)
            fuel_stop_location = trip.dropoff_location  # Placeholder

            stops.append(Stop(
                trip=trip,
                location=fuel_stop_location,
                type='fuel',
                arrival_time=current_time - datetime.timedelta(hours=pickup_to_dropoff_duration / 2),  # Approximate middle of journey
                duration=0.5,  # 30 minutes for fueling
                sequence=sequence
            ))
            sequence += 1

    # Add dropoff stop
    stops.append(Stop(
        trip=trip,
        location=trip.dropoff_location,
        type='dropoff',
        arrival_time=current_time,
        duration=1.0,  # 1 hour for dropoff
        sequence=sequence
    ))

    # Save all stops
    Stop.objects.bulk_create(stops)

    return stops