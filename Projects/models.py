from django.db import models
from django.contrib.auth.models import User


class Researcher(models.Model):
    """ Researchers' registry
    """
    # Name
    name = models.CharField(max_length=200)
    # Surname
    surname = models.CharField(max_length=200)
    # User name
    username = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True)

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
    RESEARCHER_TD = "TD"
    RESEARCHER = "RI"
    SENIOR = "PR"
    DIRECTOR = "DR"
    INSTITUTE_DIRECTOR = "ID"
    FULL_PROFESSOR = "FP"
    ASSOCIATE_PROFESSOR = "AP"
    role = models.CharField(
        max_length=2,
        choices=[
            (RESEARCHER_TD, "Researcher (TD)"),
            (RESEARCHER, "Researcher"),
            (SENIOR, "Senior Researcher"),
            (DIRECTOR, "Research Director"),
            (INSTITUTE_DIRECTOR, "Institute Director"),
            (FULL_PROFESSOR, "Full Professor"),
            (ASSOCIATE_PROFESSOR, "Associate Professor"),
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
    name = models.CharField(max_length=100, db_index=True)
    agency = models.CharField(max_length=200)
    reference = models.CharField(max_length=200)
    pi = models.ForeignKey(Researcher, on_delete=models.PROTECT, null=True, blank=True)
    sigla_id = models.IntegerField(null=True, blank=True)
    sigla_name = models.CharField(max_length=32, null=True, blank=True)
    sigla_cup = models.CharField(max_length=64, null=True, blank=True)

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
    name = models.CharField(max_length=100, db_index=True)
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
