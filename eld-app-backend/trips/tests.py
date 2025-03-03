from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Trip

class TripAPITests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.trip_data = {
            "current_location": "New York, NY",
            "pickup_location": "Boston, MA",
            "dropoff_location": "Philadelphia, PA",
            "current_cycle_hours": 20
        }

    def test_create_trip(self):
        """Test creating a new trip"""
        url = reverse('trip-create')  # Adjust name based on your URL configuration
        response = self.client.post(url, self.trip_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Trip.objects.count(), 1)

    def test_get_route_instructions(self):
        """Test getting route instructions for a trip"""
        # First create a trip
        trip = Trip.objects.create(**self.trip_data)
        url = reverse('trip-route', args=[trip.id])  # Adjust name based on your URL configuration
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('route', response.data)

    def test_invalid_location(self):
        """Test handling invalid location input"""
        invalid_data = self.trip_data.copy()
        invalid_data['current_location'] = "NonexistentPlace123"
        url = reverse('trip-create')
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cycle_hours_validation(self):
        """Test validation of cycle hours"""
        invalid_data = self.trip_data.copy()
        invalid_data['current_cycle_hours'] = 80  # Over 70-hour limit
        url = reverse('trip-create')
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
