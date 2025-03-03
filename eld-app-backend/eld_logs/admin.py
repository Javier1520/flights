from django.contrib import admin
from .models import ELDLog

@admin.register(ELDLog)
class ELDLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'date', 'driving_hours', 'on_duty_not_driving_hours', 'off_duty_hours', 'sleeper_berth_hours', 'is_compliant')
    list_filter = ('date',)
    search_fields = ('trip__current_location', 'trip__pickup_location', 'trip__dropoff_location')
    readonly_fields = ('total_hours', 'is_compliant')

    def is_compliant(self, obj):
        return obj.is_compliant
    is_compliant.boolean = True
    is_compliant.short_description = 'Compliant'
