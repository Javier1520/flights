from django.db import models
from django.utils import timezone

class Trip(models.Model):
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    current_location = models.CharField(max_length=255, help_text="Current location as string or coordinates")
    pickup_location = models.CharField(max_length=255, help_text="Pickup location as string or coordinates")
    dropoff_location = models.CharField(max_length=255, help_text="Dropoff location as string or coordinates")
    current_cycle_hours = models.FloatField(help_text="Current cycle hours used (in hours)")
    start_time = models.DateTimeField(default=timezone.now, help_text="Trip start time")
    total_distance = models.FloatField(null=True, blank=True, help_text="Total trip distance (in miles)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned', help_text="Trip status")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trip from {self.current_location} to {self.dropoff_location} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class Stop(models.Model):
    STOP_TYPE_CHOICES = [
        ('rest', 'Rest Stop'),
        ('fuel', 'Fuel Stop'),
        ('pickup', 'Pickup'),
        ('dropoff', 'Dropoff'),
        ('break', 'Break'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    location = models.CharField(max_length=255, help_text="Stop location as string or coordinates")
    type = models.CharField(max_length=20, choices=STOP_TYPE_CHOICES, help_text="Type of stop")
    arrival_time = models.DateTimeField(help_text="Estimated arrival time at the stop")
    duration = models.FloatField(help_text="Duration of the stop (in hours)")
    sequence = models.PositiveIntegerField(help_text="Sequence number of the stop in the trip")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_type_display()} at {self.location}"

    class Meta:
        ordering = ['sequence']
