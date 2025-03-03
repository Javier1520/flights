from rest_framework import serializers
from .models import ELDLog

class ELDLogSerializer(serializers.ModelSerializer):
    total_hours = serializers.FloatField(read_only=True)
    is_compliant = serializers.BooleanField(read_only=True)

    class Meta:
        model = ELDLog
        fields = [
            'id', 'trip', 'date', 'off_duty_hours',
            'sleeper_berth_hours', 'driving_hours',
            'on_duty_not_driving_hours', 'locations_visited',
            'cycle_hours_used', 'cycle_hours_remaining',
            'total_hours', 'is_compliant',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Validate that the total hours add up to 24 hours
        """
        total_hours = (
            data.get('off_duty_hours', 0) +
            data.get('sleeper_berth_hours', 0) +
            data.get('driving_hours', 0) +
            data.get('on_duty_not_driving_hours', 0)
        )

        if abs(total_hours - 24) > 0.01:  # Allow small floating-point error
            raise serializers.ValidationError("Total hours must add up to 24 hours")

        # Validate driving hours (max 11 hours)
        if data.get('driving_hours', 0) > 11:
            raise serializers.ValidationError("Driving hours cannot exceed 11 hours")

        # Validate on-duty hours (max 14 hours)
        on_duty_total = data.get('driving_hours', 0) + data.get('on_duty_not_driving_hours', 0)
        if on_duty_total > 14:
            raise serializers.ValidationError("Total on-duty hours cannot exceed 14 hours")

        return data