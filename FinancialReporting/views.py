from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.http import JsonResponse, Http404, FileResponse

from django.db.models import Count, Sum, Q, F, Value
from django.db.models.functions import ExtractYear, ExtractMonth, Concat
from Projects.models import Researcher, ResearcherRole, WorkPackage
from .models import BankHoliday, PersonnelCost, PresenceData, Reporting, EpasCode, TimesheetHint, TimesheetMissionHint, TimesheetHours

from .forms import PresenceInputForm, EpasCodeUpdateForm, ReportingAddForm

from .utils import process_presences, summarize_presences, serialize_presences
from .utils import unserialize_presences, check_presences_unique, check_bank_holiday
from .utils import GenerateTimesheetData, LoadTimesheetData, CheckTimesheetData
from .print import PrintPFDTimesheet

from Tags.templatetags import tr_month

from django.views import View
from UdyniManagement.menu import UdyniMenu
from UdyniManagement.views import ListViewMenu, CreateViewMenu, UpdateViewMenu, DeleteViewMenu


from django.contrib.auth.mixins import PermissionRequiredMixin

import re
import pandas as pd
from lxml import etree
import datetime
import math
import calendar
import json
import random


# =============================================
# PERSONNEL COSTS
#
class PersonnelCostList(PermissionRequiredMixin, ListViewMenu):
    model = PersonnelCost
    permission_required = 'reporting.read'

    def get_queryset(self):
        return PersonnelCost.objects.all().order_by('researcher', 'year')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Personnel cost"
        return context


class PersonnelCostCreate(PermissionRequiredMixin, CreateViewMenu):
    model = PersonnelCost
    fields = ['researcher', 'year', 'working_hours', 'cost']
    success_url = reverse_lazy('cost_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new personnel cost"
        context['back_url'] = reverse_lazy('cost_view')
        return context


class PersonnelCostUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = PersonnelCost
    fields = ['year', 'working_hours', 'cost']
    success_url = reverse_lazy('cost_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify personnel cost of " + str(context['personnelcost'].researcher)
        context['back_url'] = reverse_lazy('cost_view')
        return context


class PersonnelCostDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = PersonnelCost
    success_url = reverse_lazy('cost_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete personnel cost"
        context['message'] = "Are you sure you want to delete the personnel cost for {0!s} for year {1!s}?".format(context["personnelcost"].researcher, context["personnelcost"].year)
        context['back_url'] = reverse_lazy('cost_view')
        return context


# =============================================
# PRESENCES
#

class PresenceDataList(PermissionRequiredMixin, ListViewMenu):
    model = PresenceData
    permission_required = 'reporting.read'

    def get_queryset(self):
        if 'researcher' in self.kwargs:
            return PresenceData.objects.filter(researcher=self.kwargs['researcher'])
        else:
            qs = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'))  # , ts_code=F("code__ts_code"))
                .values('researcher', 'year')
                .annotate(
                    tot_hours=Sum('hours', filter=Q(code__ts_code=EpasCode.NONE) | Q(code__isnull=True) | Q(code__ts_code=EpasCode.MISSION)),
                    tot_hours_nom=Sum('hours', filter=Q(code__ts_code=EpasCode.NONE) | Q(code__isnull=True)),
                    working_days=Count('hours', filter=Q(code__ts_code=EpasCode.NONE) | ~Q(hours=0)),
                    tot_ts_hours=Sum('ts_hours', filter=Q(ts_code=EpasCode.NONE) | Q(ts_code=EpasCode.MISSION)),
                    holidays=Count('code', filter=Q(code__ts_code=EpasCode.HOLIDAYS)),
                    illness_leave=Count('code', filter=Q(code__ts_code=EpasCode.ILLNESS)),
                    missions=Count('code', filter=Q(code__ts_code=EpasCode.MISSION)),
                )
                .order_by('year')
            )
            return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Presences summary"
        # Extract researchers' IDs
        researchers_pks = []
        for q in context['object_list']:
            if q['researcher'] not in researchers_pks:
                researchers_pks.append(q['researcher'])
        context['researchers'] = Researcher.objects.filter(pk__in=researchers_pks).order_by()
        return context


class PresenceDataDetail(PermissionRequiredMixin, ListViewMenu):
    model = PresenceData
    context_object_name = 'presences'
    permission_required = 'reporting.read'

    def get_template_names(self):
        if 'month' in self.kwargs:
            return ["FinancialReporting/presencedata_detailmonth.html", ]
        else:
            return ["FinancialReporting/presencedata_detail.html", ]

    def get_queryset(self):
        if 'month' in self.kwargs:
            qs = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
                .filter(
                    researcher=self.kwargs['researcher'],
                    year=self.kwargs['year'],
                    month=self.kwargs['month'],
                )
                .annotate(code_name=F('code__code'))
                .order_by('day')
            )
            cs = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
                .filter(
                    researcher=self.kwargs['researcher'],
                    year=self.kwargs['year'],
                    month=self.kwargs['month'],
                    code__isnull=False,
                )
                .values('code')
                .annotate(
                    code_name=F('code__code'),
                    code_desc=F('code__description'),
                    code_ts=F('code__ts_code'),
                    tot_code=Count('code'),
                )
                .order_by()
            )

        else:
            qs = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'))
                .filter(researcher=self.kwargs['researcher'], year=self.kwargs['year'])
                .annotate(month=ExtractMonth('day'))  # , ts_code=F("code__ts_code"))
                .values('month')
                .annotate(
                    tot_hours=Sum('hours', filter=Q(code__ts_code=EpasCode.NONE) | Q(code__isnull=True) | Q(code__ts_code=EpasCode.MISSION)),
                    tot_hours_nom=Sum('hours', filter=Q(code__ts_code=EpasCode.NONE) | Q(code__isnull=True)),
                    working_days=Count('hours', filter=Q(code__ts_code=EpasCode.NONE) | ~Q(hours=0)),
                    tot_ts_hours=Sum('ts_hours', filter=Q(ts_code=EpasCode.NONE) | Q(ts_code=EpasCode.MISSION)),
                    holidays=Count('code', filter=Q(code__ts_code=EpasCode.HOLIDAYS)),
                    illness_leave=Count('code', filter=Q(code__ts_code=EpasCode.ILLNESS)),
                    missions=Count('code', filter=Q(code__ts_code=EpasCode.MISSION)),
                )
                .order_by('month')
            )
            cs = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'))
                .filter(researcher=self.kwargs['researcher'], year=self.kwargs['year'], code__isnull=False)
                .values('code')
                .annotate(
                    code_name=F('code__code'),
                    code_desc=F('code__description'),
                    code_ts=F('code__ts_code'),
                    tot_code=Count('code'),
                )
                .order_by()
            )

        return {'pres_stat': qs, 'code_stat': cs}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        r = Researcher.objects.get(pk=self.kwargs['researcher'])
        if 'month' in self.kwargs:
            context['title'] = "Presences for {0!s} - {1:s} {2:d}".format(r, tr_month.month_num2en(self.kwargs['month']), self.kwargs['year'])
            context['choices'] = EpasCode.CHOICES
        else:
            context['title'] = "Presences summary for {0!s} - {1:d}".format(r, self.kwargs['year'])
        return context


class PresenceDataImport(PermissionRequiredMixin, View):

    http_method_names = ['get', 'post']
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):
        # Clear session
        try:
            del request.session['presences']
        except KeyError:
            pass
        context = {
            'title': "Import presence data",
            'form': PresenceInputForm(),
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/presencedata_form.html', context)

    def post(self, request, *args, **kwargs):
        form = PresenceInputForm(request.POST, request.FILES)
        if form.is_valid():
            # Load excel file
            xls = pd.ExcelFile(request.FILES['file'])
            # Process excel file
            presences = process_presences(xls, "{0:s} {1:s}".format(form.cleaned_data['researcher'].surname,
                                                                    form.cleaned_data['researcher'].name))
            request.session['presences'] = serialize_presences(presences)
            context = {
                'title': 'Confirm presence data for ' + str(form.cleaned_data['researcher']),
                'summary': summarize_presences(presences),
                'researcher': form.cleaned_data['researcher'],
                'menu': UdyniMenu().getMenu(request.user),
            }
            return render(request, 'FinancialReporting/presencedata_summary.html', context)

        context = {
            'title': "Import presence data",
            'form': form,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/presencedata_form.html', context)


class PresenceDataStore(PermissionRequiredMixin, View):

    http_method_names = ['post', ]
    permission_required = 'reporting.modify'

    def post(self, request, *args, **kwargs):
        if 'presences' in request.session:
            # Unserialize presences
            presences = unserialize_presences(request.session['presences'])
            researcher = get_object_or_404(Researcher, pk=request.POST['researcher'])

            check_presences_unique(presences)

            # data = []
            for year, v1 in presences.items():
                for month, v2 in v1.items():
                    # Check post data
                    checkbox = "i_{0:d}_{1:s}".format(year, month)
                    if checkbox in request.POST and request.POST[checkbox] == 'on':
                        # Insert data in DB
                        for i, row in v2.iterrows():
                            # Convert code
                            if row['Code'] != "":
                                try:
                                    code = EpasCode.objects.get(code=row['Code'])
                                except EpasCode.DoesNotExist:
                                    print("Missing code:", year, month, row['Date'], row['Code'])
                                    code = None
                            else:
                                code = None

                            # Check if data is already in DB
                            try:
                                obj = PresenceData.objects.get(researcher=researcher, day=row['Date'])
                                update = False
                                if obj.hours != row['Hours']:
                                    obj.hours = row['Hours']
                                    update = True
                                if obj.code != code:
                                    obj.code = code
                                    update = True
                                if update:
                                    obj.save()

                            except PresenceData.MultipleObjectsReturned:
                                print("ERROR: more that one result! This should never happen!")

                            except PresenceData.DoesNotExist:
                                p = PresenceData(researcher=researcher,
                                                 day=row['Date'],
                                                 hours=row['Hours'],
                                                 ts_hours=0.0,
                                                 code=code)
                                p.save()
                                # data.append(p) NOTE: disabled bulk create as it was impossibile to debug an integrity violation

                # if len(data):
                    # PresenceData.objects.bulk_create(data)

        return redirect('presencedata_view')


class PresenceDataUpdate(PermissionRequiredMixin, View):

    http_method_names = ['post', ]
    permission_required = 'reporting.modify'

    def post(self, request, *args, **kwargs):
        # Extract data from POST
        researcher = get_object_or_404(Researcher, pk=request.POST['researcher'])
        year = int(request.POST['year'])
        month = int(request.POST['month'])

        days = calendar.monthrange(year, month)[1]

        for i in range(days):
            h = "ts_day_{0:02d}".format(i + 1)
            c = "ts_code_{0:02d}".format(i + 1)

            if h in request.POST or c in request.POST:
                try:
                    obj = PresenceData.objects.get(
                        researcher=researcher,
                        day=datetime.datetime(year=year, month=month, day=i + 1),
                    )
                    modified = False
                    try:
                        if h in request.POST:
                            hours = float(request.POST[h])
                            if obj.ts_hours != hours:
                                obj.ts_hours = hours
                                modified = True
                        if c in request.POST:
                            code = request.POST[c]
                            if code != obj.ts_code:
                                obj.ts_code = code
                                modified = True
                    except Exception:
                        pass

                    if modified:
                        obj.save()

                except PresenceData.DoesNotExist:
                    pass
                except PresenceData.MultipleObjectsReturned:
                    pass

        return redirect('presencedata_detailmonth', researcher=researcher.pk, year=year, month=month)


class PresenceDataExportTS(PermissionRequiredMixin, View):

    http_method_names = ['get', 'post']
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):
        # First step -> Check which missions in the year should be reported
        # We need to retrieve:
        #  - All days marked as missions for each month
        #  - Total working hours by month
        #  - Working hours for the year

        rid = self.kwargs['researcher']
        year = self.kwargs['year']

        # Missions by month
        missions = {}
        for month in range(1, 13, 1):
            missions[month] = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
                .filter(researcher=rid, year=year, month=month, code__ts_code=EpasCode.MISSION)
                .order_by()
            )

        # Total hours by month and by year
        qs = (
            PresenceData.objects
            .annotate(year=ExtractYear('day'))
            .filter(researcher=rid, year=year)
            .annotate(month=ExtractMonth('day'))
            .values('month')
            .annotate(
                tot_hours=Sum('hours', filter=Q(code__ts_code=EpasCode.NONE) | Q(code__isnull=True)),
                working_days=Count('hours', filter=(Q(code__ts_code=EpasCode.NONE) | Q(code__isnull=True)) & ~Q(hours=0)),
            )
            .order_by()
        )

        # Totals by year
        total_hours = 0.0
        total_days = 0
        for q in qs:
            if q['tot_hours'] is not None:
                total_hours += q['tot_hours']
            total_days += q['working_days']

        print("Total days:", total_days)
        print("Total hours:", total_hours)

        # Nominal working hours for the year
        try:
            pcost = PersonnelCost.objects.get(researcher=rid, year=year)
            working_hours = pcost.working_hours
        except PersonnelCost.DoesNotExist:
            working_hours = 1506

        # Data by month
        data_by_month = {}
        for m, data in missions.items():
            data_by_month[m] = {}
            data_by_month[m]['missions'] = data
            for q in qs:
                if q['month'] == m:
                    if q['tot_hours'] is not None:
                        data_by_month[m]['tot_hours'] = q['tot_hours']
                    else:
                        data_by_month[m]['tot_hours'] = 0.0
                    data_by_month[m]['working_hours'] = working_hours / total_days * q['working_days']
                    if data_by_month[m]['working_hours'] > data_by_month[m]['tot_hours']:
                        data_by_month[m]['missions2report'] = math.ceil((data_by_month[m]['working_hours'] - data_by_month[m]['tot_hours']) / 7.2)
                    else:
                        data_by_month[m]['missions2report'] = 0

        # Missinig working hours (excluding missions)
        missing_hours = working_hours - total_hours
        if missing_hours < 0:
            missing_hours = 0.0

        r = Researcher.objects.get(pk=rid)
        context = {
            'title': "Missions summary for {0!s} - Year: {1:d}".format(r, year),
            'total_hours': total_hours,
            'working_hours': working_hours,
            'missing_hours': missing_hours,
            'missions2report': math.ceil(missing_hours / 7.2),
            'data_by_month': data_by_month,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/presencedata_export2ts_missions.html', context)

    def post(self, request, *args, **kwargs):
        rid = self.kwargs['researcher']
        year = self.kwargs['year']

        # Find selected checkboxes
        checked_missions = []
        for k, v in request.POST.items():
            m = re.match(r"rep_(\d+)_(\d+)", k)
            if m is not None and v == 'on':
                checked_missions.append(datetime.date(year, int(m.groups()[0]), int(m.groups()[1])))

        # Get all presences and check
        qs = (
            PresenceData.objects
            .annotate(year=ExtractYear('day'), code_ts=F("code__ts_code"))
            .filter(researcher=rid, year=year)
            .order_by()
        )

        # Nominal working hours for the year
        try:
            pcost = PersonnelCost.objects.get(researcher=rid, year=year)
            working_hours = pcost.working_hours
        except PersonnelCost.DoesNotExist:
            working_hours = 1506

        # NONE = ""
        # HOLIDAYS = "HO"
        # MISSION = "MI"
        # ILLNESS = "IL"
        # OTHER = "OA"

        total_hours = 0.0
        # Cycle over presences
        for q in qs:
            # First check code
            if q.code_ts == EpasCode.MISSION:
                if q.day in checked_missions:
                    # Set mission code only to selected missions
                    q.ts_code = EpasCode.MISSION
                else:
                    # Set other absences to other missions
                    q.ts_code = EpasCode.OTHER
            elif q.code_ts is None:
                q.ts_code = EpasCode.NONE
            else:
                q.ts_code = q.code_ts

            # Check if day is weekend or bank holiday
            if q.day.isoweekday() < 6 and not check_bank_holiday(q.day):
                if q.ts_code == EpasCode.MISSION:
                    q.ts_hours = 7
                    total_hours += 7
                elif q.ts_code == EpasCode.NONE:
                    q.ts_hours = round(q.hours * 2) / 2   # Round to the nearest 1/2 hour
                    total_hours += q.ts_hours
                else:
                    q.ts_hours = 0
            else:
                # Set zero hours on weekend even if is a mission
                q.ts_hours = 0

            # Save object
            q.save()

        if working_hours != total_hours:
            qs = (
                PresenceData.objects
                .annotate(year=ExtractYear('day'))
                .filter(Q(researcher=rid) & Q(year=year) & Q(ts_hours__gt=0) & Q(ts_code=EpasCode.NONE))
                .order_by()
            )

            indexes = list(range(qs.count()))
            rand_ind = random.sample(indexes, len(indexes))

            if total_hours < working_hours:
                # We have to add some hours here and there
                while total_hours < working_hours:
                    try:
                        i = rand_ind.pop()
                        q = qs[i]
                        q.ts_hours += 0.5
                        total_hours += 0.5
                        q.save()
                    except IndexError:
                        rand_ind = random.sample(indexes, len(indexes))
            else:
                # We need to remove hours
                while total_hours > working_hours:
                    try:
                        i = rand_ind.pop()
                        q = qs[i]
                        q.ts_hours -= 0.5
                        total_hours -= 0.5
                        q.save()
                    except IndexError:
                        rand_ind = random.sample(indexes, len(indexes))

        return redirect('presencedata_view')


# =============================================
# EPAS CODES
#

class EpasCodeList(PermissionRequiredMixin, ListViewMenu):
    model = EpasCode
    paginate_by = 20
    permission_required = 'reporting.read'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "EPAS codes"
        context['choices'] = EpasCode.CHOICES
        print(context['page_obj'])
        return context


class EpasCodeImport(PermissionRequiredMixin, View):

    http_method_names = ['get', 'post']
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):
        context = {
            'title': 'Import EPAS codes',
            'form': EpasCodeUpdateForm(),
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/epascode_form.html', context)

    def post(self, request, *args, **kwargs):
        form = EpasCodeUpdateForm(request.POST, request.FILES)
        if form.is_valid():
            # Parse file
            codes = {}
            try:
                f = request.FILES['file']
                parser = etree.HTMLParser(encoding="utf-8")
                tbody = etree.HTML(f.read(), parser=parser).find("body/table/tbody")
                for row in iter(tbody):
                    # Get cells
                    cols = row.getchildren()
                    # Check if the code is active
                    code = cols[0].find("a").text.strip()
                    desc = cols[2].text
                    if desc is not None:
                        desc = desc.strip()
                        codes[code] = desc
            except Exception as e:
                context = {
                    'title': 'Import EPAS codes',
                    'form': form,
                    'error': str(e),
                    'menu': UdyniMenu().getMenu(request.user),
                }
                return render(request, 'FinancialReporting/epascode_form.html', context)

            for k, v in codes.items():
                try:
                    obj = EpasCode.objects.get(code=k)
                    if obj.description != v:
                        obj.description = v
                        obj.save()
                except EpasCode.DoesNotExist:
                    new_code = EpasCode(code=k, ts_code="", description=v)
                    new_code.save()
            return redirect('epas_view')

        else:
            context = {
                'title': 'Import EPAS codes',
                'form': form,
                'menu': UdyniMenu().getMenu(request.user),
            }
            return render(request, 'FinancialReporting/epascode_form.html', context)


class EpasCodeUpdate(PermissionRequiredMixin, View):

    http_method_names = ['post', ]
    permission_required = 'reporting.modify'

    def post(self, request, *args, **kwargs):
        for k, v in request.POST.items():
            m = re.match(r"ts_(\d+)", k)
            if m is not None:
                pk = int(m.groups()[0])
                try:
                    obj = EpasCode.objects.get(pk=pk)
                    obj.ts_code = v
                    obj.save()
                except EpasCode.DoesNotExist:
                    pass

        return JsonResponse({'success': True})


# =============================================
# BANK HOLYDAYS
#

class BankHolidayList(PermissionRequiredMixin, ListViewMenu):
    model = BankHoliday
    permission_required = 'reporting.read'

    def ordinaltg(self, n):
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(4 if 10 <= n % 100 < 20 else n % 10, "th")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Bank Holidays"
        for bh in context['object_list']:
            if bh.year == 0:
                bh.date = "{0:s} {1:d}{2:s}".format(calendar.month_name[bh.month], bh.day, self.ordinaltg(bh.day))
            else:
                bh.date = "{0:s} {1:d}{2:s}, {3:d}".format(calendar.month_name[bh.month], bh.day, self.ordinaltg(bh.day), bh.year)
        return context


class BankHolidayCreate(PermissionRequiredMixin, CreateViewMenu):
    model = BankHoliday
    fields = ['name', 'year', 'month', 'day']
    success_url = reverse_lazy('bankholiday_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Add new bank holiday"
        context['back_url'] = reverse_lazy('bankholiday_view')
        return context


class BankHolidayUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = BankHoliday
    fields = ['name', 'year', 'month', 'day']
    success_url = reverse_lazy('bankholiday_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Modify bank holiday"
        context['back_url'] = reverse_lazy('bankholiday_view')
        return context


class BankHolidayDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = BankHoliday
    success_url = reverse_lazy('bankholiday_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete bank holiday"
        context['message'] = "Are you sure you want to delete the bank holiday: {0!s}?".format(context['bankholiday'])
        context['back_url'] = reverse_lazy('bankholiday_view')
        return context


# =============================================
# REPORTING
#

class ReportingList(PermissionRequiredMixin, ListViewMenu):
    model = Reporting
    permission_required = 'reporting.read'

    def get_queryset(self):
        qs = (
            Reporting.objects.all()
            .annotate(
                res_name=Concat(F('researcher__name'), Value(' '), F('researcher__surname')),
                res_cost=F('hours') * F('cost__cost') / F('cost__working_hours'),
            )
            .order_by('researcher', 'project', 'rp_start', 'wp')
        )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Reporting"

        periods = {}

        for obj in context['object_list']:
            # Researcher name
            name = str(obj.res_name)
            if name not in periods:
                periods[name] ={}
            # Project name
            project = str(obj.project.name)
            if project not in periods[name]:
                periods[name][project] = {'rowspan': 0, 'periods': {}}
            # Reporting period
            start = obj.rp_start.isoformat()
            if start not in periods[name][project]['periods']:
                periods[name][project]['periods'][start] = {'rowspan': 0, 'start': obj.rp_start, 'end': obj.rp_end}
            # Workpackages
            if obj.wp is not None:
                if 'wps' not in periods[name][project]['periods'][start]:
                    periods[name][project]['periods'][start]['wps'] = {}
                periods[name][project]['periods'][start]['wps'][obj.wp.name] = {'pk': obj.pk, 'hours': obj.hours, 'cost': obj.res_cost}
            else:
                periods[name][project]['periods'][start].update({'pk': obj.pk, 'hours': obj.hours, 'cost': obj.res_cost})

            periods[name][project]['rowspan'] += 1
            periods[name][project]['periods'][start]['rowspan'] += 1

        context['periods'] = periods

        return context


class ReportingCreate(PermissionRequiredMixin, View):

    http_method_names = ['get', 'post']
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):
        context = {
            'title': "Add new reporting period",
            'form': ReportingAddForm(),
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/reporting_add.html', context)

    def post(self, request, *args, **kwargs):
        form = ReportingAddForm(request.POST)

        if form.is_valid():
            researcher = form.cleaned_data['researcher']
            project = form.cleaned_data['project']
            cost = form.cleaned_data['cost']
            start = form.cleaned_data['rp_start']
            end = form.cleaned_data['rp_end']

            # Cycle over WPs
            inserted_any = False
            for k, v in form.cleaned_data.items():
                m = re.match(r"wp_(\d+)", k)
                if m is not None:
                    n = int(m.groups()[0])
                    h = float(form.cleaned_data["hours_input_{0:d}".format(n)])
                    hm = bool(form.cleaned_data["has_missions_{0:d}".format(n)])
                    # We have a wp
                    obj = Reporting(
                        project=project,
                        researcher=researcher,
                        cost=cost,
                        hours=h,
                        wp=v,
                        rp_start=start,
                        rp_end=end,
                        has_missions=hm)
                    obj.save()
                    inserted_any = True

            if not inserted_any:
                # No WP specified. Get number of hours from WP1
                h = float(form.cleaned_data["hours_input_1"])
                hm = bool(form.cleaned_data["has_missions_1"])
                obj = Reporting(
                    project=project,
                    researcher=researcher,
                    cost=cost,
                    hours=h,
                    rp_start=start,
                    rp_end=end,
                    has_missions=hm)
                obj.save()

            return redirect('reporting_view')

        else:
            context = {
                'title': "Add new reporting period",
                'form': form,
                'menu': UdyniMenu().getMenu(request.user),
            }
            return render(request, 'FinancialReporting/reporting_add.html', context)


class ReportingUpdate(PermissionRequiredMixin, UpdateViewMenu):
    model = Reporting
    fields = ['hours', 'cost', 'has_missions']
    success_url = reverse_lazy('reporting_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/generic_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Editing reporting period "
        context['back_url'] = reverse_lazy('reporting_view')
        return context


class ReportingDelete(PermissionRequiredMixin, DeleteViewMenu):
    model = Reporting
    success_url = reverse_lazy('reporting_view')
    permission_required = 'reporting.modify'
    template_name = "UdyniManagement/confirm_delete.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = "Delete personnel cost"
        values = [
                context['reporting'].rp_start,
                context['reporting'].rp_end,
                context['reporting'].researcher,
                context['reporting'].project.name,
                " (WP: {0!s})".format(context['reporting'].wp.name) if context['reporting'].wp else "",
        ]
        context['message'] = "Are you sure you want to delete the reporting period from {0!s} to {1!s} for {2!s} on the project {3!s}{4!s}?".format(*values)
        context['back_url'] = reverse_lazy('reporting_view')
        print(context)
        return context


class ReportingUpdateWPs(PermissionRequiredMixin, View):

    http_method_names = ['post', ]
    permission_required = 'reporting.modify'

    def post(self, request, *args, **kwargs):

        project = request.POST['project']
        if project:
            qs = WorkPackage.objects.filter(project=project)
            wp_list = []
            for q in qs:
                wp_list.append({'pk': q.pk, 'name': str(q)})
            return JsonResponse({'wps': wp_list})
        else:
            return JsonResponse({'wps': list()})


class ReportingUpdateCosts(PermissionRequiredMixin, View):

    http_method_names = ['post', ]
    permission_required = 'reporting.modify'

    def post(self, request, *args, **kwargs):

        researcher = request.POST['researcher']
        if researcher:
            qs = PersonnelCost.objects.filter(researcher=researcher)
            cost_list = []
            for q in qs:
                cost_list.append({'pk': q.pk, 'name': str(q)})
            return JsonResponse({'costs': cost_list})
        else:
            return JsonResponse({'costs': list()})


# =============================================
# TIMESHEETS
#
class TimeSheetsView(PermissionRequiredMixin, View):
    """ List a summary of all the available timesheets / reporting periods
        and status of the generation
    """

    http_method_names = ['get', ]
    permission_required = 'reporting.read'

    def get(self, request, *args, **kwargs):

        # Get all years for which we have some reporting periods registered
        years = []
        periods = Reporting.objects.all()
        for p in periods:
            y = p.rp_start.year
            while y <= p.rp_end.year:
                if y not in years:
                    years.append(y)
                y += 1
        years.sort()

        # Get all researchers
        researchers = Researcher.objects.all()

        data = []
        for r in researchers:
            # Cycle over years
            r_data = {}
            for y in years:
                # Get reporting periods
                periods = (
                    Reporting.objects
                    .filter(
                        Q(researcher=r) &
                        Q(rp_start__lte=datetime.date(y, 12, 31)) &
                        Q(rp_end__gte=datetime.date(y, 1, 1))
                    )
                    .order_by()
                )

                # Count periods
                c = periods.count()
                if c == 0:
                    # No periods in the current year
                    continue
                r_data[y] = {}
                r_data[y]['periods'] = c

                # Get number of missions that need to be reported
                missions = (
                    PresenceData.objects
                    .filter(
                        Q(researcher=r) &
                        Q(day__gte=datetime.date(y, 1, 1)) &
                        Q(day__lte=datetime.date(y, 12, 31)) &
                        Q(ts_code=EpasCode.MISSION)
                    )
                    .aggregate(n=Count('day'))
                )
                r_data[y]['missions'] = missions['n']

                # Check hints
                r_data[y]['hints'] = 0
                for p in periods:
                    hints = (
                        TimesheetHint.objects
                        .filter(reporting_period=p, year=y)
                        .aggregate(
                            n=Count('hours'),
                        )
                    )
                    if hints['n'] != 12:
                        continue
                    r_data[y]['hints'] += 1

                # Check if timesheets are generated
                r_data[y]['ts'] = 0
                for m in range(1, 13, 1):
                    if CheckTimesheetData(r.pk, y, m):
                        r_data[y]['ts'] += 1

            if len(r_data):
                data.append({'researcher': r, 'data': r_data})

        context = {
            'title': "Generate timesheets",
            'researchers': data,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/timesheet_view.html', context)


class TimeSheetsList(PermissionRequiredMixin, View):
    """ Show a page to view the timesheets
    """
    # TODO: loading of data may be handled through Ajax

    http_method_names = ['get', ]
    permission_required = 'reporting.read'

    def get(self, request, *args, **kwargs):
        # TODO: implement!
        raise(Http404("Not implemented"))


class TimeSheetsGenerate(PermissionRequiredMixin, View):
    """ Show a page for the selection of the month
        Generation, modification and save is handled through Ajax
    """

    http_method_names = ['get', ]
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):

        researcher = Researcher.objects.get(pk=self.kwargs['researcher'])
        context = {
            'title': "Timesheets generation for {0!s} for year {1:d}".format(researcher, self.kwargs['year']),
            'rid': self.kwargs['researcher'],
            'year': self.kwargs['year'],
            'months': list(range(1, 13, 1)),
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/timesheet_generate.html', context)


class TimeSheetsGenerateHints(PermissionRequiredMixin, View):
    """ Handle the generation of hints for a year, both for hours and missions
    """
    # TODO: add checks to generate partial hints if presence data is not yet
    # available for certain months

    http_method_names = ['get', 'post']
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):
        # First pass. Look for reporting perdiods and check if any has missions.
        # If yes, build missions table, else proceed to hints table

        y = self.kwargs['year']
        r = self.kwargs['researcher']

        # Get all reporting periods registered in the year with missions
        periods = (
            Reporting.objects
            .filter(
                Q(researcher=r) &
                Q(rp_start__lte=datetime.date(y, 12, 31)) &    # Start day before or on Dec. 31st
                Q(rp_end__gte=datetime.date(y, 1, 1)) &        # End day after or on Jan. 1st
                Q(has_missions=True)
            )
        )

        if periods.count() > 0:
            # We have at least one period with missions
            context = self.__render_mission_table(r, y)
            if 'error_message' in kwargs:
                context['error_message'] = kwargs['error_message']
            context['menu'] = UdyniMenu().getMenu(request.user)
            return render(request, 'FinancialReporting/timesheet_hints_missions.html', context)

        else:
            # No missions to report
            context = self.__render_hours_hint_table(r, y)
            context['menu'] = UdyniMenu().getMenu(request.user)
            return render(request, 'FinancialReporting/timesheet_hints.html', context)


    def post(self, request, *args, **kwargs):
        # Second pass. Get the list of missions to be reported on specific
        # reporting periods and pass the to the hint generation

        y = self.kwargs['year']
        r = self.kwargs['researcher']

        missions = {}

        p = re.compile('^(\d+)_(\d+)_(\d+)$')
        # Cycle over POST data
        for k, v in request.POST.items():
            m = p.match(k)
            if m is not None and v == 'on':
                # Match selection
                month = int(m.groups()[0])
                day = int(m.groups()[2])
                pid = int(m.groups()[1])

                # Check Presence data
                try:
                    presence = PresenceData.objects.get(researcher=r, day=datetime.date(y, month, day), ts_code=EpasCode.MISSION)
                except PresenceData.DoesNotExist:
                    # Day is not a mission
                    continue

                # Check reporting period
                try:
                    period = Reporting.objects.get(pk=pid)
                except Reporting.DoesNotExist:
                    continue
                if not (period.rp_start <= datetime.date(y, 12, 31) and period.rp_end >= datetime.date(y, 1, 1)):
                    # Wrong period
                    continue

                # Check that the day is not duplicated
                for k, v in missions.items():
                    if presence.day in v:
                        # Already present
                        msg = "Day {0!s} is reported for more than one period".format(presence.day)
                        return self.get(request, *args, error_message=msg, **kwargs)

                # Add day to missions
                if period.pk not in missions:
                    missions[period.pk] = []
                missions[period.pk].append(presence.day)

        # Save mission hints
        for k, days in missions.items():
            period = Reporting.objects.get(pk=k)
            for d in days:
                presence = PresenceData.objects.get(researcher=r, day=d)
                try:
                    hint = TimesheetMissionHint.objects.get(missionday=presence.pk)
                    if hint.reporting_period != period:
                        hint.reporting_period = period
                        hint.save()
                except TimesheetMissionHint.DoesNotExist:
                    hint = TimesheetMissionHint()
                    hint.missionday = presence
                    hint.reporting_period = period
                    hint.save()

        context = self.__render_hours_hint_table(r, y, missions)
        context['menu'] = UdyniMenu().getMenu(request.user)
        return render(request, 'FinancialReporting/timesheet_hints.html', context)

    def __render_mission_table(self, rid, year):

        # Get all the periods with missions
        periods = (
            Reporting.objects
            .filter(
                Q(researcher=rid) &
                Q(rp_start__lte=datetime.date(year, 12, 31)) &   # Start day before or on Dec. 31st
                Q(rp_end__gte=datetime.date(year, 1, 1)) &       # End day after or on Jan. 1st
                Q(has_missions=True)
            )
            .order_by()
        )

        # Extract missions from PresenceData
        missions = (
            PresenceData.objects
            .filter(researcher=rid)
            .annotate(year=ExtractYear('day'))
            .filter(year=year, ts_code=EpasCode.MISSION)
            .order_by()
        )

        # Build a period-mission map
        data = {}
        for m in missions:
            # Extract month
            month = m.day.month
            if month not in data:
                data[month] = {}
            # Add day to month
            data[month][m.day.day] = []
            for p in periods:
                if p.rp_start <= m.day and p.rp_end >= m.day:
                    data[month][m.day.day].append({
                        'day': m.day,
                        'pid': p.pk,
                    })
                    # Get hint
                    try:
                        # Hint present. Set the checkbox!
                        TimesheetMissionHint.objects.get(reporting_period=p, missionday=m)
                        data[month][m.day.day][-1]['checked'] = True
                    except TimesheetMissionHint.DoesNotExist:
                        pass

                else:
                    data[month][m.day.day].append(None)

        # Resort days for each month
        for k, v in data.items():
            data[k] = sorted(v.items())

        context = {
            'title': "Timesheet mission hints for {0!s} for year {1:d}".format(Researcher.objects.get(pk=rid), year),
            'year': year,
            'rid': rid,
            'data': sorted(data.items()),   # Sort months
            'periods': periods,
        }
        return context


    def __render_hours_hint_table(self, rid, year, missions=None):

        # Given a researcher and a year present the reporting situation divided by month
        # If hints are present, they're used, otherwise the hours are divided proportionally
        # to the total working hours.

        context = {
            'title': "Timesheet hints for {0!s} for year {1:d}".format(Researcher.objects.get(pk=rid), year),
            'year': year,
            'rid': rid,
        }

        # Get all reporting periods registered in the year
        periods = (
            Reporting.objects
            .filter(
                Q(researcher=rid) &
                Q(rp_start__lte=datetime.date(year, 12, 31)) &   # Start day before or on Dec. 31st
                Q(rp_end__gte=datetime.date(year, 1, 1))         # End day after or on Jan. 1st
            )
            .order_by('project', 'wp', 'rp_start')
        )

        # List of periods of interest
        plist = []

        # Cycle over periods and split hours
        for p in periods:
            # Initialize info structure for the period
            info = {}
            info['id'] = p.pk
            if p.wp is not None:
                info['name'] = "{0:s}: {1:s}".format(p.project.name, p.wp.name)
            else:
                info['name'] = "{0:s}".format(p.project.name)
            # Set the total hours
            info['hours'] = p.hours
            # NOTE: id = 0 is previous year, 1-12 are months of current year, 13 is next year
            info['bymonth'] = [0.0 for i in range(14)]     # Hours by month
            info['ava_hours'] = [0.0 for i in range(14)]   # Total hours available in each month

            # Init working days and total worked hours
            working_days = [{'tot_hours': 0.0, 'working_days': 0.0} for i in range(14)]

            # Check start dates and count days before and after current year
            if p.rp_start.year < year:
                m_start = datetime.date(year, 1, 1)
                q_filter = (
                    Q(researcher=rid) &
                    Q(day__gte=p.rp_start) &
                    Q(day__lt=m_start) &
                    Q(ts_hours__gt=0) &
                    Q(ts_code=EpasCode.NONE)
                )
                q = (
                    PresenceData.objects
                    .filter(q_filter)
                    .aggregate(
                        tot_hours=Sum('ts_hours'),
                        working_days=Count('ts_hours'),
                    )
                )
                working_days[0]['working_days'] = q['working_days']
                working_days[0]['tot_hours'] = q['tot_hours']
            else:
                m_start = p.rp_start

            if p.rp_end.year > year:
                m_end = datetime.date(year, 12, 31)
                q_filter = (
                    Q(researcher=rid) &
                    Q(day__gt=m_end) &
                    Q(day__lte=p.rp_end) &
                    Q(ts_hours__gt=0) &
                    Q(ts_code=EpasCode.NONE)
                )
                q = (
                    PresenceData.objects
                    .filter(q_filter)
                    .aggregate(
                        tot_hours=Sum('ts_hours'),
                        working_days=Count('ts_hours'),
                    )
                )
                # If for the following year the TS hours were not assesed already
                # use the raw presence hours, so that hours can be shared on the
                # next year
                if q['tot_hours'] is None:
                    q_filter = (
                        Q(researcher=rid) &
                        Q(day__gt=m_end) &
                        Q(day__lte=p.rp_end) &
                        Q(hours__gt=0) &
                        (Q(code=None) | Q(code__ts_code=EpasCode.NONE))
                    )
                    q = (
                        PresenceData.objects
                        .filter(q_filter)
                        .aggregate(
                            tot_hours=Sum('hours'),
                            working_days=Count('hours'),
                        )
                    )
                    if q['tot_hours'] is not None:
                        q['tot_hours'] = round(q['tot_hours'] * 2) / 2
                working_days[13]['working_days'] = q['working_days'] if q['working_days'] is not None else 0
                working_days[13]['tot_hours'] = q['tot_hours'] if q['tot_hours'] is not None else 0
            else:
                m_end = p.rp_end

            # Get total worked hours and number of working days of current year
            # that are within the reporting period
            wday = (
                PresenceData.objects
                .filter(Q(researcher=rid) & Q(day__gte=m_start) & Q(day__lte=m_end))
                .annotate(month=ExtractMonth('day'))
                .values('month')
                .annotate(
                    tot_hours=Sum('ts_hours', filter=Q(ts_code=EpasCode.NONE)),
                    working_days=Count('ts_hours', filter=Q(ts_code=EpasCode.NONE) & Q(ts_hours__gt=0)),
                )
                .order_by()
            )
            for w in wday:
                if w['tot_hours'] is not None:
                    working_days[w['month']]['tot_hours'] = w['tot_hours']
                else:
                    working_days[w['month']]['tot_hours'] = 0.0
                working_days[w['month']]['working_days'] = w['working_days']

            # Total number of working days in the period
            total_working_days = 0
            for v in working_days:
                total_working_days += v['working_days']

            # Hours to use for total in the period
            act_hours = p.hours

            # Add selected missions to working days and to hours
            if p.has_missions:
                # Init mission hours
                mission_hours = [0 for i in range(14)]
                # Check mission hints for the year before
                mh = (
                    TimesheetMissionHint.objects
                    .annotate(year=ExtractYear('missionday__day'))
                    .filter(Q(reporting_period=p) & Q(year__lt=year))
                    .aggregate(h=Sum('missionday__ts_hours'))
                )
                if mh['h']:
                    mission_hours[0] = mh['h']
                    act_hours -= mh['h']

                # Check mission hints for the year after
                mh = (
                    TimesheetMissionHint.objects
                    .annotate(year=ExtractYear('missionday__day'))
                    .filter(Q(reporting_period=p) & Q(year__gt=year))
                    .aggregate(h=Sum('missionday__ts_hours'), d=Count('missionday'))
                )
                if mh['h']:
                    mission_hours[13] = mh['h']
                    act_hours -= mh['h']

                # We should remove the hours from the missions that we are reporting
                if p.pk in missions:
                    q = Q()
                    for d in missions[p.pk]:
                        q |= Q(day=d)
                    hours = (
                        PresenceData.objects
                        .filter(Q(researcher=rid) & q)
                        .annotate(month=ExtractMonth('day'))
                        .values('month')
                        .annotate(h=Sum('ts_hours'))
                        .order_by()
                    )

                    for mh in hours:
                        mission_hours[mh['month']] = mh['h']
                        act_hours -= mh['h']

                if sum(mission_hours):
                    info['has_missions'] = True
                    info['mission_hours'] = mission_hours

            print("Before:", working_days[0]['working_days'], "After:", working_days[13]['working_days'], "Total:", total_working_days)

            # Get previously saved hints
            hints = TimesheetHint.objects.filter(reporting_period=p, year=year)
            hints_p = TimesheetHint.objects.aggregate(h=Sum('hours', filter=Q(reporting_period=p) & Q(year__lt=year)))
            hints_n = TimesheetHint.objects.aggregate(h=Sum('hours', filter=Q(reporting_period=p) & Q(year__gt=year)))
            # Cycle over months and set hours by hint if present. Hints must have precedence. Month/periods without hint
            # will get an estimate based on the number of hours not allocated
            allocated_hours = 0  # Hours allocated by hint
            tot_days_nam = 0     # Total working days in months without hints
            for m in range(14):
                if m == 0:
                    if hints_p['h'] is not None:
                        info['bymonth'][0] = hints_p['h']
                        allocated_hours += hints_p['h']
                    else:
                        info['bymonth'][0] = None
                        tot_days_nam += working_days[0]['working_days']
                elif m == 13:
                    if hints_n['h'] is not None:
                        info['bymonth'][13] = hints_n['h']
                        allocated_hours += hints_n['h']
                    else:
                        info['bymonth'][13] = None
                        tot_days_nam += working_days[13]['working_days']
                else:
                    if hints:
                        for h in hints:
                            if h.month == m:
                                info['bymonth'][m] = h.hours
                                allocated_hours += h.hours
                                break
                    else:
                        info['bymonth'][m] = None
                        tot_days_nam += working_days[m]['working_days']
                # Set available hours
                info['ava_hours'][m] = working_days[m]['tot_hours']

            # Hours not allocated
            res_hours = act_hours - allocated_hours

            for m in range(14):
                if info['bymonth'][m] is None:
                    if working_days[m]['working_days']:
                        info['bymonth'][m] = -res_hours * (working_days[m]['working_days'] / tot_days_nam)
                    else:
                        info['bymonth'][m] = 0.0

            # Round guesses and check that the total matches the total hours for the period
            info['bymonth'] = self.__check_period_hours(info['bymonth'], act_hours)

            # Append to output data
            plist.append(info)

        # Get total TS working hours for each month
        ts_wh = (
            PresenceData.objects
            .filter(Q(researcher=rid))
            .annotate(year=ExtractYear('day'))
            .filter(year=year)
            .annotate(month=ExtractMonth('day'))
            .values('month')
            .annotate(
                tot_hours=Sum('ts_hours', filter=Q(ts_code=EpasCode.NONE) | Q(ts_code=EpasCode.MISSION)),
            )
            .order_by()
        )

        # Store total hours in context
        context['ts_wh'] = [0 for i in range(12)]
        context['total_hours'] = 0
        for q in ts_wh:
            context['ts_wh'][q['month'] - 1] = q['tot_hours']
            context['total_hours'] += q['tot_hours']

        # Get list of missions not reported to a specific period
        q = Q()
        if missions is not None:
            for k, v in missions.items():
                for d in v:
                    q |= Q(day=d)
        internal_missions = (
            PresenceData.objects
            .filter(researcher=rid)
            .annotate(year=ExtractYear('day'))
            .filter(Q(year=year) & Q(ts_code=EpasCode.MISSION) & ~q)
            .annotate(month=ExtractMonth('day'))
            .values('month')
            .annotate(
                h=Sum('ts_hours')
            )
            .order_by()
        )

        # Add internal activities
        internal = {}
        internal['id'] = -1
        internal['name'] = "Internal activities"
        internal['hours'] = 0
        internal['bymonth'] = [0 for i in range(14)]
        internal['ava_hours'] = [0 for i in range(14)]
        for m in range(1, 13, 1):
            tot = 0
            for p in plist:
                tot += p['bymonth'][m]
                if 'has_missions' in p:
                    tot += p['mission_hours'][m]
            h = context['ts_wh'][m - 1] - tot
            internal['bymonth'][m] = h
            internal['hours'] += h
            internal['ava_hours'][m] = context['ts_wh'][m - 1]
        if internal_missions.count():
            internal['has_missions'] = True
            internal['mission_hours'] = [0 for i in range(14)]
            for im in internal_missions:
                internal['mission_hours'][im['month']] = im['h']

        # Add interal to project list
        plist.append(internal)

        # Store project list in context
        context['project_list'] = plist

        # Render page
        return context

    def __check_period_hours(self, bymonth, total):
        # Rounding the total and checking that the sum is consistent
        by_m_h = []
        by_m_r = []

        # Months
        for m in range(14):
            if bymonth[m] < 0:
                # Guess
                by_m_h.append(round(-bymonth[m]))
                by_m_r.append((-bymonth[m]) - by_m_h[-1])
            else:
                # Hint
                by_m_h.append(bymonth[m])
                by_m_r.append(0.0)

        # Check if total has a decimal part
        t_f, t_w = math.modf(total)

        # Difference between total hours and guess
        delta = total - sum(by_m_h)

        print(delta)

        if delta > 0:
            # Adjustment needed. Missing hours
            d_f, d_w = math.modf(delta)
            while d_w > 0:
                m = max(by_m_r)
                if m != 0:
                    i = by_m_r.index(m)
                    by_m_h[i] += 0.5
                    by_m_r[i] = 0.0
                    d_w -= 0.5
                else:
                    i = random.randrange(1, 12)
                    by_m_h[i] += 0.5
                    d_w -= 0.5

            if d_f != 0:
                m = max(by_m_r)
                i = by_m_r.index(m)
                by_m_h[i] += d_f

        elif delta < 0:
            # Adjustment needed. Hours in excess
            d_f, d_w = math.modf(delta)
            while d_w < 0:
                m = min(by_m_r)
                if m != 0:
                    i = by_m_r.index(m)
                    by_m_h[i] -= 0.5
                    by_m_r[i] = 0.0
                    d_w += 0.5
                else:
                    i = random.randrange(1, 12)
                    if by_m_h[i] >= 0.5:
                        by_m_h[i] -= 0.5
                        d_w += 0.5

            if d_f != 0:
                m = min(by_m_r)
                i = by_m_r.index(m)
                by_m_h[i] += d_f

        return by_m_h


class TimeSheetsPrint(PermissionRequiredMixin, View):

    http_method_names = ['get', 'post']
    permission_required = 'reporting.read'

    def get(self, request, *args, **kwargs):
        # Save the modified year situation as TimesheetHints (if some hints are alread
        # available they're updated)
        year = self.kwargs['year']
        rid = self.kwargs['researcher']

        # Check which months are available
        good_months = []
        for m in range(1, 13, 1):
            if CheckTimesheetData(rid, year, m):
                good_months.append(m)

        researcher = Researcher.objects.get(pk=rid)
        context = {
            'title': "Print timesheets for {0!s} for year {1:d}".format(researcher, year),
            'months': good_months,
            'year': year,
            'rid': rid,
            'menu': UdyniMenu().getMenu(request.user),
        }
        return render(request, 'FinancialReporting/timesheet_printsummary.html', context)

    def post(self, request, *args, **kwargs):
        year = self.kwargs['year']
        rid = self.kwargs['researcher']

        months = []
        for k, v in request.POST.items():
            m = re.match('^m_(\d+)$', k)
            if m is not None:
                months.append(int(m.groups()[0]))
        months = sorted(months)


        try:
            context = []
            for month in months:
                print("Processing month", month)

                # Get number of days in month
                ndays = calendar.monthrange(year, month)[1]

                # Get role from ResearcherRole table
                current_role = None
                roles = ResearcherRole.objects.filter(researcher=rid).order_by('start_date')
                for role in roles:
                    # TODO: check criteria to switch to another role based on date
                    if role.start_date <= datetime.date(year, month, 1):
                        current_role = role.get_role_display()
                    else:
                        break
                # Default to researcher if nothing is set in ResearcherRole
                if current_role is None:
                    current_role = "Researcher"

                # Get researcher
                researcher = Researcher.objects.get(pk=rid)
                # Load timesheet data
                ts_data = LoadTimesheetData(rid, year, month)
                # Director
                q = (
                    ResearcherRole.objects
                    .filter(role=ResearcherRole.INSTITUTE_DIRECTOR)
                    .filter(start_date__lt=datetime.date(year, month, ndays))
                    .order_by('-start_date')
                    .first()
                    .researcher
                )
                director = "{0!s} (IFN Director)".format(q)

                # Check needed signatures
                signatures = {}
                for project in ts_data['projects']:
                    if 'pi_id' in project:
                        if project['pi_id'] == researcher or project['pi_id'] is None:
                            # director
                            name = str(director)
                            if name not in signatures:
                                signatures[name] = []
                            signatures[name].append(project['name'])
                        else:
                            name = str(project['pi_id'])
                            if name not in signatures:
                                signatures[name] = []
                            signatures[name].append(project['name'])

                for k, v in signatures.items():
                    signatures[k] = ", ".join(sorted(v))

                context.append({
                    'title': "Timesheets for {0!s} for year {1:d}".format(researcher, year),
                    'month': month,
                    'year': year,
                    'researcher': "{0:s} {1:s}".format(researcher.name, researcher.surname),
                    'employment': current_role,
                    'beneficiary': "CNR-IFN",
                    'ts': ts_data,
                    'signatures': signatures,
                })

            print(len(context))

            return FileResponse(PrintPFDTimesheet(context), as_attachment=True, filename='{0:s}_{1:04d}.pdf'.format(researcher.surname.lower(), year));
            # return FileResponse(PrintPFDTimesheet(context), as_attachment=False, filename='{0:s}_{1:04d}.pdf'.format(researcher.surname.lower(), year));

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Http404(str(e))


class TimeSheetsAjaxGenerate(PermissionRequiredMixin, View):
    """ Handle the data exchange to generate a timesheet for a given month
    """

    http_method_names = ['get', 'post']
    permission_required = 'reporting.modify'

    def get(self, request, *args, **kwargs):
        year = self.kwargs['year']
        rid = self.kwargs['researcher']
        month = self.kwargs['month']
        ndays = calendar.monthrange(year, month)[1]

        # Get all reporting periods registered in the month
        periods = (
            Reporting.objects
            .filter(
                Q(researcher=rid) &
                Q(rp_start__lte=datetime.date(year, month, ndays)) &  # Start day before or on last day
                Q(rp_end__gte=datetime.date(year, month, 1))          # End day after or on first day
            )
            .order_by()
        )

        # First thing we check if we have all the hints for the selected month,
        # otherwise redirect to hints page
        hints = {}
        for p in periods:
            # First check that all the hints for the period are consistent
            if not self.checkHintsConsistency(p, year):
                return JsonResponse({'generated': False, 'error': 'no-hint', 'message': 'Hints for month {0:d}/{1:d} for project {2!s} ({3!s}) are not consistent'.format(month, year, p.project.name, p.wp.name if p.wp else 'None')})

            # Get hint for the period
            try:
                hints[p.pk] = TimesheetHint.objects.get(reporting_period=p, year=year, month=month)
            except TimesheetHint.DoesNotExist:
                # If we are missing a hint for a period we cannot proceed
                return JsonResponse({'generated': False, 'error': 'no-hint', 'message': 'No hint found for month {0:d}/{1:d} for project {2!s} ({3!s})'.format(month, year, p.project.name, p.wp.name if p.wp else 'None')})
        try:
            data = {
                'generated': True,
                'ts': GenerateTimesheetData(rid, year, month),
            }
            return JsonResponse(data)
        except Exception as e:
            raise e
            return JsonResponse({'generated': False, 'error': str(e)})

    def post(self, request, *args, **kwargs):
        # Kwargs
        year = self.kwargs['year']
        month = self.kwargs['month']

        # Decode json data submitted
        try:
            data = json.loads(request.body.decode("utf-8"))

        except json.JSONDecodeError as e:
            return JsonResponse({'saveok': False, 'error': str(e)})

        # Cycle over submitted data
        for k, days in data.items():
            try:
                # Get period from DB
                period = Reporting.objects.get(pk=int(k))

                # Init new days query filter
                new_days = Q()

                # Cycle over days
                for d, h in days.items():
                    # Build date
                    date = datetime.date(year, month, int(d) + 1)
                    try:
                        # Get object if exixst
                        obj = TimesheetHours.objects.get(reporting_period=period, day=date)
                        if obj.hours != h:
                            # Update object if needed
                            obj.hours = h
                            obj.save()

                    except TimesheetHours.DoesNotExist:
                        # Object does not exist. Create a new one.
                        obj = TimesheetHours()
                        obj.reporting_period = period
                        obj.day = date
                        obj.hours = h
                        obj.save()

                    # Add date to new days
                    new_days |= Q(day=date)

                # Delete old unused data
                objs = (
                    TimesheetHours.objects
                    .filter(reporting_period=period.pk)
                    .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
                    .filter(
                        Q(year=year) &
                        Q(month=month) &
                        ~new_days
                    )
                )

                if objs.count():
                    objs.delete()

            except Reporting.DoesNotExist:
                JsonResponse({'saveok': False, 'error': "Reporting period {0!s} does not exist".format(k)})

        return JsonResponse({'saveok': True})

    def checkHintsConsistency(self, p, year):
        # Sum all the hints
        hints = (
            TimesheetHint.objects
            .filter(reporting_period=p, year=year)
            .aggregate(h=Sum('hours'))
        )['h']
        hints_p = (
            TimesheetHint.objects
            .filter(reporting_period=p, year__lt=year)
            .aggregate(h=Sum('hours'))
        )['h']
        hints_n = (
            TimesheetHint.objects
            .filter(reporting_period=p, year__gt=year)
            .aggregate(h=Sum('hours'))
        )['h']

        if hints is None:
            hints = 0.0
        if hints_p is None:
            hints_p = 0.0
        if hints_n is None:
            hints_n = 0.0

        # Check total sum
        if hints + hints_p + hints_n > p.hours:
            return False

        # Number of days in the period before this year
        delta_p = (datetime.date(year, 1, 1) - p.rp_start).days
        # Number of days in the period after this year
        delta_n = (p.rp_end - datetime.date(year, 12, 31)).days

        # No days before, no hours
        if not delta_p and hints_p:
            return False

        # No days after, no hours
        if not delta_n and hints_n:
            return False

        # No days before or after, the sum must match
        if not delta_p and not delta_n and hints != p.hours:
            return False

        return True


class TimeSheetsAjaxView(PermissionRequiredMixin, View):
    """ Handle the data exchange to generate a timesheet for a given month
    """

    http_method_names = ['get', ]
    permission_required = 'reporting.read'

    def get(self, request, *args, **kwargs):
        return JsonResponse({})


class TimeSheetsAjaxSaveHints(PermissionRequiredMixin, View):
    """ Save hints in the database
    """

    http_method_names = ['post', ]
    permission_required = 'reporting.modify'

    def post(self, request, *args, **kwargs):
        # Save the modified year situation as TimesheetHints (if some hints are alread
        # available they're updated)
        y = self.kwargs['year']
        # r = self.kwargs['researcher']

        # Decode json data submitted
        try:
            data = json.loads(request.body.decode("utf-8"))

        except json.JSONDecodeError as e:
            return JsonResponse({'result': 'failed', 'error': str(e)})

        # Cycle through data and save as hints
        try:
            for k, v in data.items():
                for m, h in v.items():
                    # k: period pk
                    # m: month
                    # h: hours
                    try:
                        # We already have an hint
                        hint = TimesheetHint.objects.get(reporting_period=int(k), year=y, month=int(m))
                        if hint.hours != h:
                            hint.hours = h
                            hint.save()

                    except TimesheetHint.DoesNotExist:
                        try:
                            period = Reporting.objects.get(pk=int(k))
                        except Reporting.DoesNotExist:
                            return JsonResponse({'result': 'failed', 'error': "Reporting period with ID {0!s} does not exist".format(m)})
                        # New hint
                        hint = TimesheetHint()
                        hint.reporting_period = period
                        hint.year = y
                        hint.month = int(m)
                        hint.hours = h
                        hint.save()

                    except TimesheetHint.MultipleObjectsReturned:
                        # This should never happen as the hint should be unique
                        return JsonResponse({'result': 'failed', 'error': "period={0:ds"})
        except Exception as e:
            return JsonResponse({'result': 'failed', 'error': str(e)})

        return JsonResponse({'result': 'ok'})


class TimesheetAjaxDenied(View):
    http_method_names = ['get', ]
    def get(self, request, *args, **kwargs):
        raise Http404('Resource not available')
