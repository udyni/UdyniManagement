from django.db import models
from django.contrib.auth import get_user_model
from Projects.models import Project

UserModel = get_user_model()

class Laboratory(models.Model):
    laboratory_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)


class ExperimentalStation(models.Model):
    POSSIBLE_STATUSES = [
        ("AVAILABLE", "Available"),
        ("TEMP_UNAVAILABLE", "Temporary Unavailable"),
        ("DISMISSED", "Dismissed"),
    ]

    station_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    responsible = models.ForeignKey(UserModel, on_delete=models.PROTECT, null=True, blank=True)
    description = models.TextField()
    laboratory = models.ForeignKey(Laboratory, on_delete=models.CASCADE)
    status = models.CharField(max_length=17, choices=POSSIBLE_STATUSES)


class Sample(models.Model):
    sample_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    author = models.ForeignKey(UserModel, on_delete=models.PROTECT, null=True, blank=True)
    manifacturer = models.CharField(max_length=255)
    reference = models.CharField(max_length=255)
    material = models.CharField(max_length=255)
    substrate = models.CharField(max_length=255)
    description = models.TextField()


class Experiment(models.Model):
    POSSIBLE_STATUSES = [
        ("NEW", "New"),
        ("SCHEDULED", "Scheduled"),
        ("RUNNING", "Running"),
        ("CLOSED", "Closed"),
        ("CANCELLED", "Cancelled"),
    ]

    experiment_id = models.AutoField(primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.PROTECT, null=True, blank=True)
    reference = models.CharField(max_length=255)
    creation_time = models.DateTimeField(auto_now_add=True)
    responsible = models.ForeignKey(UserModel, on_delete=models.PROTECT, null=True, blank=True)
    experimental_station = models.ForeignKey(ExperimentalStation, on_delete=models.PROTECT)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=POSSIBLE_STATUSES)


class SampleForExperiment(models.Model):
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT)

    class Meta:
        unique_together = ("experiment", "sample")


class Measurement(models.Model):
    measurement_id = models.AutoField(primary_key=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.PROTECT)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    sample = models.ForeignKey(Sample, on_delete=models.PROTECT)


class File(models.Model):
    file_id = models.AutoField(primary_key=True)
    measurement = models.ForeignKey(Measurement, on_delete=models.PROTECT)
    path = models.CharField(max_length=255)


class Comment(models.Model):
    COMMENT_TYPES = [
        ("ACQUISITION", "Acquisition"),
        ("ANALYSIS", "Analysis"),
    ]

    comment_id = models.AutoField(primary_key=True)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE)
    measurement = models.ForeignKey(Measurement, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=12, choices=COMMENT_TYPES)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies")


class CommentContent(models.Model):
    comment_content_id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    version = models.IntegerField()
    author = models.ForeignKey(UserModel, on_delete=models.PROTECT, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    text = models.TextField(null=True)


# For future versions of the application
class Attachment(models.Model):
    attachment_id = models.AutoField(primary_key=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    author = models.ForeignKey(UserModel, on_delete=models.PROTECT, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    mimetype = models.CharField(max_length=255)
    path = models.CharField(max_length=255)