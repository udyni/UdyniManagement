# Generated by Django 3.2.9 on 2022-04-06 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('FinancialReporting', '0004_auto_20220406_1615'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='personnelcost',
            options={'ordering': ['year', 'researcher']},
        ),
        migrations.AlterModelOptions(
            name='presencedata',
            options={'ordering': ['researcher', 'day']},
        ),
        migrations.RemoveConstraint(
            model_name='reporting',
            name='financialreporting_reporting_unique',
        ),
        migrations.RenameField(
            model_name='personnelcost',
            old_name='n_researcher',
            new_name='researcher',
        ),
        migrations.RenameField(
            model_name='presencedata',
            old_name='n_researcher',
            new_name='researcher',
        ),
        migrations.RenameField(
            model_name='reporting',
            old_name='n_project',
            new_name='project',
        ),
        migrations.RenameField(
            model_name='reporting',
            old_name='n_researcher',
            new_name='researcher',
        ),
        migrations.RenameField(
            model_name='reporting',
            old_name='n_wp',
            new_name='wp',
        ),
        migrations.AddConstraint(
            model_name='reporting',
            constraint=models.UniqueConstraint(fields=('researcher', 'project', 'wp', 'rp_start', 'rp_end'), name='financialreporting_reporting_unique'),
        ),
    ]
