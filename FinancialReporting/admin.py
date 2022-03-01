from django.contrib import admin
from .models import Researcher, Project, WorkPackage, BankHoliday, PersonnelCost, PresenceData, Reporting, EpasCode, TimesheetHint, TimesheetMissionHint, TimesheetHours

# Register your models here.
admin.site.register(Researcher)
admin.site.register(Project)
admin.site.register(WorkPackage)
admin.site.register(BankHoliday)
admin.site.register(PersonnelCost)
admin.site.register(PresenceData)
admin.site.register(Reporting)
admin.site.register(EpasCode)
admin.site.register(TimesheetHint)
admin.site.register(TimesheetMissionHint)
admin.site.register(TimesheetHours)
