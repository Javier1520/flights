import datetime
from django.utils import timezone
from .models import ELDLog
from trips.models import Trip, Stop

def generate_eld_logs_for_trip(trip):
    """
    Generate ELD logs for a trip based on its stops.
    Each day gets its own ELD log with hours allocated according to HOS regulations.
    """
    # Get all stops for the trip, ordered by sequence
    stops = trip.stops.all().order_by('sequence')
    if not stops:
        return []

    # Initialize variables
    logs = []
    current_date = trip.start_time.date()
    end_date = stops.last().arrival_time.date() + datetime.timedelta(days=1)  # Include the day after the last stop

    # Track cycle hours (70-hour/8-day limit)
    cycle_hours_used = trip.current_cycle_used

    # Generate a log for each day of the trip
    while current_date <= end_date:
        # Get stops that occur on this day
        day_stops = [
            stop for stop in stops
            if stop.arrival_time.date() <= current_date and
            (stop.arrival_time + datetime.timedelta(hours=stop.duration)).date() >= current_date
        ]

        if not day_stops:
            current_date += datetime.timedelta(days=1)
            continue

        # Initialize hours for this day
        off_duty_hours = 0.0
        sleeper_berth_hours = 0.0
        driving_hours = 0.0
        on_duty_not_driving_hours = 0.0

        # Calculate hours based on stops
        for stop in day_stops:
            stop_start = max(stop.arrival_time, datetime.datetime.combine(current_date, datetime.time.min, tzinfo=timezone.utc))
            stop_end = min(
                stop.arrival_time + datetime.timedelta(hours=stop.duration),
                datetime.datetime.combine(current_date + datetime.timedelta(days=1), datetime.time.min, tzinfo=timezone.utc)
            )

            # Calculate hours for this stop on this day
            stop_hours = (stop_end - stop_start).total_seconds() / 3600

            if stop.type == 'rest':
                # Allocate 8 hours to sleeper berth and the rest to off duty
                sleeper_berth_hours += min(8.0, stop_hours)
                off_duty_hours += max(0.0, stop_hours - 8.0)
            elif stop.type in ['pickup', 'dropoff', 'fuel']:
                on_duty_not_driving_hours += stop_hours
            elif stop.type == 'break':
                off_duty_hours += stop_hours

            # For driving time, we need to calculate time between stops
            if stop != day_stops[-1]:
                next_stop = day_stops[day_stops.index(stop) + 1]
                drive_start = stop.arrival_time + datetime.timedelta(hours=stop.duration)
                drive_end = next_stop.arrival_time

                # Only count driving that occurs on this day
                drive_start = max(drive_start, datetime.datetime.combine(current_date, datetime.time.min, tzinfo=timezone.utc))
                drive_end = min(drive_end, datetime.datetime.combine(current_date + datetime.timedelta(days=1), datetime.time.min, tzinfo=timezone.utc))

                if drive_end > drive_start:
                    drive_hours = (drive_end - drive_start).total_seconds() / 3600
                    driving_hours += drive_hours

        # Fill remaining hours with off-duty time
        total_hours = off_duty_hours + sleeper_berth_hours + driving_hours + on_duty_not_driving_hours
        if total_hours < 24:
            off_duty_hours += (24 - total_hours)

        # Update cycle hours
        on_duty_hours = driving_hours + on_duty_not_driving_hours
        cycle_hours_used += on_duty_hours

        # Remove hours from 8 days ago from the cycle
        if len(logs) >= 8:
            eight_days_ago_log = logs[-8]
            cycle_hours_used -= (eight_days_ago_log.driving_hours + eight_days_ago_log.on_duty_not_driving_hours)

        # Ensure cycle hours don't go below 0
        cycle_hours_used = max(0, cycle_hours_used)

        # Create locations visited data
        locations_visited = {
            'stops': [
                {
                    'location': stop.location,
                    'type': stop.type,
                    'arrival_time': stop.arrival_time.isoformat(),
                    'duration': stop.duration
                }
                for stop in day_stops
            ]
        }

        # Create ELD log for this day
        log = ELDLog(
            trip=trip,
            date=current_date,
            off_duty_hours=off_duty_hours,
            sleeper_berth_hours=sleeper_berth_hours,
            driving_hours=driving_hours,
            on_duty_not_driving_hours=on_duty_not_driving_hours,
            locations_visited=locations_visited,
            cycle_hours_used=cycle_hours_used,
            cycle_hours_remaining=70.0 - cycle_hours_used
        )
        logs.append(log)

        # Move to next day
        current_date += datetime.timedelta(days=1)

    # Save all logs
    ELDLog.objects.bulk_create(logs)

    return logs