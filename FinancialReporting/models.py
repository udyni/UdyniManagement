from django.db import models
from django.core.exceptions import ValidationError


# Financial reporting models
# ==========================


class Researcher(models.Model):
    """ Researchers' registry
    """
    # Name
    name = models.CharField(max_length=200)
    # Surname
    surname = models.CharField(max_length=200)

    class Meta:
        ordering = ["surname", "name"]
        constraints = [
            models.UniqueConstraint(fields=['name', 'surname'], name="%(app_label)s_%(class)s_unique"),
        ]

    def __str__(self):
        return self.name + " " + self.surname


class ResearcherRole(models.Model):
    """ Researcher role for each period
    """
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE)
    # Role
    RESEARCHER = "RI"
    SENIOR = "PR"
    DIRECTOR = "DR"
    role = models.CharField(
        max_length=2,
        choices=[
            (RESEARCHER, "Researcher"),
            (SENIOR, "Senior Researcher"),
            (DIRECTOR, "Research Director"),
        ],
        default=RESEARCHER,
    )
    start_date = models.DateField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['researcher', 'start_date'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["researcher", "start_date"]

    def __str__(self):
        return "{0:s} from {1:s}".format(self.get_role_display(), self.start_date.isoformat())


class Project(models.Model):
    """ Projects' task registry
    """
    name = models.CharField(max_length=100)
    agency = models.CharField(max_length=200)
    reference = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["name", ]

    def __str__(self):
        return self.name + " (" + self.agency + ", " + self.reference + ")"

    def get_workpackages(self):
        return WorkPackage.objects.filter(project=self)

    workpackages = property(get_workpackages)


class WorkPackage(models.Model):
    """ Work packages in projects
        NOTE: every project have an unnamed WP that means generic work on a project
    """
    # Project
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    # WP name
    name = models.CharField(max_length=100)
    # WP description
    desc = models.CharField(max_length=200, default="")

    def __str__(self):
        # return "{0:s} of {1!s}".format(self.name, self.project)
        return "{0:s}: {1:s}".format(self.name, self.desc)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['project', 'name'], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["project__name", "name", ]


class BankHoliday(models.Model):
    """ List of bank holidays
    """
    name = models.CharField(max_length=200)
    day = models.PositiveIntegerField()

    MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    month = models.PositiveIntegerField(choices=[(i + 1, m) for i, m in enumerate(MONTHS)])
    year = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['year', 'month', 'day', ], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["year", "month", "day"]

    def __str__(self):
        if self.year != 0:
            return self.name + " on {0:02d}/{1:02d}/{2:04d}".format(self.day, self.month, self.year)
        else:
            return self.name + " on {0!s} {1:d}".format(self.get_month_display(), self.day)


class PersonnelCost(models.Model):
    """ Registry of personnel cost by year
    """
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE)
    year = models.PositiveIntegerField()
    working_hours = models.PositiveIntegerField()
    cost = models.FloatField()

    def __str__(self):
        return "{0!s} cost of {1:d}: {2:.2f}".format(self.researcher, self.year, self.cost)

    class Meta:
        ordering = ["year", "researcher"]
        constraints = [
            models.UniqueConstraint(fields=['year', 'researcher'], name="%(app_label)s_%(class)s_unique"),
        ]


class EpasCode(models.Model):
    """ EPAS absence codes
    """
    code = models.CharField(max_length=32, unique=True)
    NONE = ""
    HOLIDAYS = "HO"
    MISSION = "MI"
    ILLNESS = "IL"
    OTHER = "OA"
    CHOICES = [
        (NONE, "None"),
        (HOLIDAYS, "Holidays"),
        (MISSION, "Mission"),
        (ILLNESS, "Illness"),
        (OTHER, "Other absences"),
    ]
    ts_code = models.CharField(
        max_length=2,
        choices=CHOICES,
        default=NONE,
    )
    description = models.CharField(max_length=256)

    def __str__(self):
        return "Code {0:s}: {1:s} (TS: {2:s})".format(self.code, self.description, self.get_ts_code_display())

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', ], name="%(app_label)s_%(class)s_unique"),
        ]
        ordering = ["code", ]


class PresenceData(models.Model):
    """ Presence data; hours, TS hours, absences, missions, ecc.
    """
    # Reserarcher
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE)
    # Working day
    day = models.DateField()
    # Actual worked hours (from accounting system)
    hours = models.FloatField()
    # Corrected timesheet hours
    ts_hours = models.FloatField()
    # Abscence code
    code = models.ForeignKey(EpasCode, on_delete=models.PROTECT, null=True, blank=True)
    # Absence code for ts
    ts_code = models.CharField(max_length=2, choices=EpasCode.CHOICES, default=EpasCode.NONE)

    def __str__(self):
        if self.code is None or self.code.ts_code == EpasCode.NONE:
            return "{0!s} on {1!s} worked for {2:.1f} hours".format(self.researcher, self.day, self.hours)
        else:
            return "{0!s} on {1!s} was absent for {2!s}".format(self.researcher, self.day, self.code.get_ts_code_display())

    class Meta:
        ordering = ["researcher", "day"]
        constraints = [
            models.UniqueConstraint(fields=['researcher', 'day'], name="%(app_label)s_%(class)s_unique"),
        ]


class Reporting(models.Model):
    """ Reporting of hours worked on projects
    """
    researcher = models.ForeignKey(Researcher, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    wp = models.ForeignKey(WorkPackage, on_delete=models.CASCADE, null=True, blank=True)
    rp_start = models.DateField()
    rp_end = models.DateField()
    hours = models.FloatField()
    has_missions = models.BooleanField(default=False)
    cost = models.ForeignKey(PersonnelCost, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['researcher', 'project', 'wp', 'rp_start', 'rp_end'],
                name="%(app_label)s_%(class)s_unique"
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_start_lt_end",
                check=models.Q(rp_start__lt=models.F("rp_end")),
            ),
        ]

    def clean(self):
        if self.pk is not None:
            # This is an update
            pass
        else:
            # First check that WP and project are consistent
            if self.wp is not None and self.wp.project.pk != self.project.pk:
                raise ValidationError({'wp': ValidationError("The workpackage must refer to the selected project")})
            # Check that the reporting period does not overlap with others
            for rp in Reporting.objects.filter(project=self.project):
                if self.wp is not None:
                    if rp.wp != self.wp:
                        continue
                if self.rp_start >= rp.rp_start and self.rp_start <= rp.rp_end:
                    raise ValidationError({'rp_start': ValidationError("The start date of the reporting period overlaps with another period for the same project/wp")})
                if self.rp_end >= rp.rp_start and self.rp_end <= rp.rp_end:
                    raise ValidationError({'rp_end': ValidationError("The end date of the reporting period overlaps with another period for the same project/wp")})

    def __str__(self):
        return "{0!s} worked {1:.1f} hours on {2!s} from {3!s} to {4!s}".format(self.researcher, self.hours, self.project, self.rp_start, self.rp_end)


class TimesheetHint(models.Model):
    """ Hints to generate timesheets
    """
    reporting_period = models.ForeignKey(Reporting, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()
    hours = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reporting_period', 'year', 'month'], name="%(app_label)s_%(class)s_unique"),
        ]

    def __str__(self):
        return ("{0!s} on {1!s}, WP {2!s} - {3:d}/{4:d} = {5:.1f}"
                .format(
                    self.reporting_period.researcher,
                    self.reporting_period.project,
                    self.reporting_period.wp,
                    self.year,
                    self.month,
                    self.hours)
                )


class TimesheetMissionHint(models.Model):
    """ Hints to assign missions to reporting periods
        NOTE: missions without hints will be assigned to 'Internal activities'
    """
    reporting_period = models.ForeignKey(Reporting, on_delete=models.CASCADE)
    missionday = models.ForeignKey(PresenceData, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            # Each mission day can be related to only one reporting period
            models.UniqueConstraint(
                fields=['missionday', ],
                name="%(app_label)s_%(class)s_unique"
            ),
        ]

    def clean(self):
        # Check that presence data object referenced by missionday is indeed a
        # mission (ts_code == EpasCode.MISSION)
        if self.missionday.ts_code != EpasCode.MISSION:
            raise ValidationError('Mission day must have the ts_code set to MISSION')


class TimesheetHours(models.Model):
    """ Hours recorded on timesheets for each day
    """
    reporting_period = models.ForeignKey(Reporting, on_delete=models.CASCADE)
    day = models.DateField()
    hours = models.FloatField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['reporting_period', 'day'], name="%(app_label)s_%(class)s_unique"),
        ]

    def __str__(self):
        s = "TS: period {0:s}".format(self.reporting_period.project.name)
        if self.reporting_period.wp:
            s += " ({0:s})".format(self.reporting_period.wp.name)
        s += "Day: {0!s}, Hours {1:.1f}".format(self.day, self.hours)
        return s
