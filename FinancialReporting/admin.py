from django.contrib import admin
from .models import BankHoliday, PersonnelCost, PresenceData, Reporting, EpasCode, TimesheetHint, TimesheetMissionHint, TimesheetHours

# Register your models here.
admin.site.register(BankHoliday)
admin.site.register(PersonnelCost)
admin.site.register(PresenceData)
admin.site.register(Reporting)
admin.site.register(EpasCode)
admin.site.register(TimesheetHint)
admin.site.register(TimesheetMissionHint)
admin.site.register(TimesheetHours)
