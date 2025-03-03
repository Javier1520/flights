from rest_framework import serializers
from .models import Trip, Stop

class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = [
            'id', 'location', 'type', 'arrival_time',
            'duration', 'sequence', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TripSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'current_location', 'pickup_location',
            'dropoff_location', 'current_cycle_used', 'start_time',
            'total_distance', 'status', 'stops', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_distance', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validate that the current_cycle_used is within the allowed range (0-70 hours)
        """
        if 'current_cycle_used' in data and (data['current_cycle_used'] < 0 or data['current_cycle_used'] > 70):
            raise serializers.ValidationError("Current cycle used must be between 0 and 70 hours")
        return data

class TripCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = [
            'current_location', 'pickup_location',
            'dropoff_location', 'current_cycle_used'
        ]

    def validate(self, data):
        """
        Validate that the current_cycle_used is within the allowed range (0-70 hours)
        """
        if data['current_cycle_used'] < 0 or data['current_cycle_used'] > 70:
            raise serializers.ValidationError("Current cycle used must be between 0 and 70 hours")
        return data