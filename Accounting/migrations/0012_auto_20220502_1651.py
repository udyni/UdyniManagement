# Generated by Django 3.2.5 on 2022-05-02 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Accounting', '0011_auto_20220502_1247'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='variazione',
            name='accounting_variazione_unique',
        ),
        migrations.AddConstraint(
            model_name='variazione',
            constraint=models.UniqueConstraint(fields=('gae', 'data', 'numero', 'voce'), name='accounting_variazione_unique'),
        ),
    ]
