from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Trip, Stop
from .serializers import TripSerializer, TripCreateSerializer, StopSerializer
from .utils import generate_stops_for_trip
from eld_logs.utils import generate_eld_logs_for_trip
from eld_logs.serializers import ELDLogSerializer

class TripViewSet(viewsets.ModelViewSet):
    """
    API endpoint for trips.
    """
    queryset = Trip.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TripCreateSerializer
        return TripSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create the trip
        trip = serializer.save()

        try:
            # Generate stops for the trip
            stops = generate_stops_for_trip(trip)

            # Generate ELD logs for the trip
            logs = generate_eld_logs_for_trip(trip)

            # Return the trip with stops and logs
            trip_serializer = TripSerializer(trip)
            return Response(trip_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            # If there's an error, delete the trip and return the error
            trip.delete()
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def stops(self, request, pk=None):
        """
        Get all stops for a trip.
        """
        trip = self.get_object()
        stops = trip.stops.all().order_by('sequence')
        serializer = StopSerializer(stops, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def eld_logs(self, request, pk=None):
        """
        Get all ELD logs for a trip.
        """
        trip = self.get_object()
        logs = trip.eld_logs.all().order_by('date')
        serializer = ELDLogSerializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def regenerate_stops(self, request, pk=None):
        """
        Regenerate stops for a trip.
        """
        trip = self.get_object()

        # Delete existing stops
        trip.stops.all().delete()

        try:
            # Generate new stops
            stops = generate_stops_for_trip(trip)

            # Return the updated trip
            serializer = TripSerializer(trip)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def regenerate_eld_logs(self, request, pk=None):
        """
        Regenerate ELD logs for a trip.
        """
        trip = self.get_object()

        # Delete existing logs
        trip.eld_logs.all().delete()

        try:
            # Generate new logs
            logs = generate_eld_logs_for_trip(trip)

            # Return the updated trip
            serializer = TripSerializer(trip)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
