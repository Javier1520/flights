from django.db import models
from trips.models import Trip

class ELDLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='eld_logs')
    date = models.DateField(help_text="Date of the ELD log")
    off_duty_hours = models.FloatField(default=0.0, help_text="Hours spent off duty")
    sleeper_berth_hours = models.FloatField(default=0.0, help_text="Hours spent in sleeper berth")
    driving_hours = models.FloatField(default=0.0, help_text="Hours spent driving")
    on_duty_not_driving_hours = models.FloatField(default=0.0, help_text="Hours spent on duty but not driving")
    locations_visited = models.JSONField(default=dict, help_text="JSON field for route stops and locations visited")
    cycle_hours_used = models.FloatField(default=0.0, help_text="Cumulative hours used in the 70-hour/8-day cycle")
    cycle_hours_remaining = models.FloatField(default=70.0, help_text="Hours remaining in the 70-hour/8-day cycle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ELD Log for {self.trip} on {self.date}"

    class Meta:
        ordering = ['date']
        unique_together = ['trip', 'date']

    @property
    def total_hours(self):
        """Calculate total hours accounted for in this log"""
        return (
            self.off_duty_hours +
            self.sleeper_berth_hours +
            self.driving_hours +
            self.on_duty_not_driving_hours
        )

    @property
    def is_compliant(self):
        """Check if the log is compliant with HOS regulations"""
        # 11-hour driving limit
        if self.driving_hours > 11:
            return False

        # 14-hour on-duty limit
        if self.driving_hours + self.on_duty_not_driving_hours > 14:
            return False

        # Total hours should be 24
        if abs(self.total_hours - 24) > 0.01:  # Allow small floating-point error
            return False

        return True
