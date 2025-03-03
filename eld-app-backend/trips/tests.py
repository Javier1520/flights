from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Trip, Stop
from django.utils import timezone

class TripViewSetTests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.trip_data = {
            "current_location": "New York, NY",
            "pickup_location": "Boston, MA",
            "dropoff_location": "Philadelphia, PA",
            "current_cycle_hours": 20.0,
            "start_time": timezone.now().isoformat(),
            "status": "planned"
        }
        # Create a test trip
        self.trip = Trip.objects.create(**self.trip_data)
        # Create some test stops
        self.stop = Stop.objects.create(
            trip=self.trip,
            location="Test Location",
            type="rest",
            arrival_time=timezone.now(),
            duration=1.0,
            sequence=1
        )

    def test_list_trips(self):
        """Test getting list of trips"""
        url = reverse('trip-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_trip(self):
        """Test creating a new trip"""
        url = reverse('trip-list')
        new_trip_data = self.trip_data.copy()
        new_trip_data['current_location'] = "Chicago, IL"
        response = self.client.post(url, new_trip_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Trip.objects.count(), 2)

    def test_retrieve_trip(self):
        """Test retrieving a single trip"""
        url = reverse('trip-detail', kwargs={'pk': self.trip.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['current_location'], self.trip_data['current_location'])

    def test_update_trip(self):
        """Test updating a trip"""
        url = reverse('trip-detail', kwargs={'pk': self.trip.pk})
        updated_data = self.trip_data.copy()
        updated_data['status'] = 'in_progress'
        response = self.client.put(url, updated_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_progress')

    def test_partial_update_trip(self):
        """Test partially updating a trip"""
        url = reverse('trip-detail', kwargs={'pk': self.trip.pk})
        response = self.client.patch(url, {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')

    def test_delete_trip(self):
        """Test deleting a trip"""
        url = reverse('trip-detail', kwargs={'pk': self.trip.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Trip.objects.count(), 0)

    def test_get_stops(self):
        """Test getting stops for a trip"""
        url = reverse('trip-stops', kwargs={'pk': self.trip.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_eld_logs(self):
        """Test getting ELD logs for a trip"""
        url = reverse('trip-eld-logs', kwargs={'pk': self.trip.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regenerate_stops(self):
        """Test regenerating stops for a trip"""
        url = reverse('trip-regenerate-stops', kwargs={'pk': self.trip.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_regenerate_eld_logs(self):
        """Test regenerating ELD logs for a trip"""
        url = reverse('trip-regenerate-eld-logs', kwargs={'pk': self.trip.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_cycle_hours(self):
        """Test validation of cycle hours"""
        url = reverse('trip-list')
        invalid_data = self.trip_data.copy()
        invalid_data['current_cycle_hours'] = 80.0  # Over 70-hour limit
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_route_instructions(self):
        """Test getting route instructions for a trip"""
        url = reverse('trip-route', args=[self.trip.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('route', response.data)

    def test_invalid_location(self):
        """Test handling invalid location input"""
        invalid_data = self.trip_data.copy()
        invalid_data['current_location'] = "NonexistentPlace123"
        url = reverse('trip-list')
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cycle_hours_validation(self):
        """Test validation of cycle hours"""
        invalid_data = self.trip_data.copy()
        invalid_data['current_cycle_hours'] = 80.0  # Over 70-hour limit
        url = reverse('trip-list')
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
