# Generated by Django 3.2.5 on 2022-04-13 07:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Projects', '0004_auto_20220413_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='researcher',
            name='username',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
