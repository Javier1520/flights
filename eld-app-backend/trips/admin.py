from django.contrib import admin
from .models import Trip, Stop

class StopInline(admin.TabularInline):
    model = Stop
    extra = 0

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id', 'current_location', 'pickup_location', 'dropoff_location', 'status', 'start_time', 'total_distance')
    list_filter = ('status', 'start_time')
    search_fields = ('current_location', 'pickup_location', 'dropoff_location')
    inlines = [StopInline]

@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'location', 'type', 'arrival_time', 'duration', 'sequence')
    list_filter = ('type', 'arrival_time')
    search_fields = ('location',)
    ordering = ('trip', 'sequence')
