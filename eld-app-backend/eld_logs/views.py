from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ELDLog
from .serializers import ELDLogSerializer
from trips.models import Trip

class ELDLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for ELD logs (read-only).
    """
    queryset = ELDLog.objects.all()
    serializer_class = ELDLogSerializer

    def get_queryset(self):
        queryset = ELDLog.objects.all()

        # Filter by trip if trip_id is provided
        trip_id = self.request.query_params.get('trip_id', None)
        if trip_id is not None:
            queryset = queryset.filter(trip_id=trip_id)

        # Filter by date range if start_date and end_date are provided
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date is not None:
            queryset = queryset.filter(date__gte=start_date)

        if end_date is not None:
            queryset = queryset.filter(date__lte=end_date)

        return queryset

    @action(detail=False, methods=['get'])
    def by_trip(self, request):
        """
        Get all ELD logs for a specific trip.
        """
        trip_id = request.query_params.get('trip_id', None)
        if trip_id is None:
            return Response(
                {"error": "trip_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        trip = get_object_or_404(Trip, pk=trip_id)
        logs = self.get_queryset().filter(trip=trip).order_by('date')
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get a summary of ELD logs for a specific trip or date range.
        """
        logs = self.get_queryset()

        if not logs:
            return Response(
                {"error": "No logs found for the specified filters"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate summary statistics
        total_driving_hours = sum(log.driving_hours for log in logs)
        total_on_duty_hours = sum(log.on_duty_not_driving_hours for log in logs)
        total_off_duty_hours = sum(log.off_duty_hours for log in logs)
        total_sleeper_berth_hours = sum(log.sleeper_berth_hours for log in logs)

        # Calculate averages
        log_count = logs.count()
        avg_driving_hours = total_driving_hours / log_count if log_count > 0 else 0
        avg_on_duty_hours = total_on_duty_hours / log_count if log_count > 0 else 0

        # Check compliance
        compliant_logs = sum(1 for log in logs if log.is_compliant)
        compliance_rate = (compliant_logs / log_count) * 100 if log_count > 0 else 0

        summary = {
            'log_count': log_count,
            'total_driving_hours': total_driving_hours,
            'total_on_duty_hours': total_on_duty_hours,
            'total_off_duty_hours': total_off_duty_hours,
            'total_sleeper_berth_hours': total_sleeper_berth_hours,
            'avg_driving_hours': avg_driving_hours,
            'avg_on_duty_hours': avg_on_duty_hours,
            'compliant_logs': compliant_logs,
            'compliance_rate': compliance_rate,
        }

        return Response(summary)
