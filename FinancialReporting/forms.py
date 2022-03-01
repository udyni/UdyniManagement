from django import forms
from django.db.models import Q
from .models import Researcher, ResearcherRole, Project, WorkPackage, PersonnelCost, Reporting
from django.core.exceptions import ValidationError
import pandas as pd
import re


class ResearcherRoleForm(forms.ModelForm):
    # Explicitly specify start_date to set date format
    start_date = forms.DateField(input_formats=['%d/%m/%Y', '%d-%m-%Y'], widget=forms.DateInput())

    class Meta:
        model = ResearcherRole
        fields = ['researcher', 'role', 'start_date']
        widgets = {
            'researcher': forms.HiddenInput,
        }


class PresenceInputForm(forms.Form):

    researcher = forms.ModelChoiceField(queryset=Researcher.objects.all())
    file = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data['file']
        try:
            name = "{0:s} {1:s}".format(self.cleaned_data['researcher'].surname, self.cleaned_data['researcher'].name)
            xls = pd.ExcelFile(file)
            good_sheets = 0
            # Check if is an old format file
            if 'Riassunto RF' in xls.sheet_names:
                # TODO: any check for old files?
                pass
            else:
                # Check that the file matches the selected researcher
                for n in xls.sheet_names:
                    m = re.match(r"([a-zA-Z ]+)_([a-z]+)(\d+)", n)
                    if m is not None:
                        if m.groups()[0] == name:
                            good_sheets += 1
                if good_sheets == 0:
                    raise ValidationError("Excel file does not contain data for the selected researcher")

        except ValueError:
            raise ValidationError("File is not a valid Excel file")


class EpasCodeUpdateForm(forms.Form):

    file = forms.FileField()

    def clean_file(self):
        # File should contain only an HTML table with EPAS codes
        file = self.cleaned_data['file']
        try:
            from lxml import etree
            etree.HTML(file.read()).find("body/table/tbody")
            file.seek(0)
        except Exception as e:
            print(e)
            raise ValidationError("File is not a valid table of EPAS codes")


class ReportingAddForm(forms.Form):

    researcher = forms.ModelChoiceField(label="Researcher", queryset=Researcher.objects.all())
    project = forms.ModelChoiceField(label="Project", queryset=Project.objects.all())
    cost = forms.ModelChoiceField(label="Cost", queryset=PersonnelCost.objects.none())

    # Reporting period dates
    rp_start = forms.DateField(input_formats=['%d/%m/%Y', '%d-%m-%Y'], widget=forms.DateInput())
    rp_end = forms.DateField(input_formats=['%d/%m/%Y', '%d-%m-%Y'], widget=forms.DateInput())

    # WP and hours information
    wp_1 = forms.ModelChoiceField(label="WP", queryset=WorkPackage.objects.none(), required=False)
    wp_1.number = 1
    hours_input_1 = forms.CharField(label="Hours", widget=forms.NumberInput(attrs={'min': '0', 'step': '0.1'}), required=False)
    hours_input_1.number = 1

    def __init__(self, *args, **kwargs):

        # Parent INIT
        super().__init__(*args, **kwargs)

        # Add missing fields
        if self.is_bound:
            qs = WorkPackage.objects.none()
            if 'project' in self.data:
                try:
                    prj = int(self.data['project'])
                    qs = WorkPackage.objects.filter(project=prj)
                except ValueError:
                    pass

            if 'researcher' in self.data:
                try:
                    res = int(self.data['researcher'])
                    self.fields['cost'].queryset = PersonnelCost.objects.filter(researcher=res)
                except ValueError:
                    pass

            for k, v in self.data.items():
                m = re.match(r"wp_(\d+)", k)
                if m is not None:
                    number = int(m.groups()[0])
                    name = "wp_{0:d}".format(number)
                    if name not in self.fields:
                        wp = forms.ModelChoiceField(label="WP", queryset=qs, required=False)
                        wp.number = number
                        h = forms.CharField(label="Hours", widget=forms.NumberInput(attrs={'min': '0', 'step': '0.1'}), required=False)
                        h.number = number
                        self.fields[name] = wp
                        self.fields["hours_input_{0:d}".format(number)] = h
                    else:
                        self.fields[name].queryset = qs

        # Set number on all fields
        for k, v in self.fields.items():
            if not hasattr(v, 'number'):
                setattr(v, 'number', 0)

    # Custom visible_fields method that propagate number attribute
    def visible_fields(self):
        fields = super().visible_fields()
        for f in fields:
            if hasattr(f.field, 'number'):
                setattr(f, 'number', f.field.number)
        return fields

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        # Check that period does not overlap for any WP with other records
        good_wps = {}
        wp_to_discard = []
        qf = Q()
        for k, v in cleaned_data.items():
            if v is None:
                # Empty WP, ignore
                wp_to_discard.append(k)
                continue

            # Match key
            m = re.match(r"wp_(\d+)", k)
            if m is not None:
                # WP id
                n = int(m.groups()[0])

                # WP field
                hours = "hours_input_{0:d}".format(n)
                if hours not in cleaned_data:
                    # Empty data
                    wp_to_discard.append(k)
                    continue
                try:
                    h = float(cleaned_data[hours])
                    if h <= 0.0:
                        # Zero or negative hours, ignore
                        wp_to_discard.append(k)
                        continue
                except ValueError as e:
                    # Invalid number of hours
                    errors[hours] = ValidationError("Invalid number of hours (Error: {0!s})".format(e), code="invalid")
                    wp_to_discard.append(k)
                    continue

                # The WP is well defined. Let's check that is not duplicated
                if v.pk not in good_wps:
                    qf |= Q(wp=v.pk)
                    good_wps[v.pk] = k
                else:
                    errors[k] = ValidationError("Cannot specify the same WP more than once", code="invalid")

        # Add project specifier
        qf &= Q(project=cleaned_data["project"].pk, researcher=cleaned_data["researcher"].pk)

        if not len(good_wps):
            # No WP selected with a non-zero number of hours
            # Check WP1 for a number of hours (hours for the full project)
            try:
                if "hours_input_1" not in self.cleaned_data:
                    raise ValueError("not specified")
                h = float(self.cleaned_data['hours_input_1'])
                if h <= 0:
                    raise ValueError("must be greater than zero")
            except ValueError as e:
                errors['hours_input_1'] = ValidationError("Invalid number of hours (Error: {0!s})".format(e), code="invalid")

        # Filter objects
        objs = Reporting.objects.filter(qf)
        start = cleaned_data["rp_start"]
        end = cleaned_data["rp_end"]

        for period in objs:
            if start >= period.rp_start and start <= period.rp_end:
                if period.wp is not None:
                    errors[good_wps[period.wp.pk]] = ValidationError("The start date of the reporting period overlaps with another period for the same WP")
                else:
                    errors['rp_start'] = ValidationError("The start date of the reporting period overlaps with another period for the same project")
            if end >= period.rp_start and end <= period.rp_end:
                if period.wp is not None:
                    errors[good_wps[period.wp.pk]] = ValidationError("The end date of the reporting period overlaps with another period for the same WP")
                else:
                    errors['rp_end'] = ValidationError("The end date of the reporting period overlaps with another period for the same project")

        if len(errors):
            raise ValidationError(errors)

        # Cleanup data
        for wp in wp_to_discard:
            del cleaned_data[wp]

        return cleaned_data
