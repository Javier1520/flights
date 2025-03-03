from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import ELDLog
from trips.models import Trip
from django.utils import timezone
import datetime

class ELDLogAPITests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.trip = Trip.objects.create(
            current_location="New York, NY",
            pickup_location="Boston, MA",
            dropoff_location="Philadelphia, PA",
            current_cycle_hours=20.0,
            start_time=timezone.now(),
            status="planned"
        )

    def test_generate_log_sheets(self):
        """Test generating ELD log sheets for a trip"""
        url = reverse('eldlog-by-trip')
        response = self.client.get(url, {'trip_id': self.trip.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_daily_log_creation(self):
        """Test creating a daily log entry"""
        log_data = {
            'trip': self.trip.id,
            'date': '2024-03-20',
            'off_duty_hours': 10.0,
            'sleeper_berth_hours': 8.0,
            'driving_hours': 4.0,
            'on_duty_not_driving_hours': 2.0,
            'locations_visited': {"stops": []}
        }
        url = reverse('eldlog-list')
        response = self.client.post(url, log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_multiple_day_trip_logs(self):
        """Test generating logs for a multi-day trip"""
        long_trip = Trip.objects.create(
            current_location="Seattle, WA",
            pickup_location="Los Angeles, CA",
            dropoff_location="Miami, FL",
            current_cycle_hours=0.0,
            start_time=timezone.now(),
            status="planned"
        )
        url = reverse('eldlog-by-trip')
        response = self.client.get(url, {'trip_id': long_trip.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hours_of_service_limits(self):
        """Test HOS limits are respected in log generation"""
        log_data = {
            'trip': self.trip.id,
            'date': '2024-03-20',
            'off_duty_hours': 0.0,
            'sleeper_berth_hours': 0.0,
            'driving_hours': 12.0,
            'on_duty_not_driving_hours': 2.0,
            'locations_visited': {"stops": []}
        }
        url = reverse('eldlog-list')
        response = self.client.post(url, log_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class ELDLogViewSetTests(APITestCase):
    def setUp(self):
        # Create a test trip
        self.trip = Trip.objects.create(
            current_location="New York, NY",
            pickup_location="Boston, MA",
            dropoff_location="Philadelphia, PA",
            current_cycle_hours=20.0,
            start_time=timezone.now(),
            status="planned"
        )

        # Create a test ELD log
        self.eld_log = ELDLog.objects.create(
            trip=self.trip,
            date=timezone.now().date(),
            off_duty_hours=10.0,
            sleeper_berth_hours=8.0,
            driving_hours=4.0,
            on_duty_not_driving_hours=2.0,
            locations_visited={"stops": []},
            cycle_hours_used=20.0,
            cycle_hours_remaining=50.0
        )

    def test_list_eld_logs(self):
        """Test getting list of ELD logs"""
        url = reverse('eldlog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_eld_log(self):
        """Test retrieving a single ELD log"""
        url = reverse('eldlog-detail', kwargs={'pk': self.eld_log.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['trip'], self.trip.id)

    def test_filter_by_trip(self):
        """Test filtering ELD logs by trip"""
        url = reverse('eldlog-list')
        response = self.client.get(url, {'trip_id': self.trip.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_by_date_range(self):
        """Test filtering ELD logs by date range"""
        today = timezone.now().date()
        url = reverse('eldlog-list')
        response = self.client.get(url, {
            'start_date': today,
            'end_date': today
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_logs_by_trip(self):
        """Test getting logs by trip endpoint"""
        url = reverse('eldlog-by-trip')
        response = self.client.get(url, {'trip_id': self.trip.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_logs_by_trip_missing_id(self):
        """Test getting logs by trip without trip_id"""
        url = reverse('eldlog-by-trip')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_summary(self):
        """Test getting ELD logs summary"""
        url = reverse('eldlog-summary')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_driving_hours', response.data)
        self.assertIn('compliance_rate', response.data)

    def test_verify_read_only(self):
        """Test that POST/PUT/DELETE methods are not allowed"""
        url = reverse('eldlog-list')
        post_response = self.client.post(url, {})
        self.assertEqual(post_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        detail_url = reverse('eldlog-detail', kwargs={'pk': self.eld_log.pk})
        put_response = self.client.put(detail_url, {})
        self.assertEqual(put_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class ELDLogModelTests(TestCase):
    def setUp(self):
        self.trip = Trip.objects.create(
            current_location="New York, NY",
            pickup_location="Boston, MA",
            dropoff_location="Philadelphia, PA",
            current_cycle_hours=20.0,
            start_time=timezone.now(),
            status="planned"
        )

    def test_total_hours_property(self):
        """Test the total_hours property calculation"""
        log = ELDLog.objects.create(
            trip=self.trip,
            date=timezone.now().date(),
            off_duty_hours=10.0,
            sleeper_berth_hours=8.0,
            driving_hours=4.0,
            on_duty_not_driving_hours=2.0,
            locations_visited={"stops": []},
            cycle_hours_used=20.0,
            cycle_hours_remaining=50.0
        )
        self.assertEqual(log.total_hours, 10.0 + 8.0 + 4.0 + 2.0)
