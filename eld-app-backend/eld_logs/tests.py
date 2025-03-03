from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import ELDLog
from trips.models import Trip

class ELDLogAPITests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.trip = Trip.objects.create(
            current_location="New York, NY",
            pickup_location="Boston, MA",
            dropoff_location="Philadelphia, PA",
            current_cycle_hours=20
        )

    def test_generate_log_sheets(self):
        """Test generating ELD log sheets for a trip"""
        url = reverse('generate-logs', args=[self.trip.id])  # Adjust name based on your URL configuration
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('log_sheets', response.data)

    def test_daily_log_creation(self):
        """Test creating a daily log entry"""
        log_data = {
            'trip': self.trip.id,
            'date': '2024-03-20',
            'duty_status': 'ON_DUTY',
            'location': 'New York, NY',
            'hours': 2
        }
        url = reverse('log-create')  # Adjust name based on your URL configuration
        response = self.client.post(url, log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ELDLog.objects.count(), 1)

    def test_multiple_day_trip_logs(self):
        """Test generating logs for a multi-day trip"""
        # Create a longer trip that would require multiple days
        long_trip = Trip.objects.create(
            current_location="Seattle, WA",
            pickup_location="Los Angeles, CA",
            dropoff_location="Miami, FL",
            current_cycle_hours=0
        )
        url = reverse('generate-logs', args=[long_trip.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['log_sheets']) > 1)

    def test_hours_of_service_limits(self):
        """Test HOS limits are respected in log generation"""
        log_data = {
            'trip': self.trip.id,
            'date': '2024-03-20',
            'duty_status': 'DRIVING',
            'location': 'New York, NY',
            'hours': 12  # Exceeds 11-hour driving limit
        }
        url = reverse('log-create')
        response = self.client.post(url, log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
