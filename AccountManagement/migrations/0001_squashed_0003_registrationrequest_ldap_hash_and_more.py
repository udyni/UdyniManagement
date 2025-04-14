# Generated by Django 4.2.20 on 2025-04-14 13:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('AccountManagement', '0001_initial'), ('AccountManagement', '0002_registrationrequest_submit_timestamp'), ('AccountManagement', '0003_registrationrequest_ldap_hash_and_more')]

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('surname', models.CharField(max_length=64)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('uuid', models.CharField(max_length=32, unique=True)),
                ('status', models.CharField(choices=[('S', 'Submitted'), ('V', 'Verified'), ('A', 'Accepted'), ('R', 'Rejected')], max_length=1)),
            ],
            options={
                'ordering': ['surname', 'name'],
                'permissions': [('registration_manage', 'Manage registration requests')],
                'default_permissions': (),
            },
        ),
        migrations.AddConstraint(
            model_name='registrationrequest',
            constraint=models.UniqueConstraint(fields=('name', 'surname'), name='accountmanagement_registrationrequest_unique'),
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='submit_timestamp',
            field=models.DateTimeField(auto_now_add=True, default=datetime.datetime(2022, 5, 1, 1, 0)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='ldap_hash',
            field=models.CharField(default='', max_length=38),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='registrationrequest',
            name='samba_hash',
            field=models.CharField(default='', max_length=32),
            preserve_default=False,
        ),
    ]
