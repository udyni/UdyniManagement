import re
import pandas as pd
import numpy as np
import datetime
import calendar
import random

from Tags.templatetags.tr_month import month_num2it

from django.db.models import Q, F
from django.db.models import Sum, Subquery, OuterRef
from .models import BankHoliday, PresenceData, Reporting, TimesheetHint, TimesheetMissionHint, EpasCode, TimesheetHours
from django.db.models.functions import ExtractYear, ExtractMonth, Coalesce


def process_presences(xls, researcher):
    # Cycle through sheets
    out = {}
    # First find out if the xls comes from EPAS
    if 'Riassunto RF' in xls.sheet_names:
        # Old format
        for n in xls.sheet_names:
            m = re.match(r"\d+\-(\d+)|(\d+)", n)
            if m is not None:
                month = [int(el) for el in m.groups() if el is not None]
                month = month_num2it(month[0])

                # Convert sheet to dataframe
                df = xls.parse(n, header=3, usecols="A:D")

                # Get year from date
                year = df.loc[0, 'Giorno'].year
                if year not in out:
                    out[year] = {}

                # Lines that actually had data
                good_lines = ~pd.isna(df['Giorno']).to_numpy()

                out[year][month] = pd.DataFrame()
                out[year][month]['Date'] = pd.to_datetime(df.loc[good_lines, 'Giorno'])
                # Convert working hours
                hours = df.loc[good_lines, 'Ore lavorate']
                hours[pd.isna(hours)] = 0.0
                out[year][month]['Hours'] = hours
                # Convert absence codes
                codes = df.loc[good_lines, 'Ferie/Missione']
                codes[pd.isna(codes)] = ""
                codes[codes == "Ferie"] = "32"
                codes[codes == "ferie"] = "32"
                codes[codes == "RF"] = "91"
                codes[codes == "Missione"] = "92"
                codes[codes == "missione"] = "92"
                codes[codes == "Malattia"] = "111"
                codes[codes == "malattia"] = "111"
                out[year][month]['Code'] = codes

                # Add 7.2 hours to missions (but only on working days!)
                weekday = out[year][month].loc[:, 'Date'].apply(lambda date: date.isoweekday())
                bank_holiday = out[year][month].loc[:, 'Date'].apply(check_bank_holiday)
                working_days = np.logical_and(weekday < 6, np.logical_not(bank_holiday))
                out[year][month].loc[np.logical_and(out[year][month].loc[:, 'Code'] == "92", working_days), 'Hours'] = 7.2

    else:
        # From EPAS
        for n in xls.sheet_names:
            m = re.match(r"([a-zA-Z ]+)_([a-z]+)(\d+)", n)
            if m is not None:
                name = str(m.groups()[0])
                if name != researcher:
                    continue
                year = int(m.groups()[2])
                if year not in out:
                    out[year] = {}
                month = str(m.groups()[1])

                # Convert sheet to dataframe
                df = xls.parse(n)

                out[year][month] = pd.DataFrame()
                # Convert date
                out[year][month]['Date'] = pd.to_datetime(df['Data'])
                # Convert working hours
                out[year][month]['Hours'] = pd.to_timedelta(df['Lavoro effettivo (hh:mm)'] + ":00") / np.timedelta64(1, 'h')
                # Convert absence codes
                if df['Tutti i codici di assenza'].dtype == np.float64:
                    # Only numeric codes, coverted to float (will not match EpasCode)
                    out[year][month].loc[:, 'Code'] = ""
                    out[year][month].loc[~np.isnan(df.loc[:, 'Tutti i codici di assenza']), 'Code'] = \
                        df.loc[~np.isnan(df.loc[:, 'Tutti i codici di assenza']), 'Tutti i codici di assenza'].astype(int).astype(str)
                else:
                    out[year][month]['Code'] = df['Tutti i codici di assenza'].astype(str)
                out[year][month].loc[out[year][month].loc[:, 'Code'] == 'nan', 'Code'] = ""
                # Check multiple codes
                mpc = out[year][month].loc[:, 'Code'].apply(lambda code: code.find(";") != -1)
                out[year][month].loc[mpc, 'Code'] = out[year][month].loc[mpc, 'Code'].apply(get_single_code)

    return out


def get_single_code(code):
    # Return a single epas code for days with multiple codes
    # TODO: this may not be trivial
    codes = code.split(";")
    i = 0
    try:
        i = codes.index("92E")
    except ValueError:
        try:
            i = codes.index("92")
        except ValueError:
            try:
                i = codes.index("92M")
            except ValueError:
                i = 0
    return codes[i]


def summarize_presences(presences):
    out = {}
    # Cycle over years
    for year, v1 in presences.items():
        out[year] = {}
        tot_hours = 0
        # Cycle over months
        for month, v2 in v1.items():
            out[year][month] = {}
            out[year][month]['hours'] = np.sum(v2['Hours'])
            tot_hours += out[year][month]['hours']
            out[year][month]['workingdays'] = np.sum(v2['Hours'] > 0)
            out[year][month]['codes'] = {}
            uc = np.unique(v2['Code'])
            for c in uc:
                if c == "":
                    continue
                out[year][month]['codes'][c] = np.sum(v2['Code'] == c)
        out[year]['total'] = tot_hours
    return out


def serialize_presences(presences):
    out = {}
    # Cycle over years
    for year, v1 in presences.items():
        out[year] = {}
        # Cycle over months
        for month, v2 in v1.items():
            out[year][month] = v2.to_json()
    return out


def unserialize_presences(json):
    out = {}
    # Cycle over years
    for year, v1 in json.items():
        year = int(year)
        out[year] = {}
        # Cycle over months
        for month, v2 in v1.items():
            out[year][month] = pd.read_json(v2)
    return out


def check_presences_unique(presences):
    dates = []
    print("CHECK for duplicates!")
    for year, v1 in presences.items():
        for month, v2 in v1.items():
            for i, row in v2.iterrows():
                date = row['Date'].strftime("%Y-%m-%d")
                if date in dates:
                    print("Date {0:s} is duplicated!")
                else:
                    dates.append(date)
    print("CHECK done!")


def check_bank_holiday(date):
    try:
        BankHoliday.objects.get(year=0, month=date.month, day=date.day)
        return True
    except BankHoliday.DoesNotExist:
        try:
            BankHoliday.objects.get(year=date.year, month=date.month, day=date.day)
            return True
        except BankHoliday.DoesNotExist:
            return False


def GenerateTimesheetData(rid, year, month):
    print("Generating timesheets for {0:d}/{1:d}".format(month, year))
    data = {}

    # Build days array, marking Saturdays and Sundays as holiday
    ndays = calendar.monthrange(year, month)[1]
    data['numdays'] = ndays     # Number of days in month
    data['days'] = []           # Array of data for each day
    data['absence_code'] = []   # Absence code for every day
    for d in range(1, ndays + 1, 1):
        day = {}
        day['n'] = d

        # Check Saturday and Sunday
        date = datetime.date(year=year, month=month, day=d)
        if date.weekday() > 4:
            day['holiday'] = True
        else:
            day['holiday'] = False

        # Append day
        data['days'].append(day)

        # Set absence code as public holiday if needed
        absence =  {'a': "", 'holiday': day['holiday']}
        if check_bank_holiday(date):
           absence['a'] = "PH"
        # Append absence
        data['absence_code'].append(absence)

    # Load presence data for the month
    presences = (
        PresenceData.objects
        .filter(
            Q(researcher=rid) &
            Q(day__gte=datetime.date(year, month, 1)) &
            Q(day__lte=datetime.date(year, month, ndays))
        )
        .order_by('day')
    )

    # Extract available hours for each day and absence code if available
    available_hours = [0.0 for i in range(ndays)]
    for p in presences:
        d = p.day.day
        # Set available hours
        if p.ts_code == EpasCode.NONE and p.ts_hours > 0:
            available_hours[d - 1] = p.ts_hours
        # Update absence code
        if p.ts_code == EpasCode.ILLNESS:
            data['absence_code'][d - 1]['a'] = 'SL'
        else:
            if data['absence_code'][d - 1]['a'] != 'PH':
                if p.ts_code == EpasCode.MISSION:
                    data['absence_code'][d - 1]['a'] = 'BT'
                elif p.ts_code == EpasCode.HOLIDAYS:
                    data['absence_code'][d - 1]['a'] = 'AH'
                elif p.ts_code == EpasCode.OTHER:
                    data['absence_code'][d - 1]['a'] = 'OA'

    # Get all reporting periods for the current researcher in the month
    rps = (
        Reporting.objects
        .filter(
            Q(researcher=rid) &
            Q(rp_start__lte=datetime.date(year, month, ndays)) &
            Q(rp_end__gte=datetime.date(year, month, 1))
        )
        .order_by()
    )

    # Group all reporting periods by project
    projects = {}
    for p in rps:
        pid = p.project.pk
        if p.wp is None:
            # Project without WPs
            if pid not in projects:
                projects[pid] = {}
                projects[pid]['has_wp'] = False
                projects[pid]['period'] = [p, ]   # NB: this is a list to handle multiple project periods in the same month
            else:
                projects[pid]['period'].append(p)
        else:
            # Project with WPs
            if pid not in projects:
                projects[pid] = {}
                projects[pid]['has_wp'] = True
                projects[pid]['wps'] = []
            projects[pid]['wps'].append(p)

    # Cycle over periods, load hints and split hours over days
    data['projects'] = []
    for pk, p in projects.items():
        if p['has_wp']:
            new_p = {}
            # Project with WPs
            new_p['has_wps'] = True
            # Project name and reference
            new_p['name'] = p['wps'][0].project.name
            print(p['wps'][0].project.name)
            new_p['ref'] = p['wps'][0].project.reference
            # Cycle over work packages
            new_p['wps'] = []
            for wp in p['wps']:
                new_wp = {}
                # WP name and description
                new_wp['name'] = wp.wp.name
                new_wp['desc'] = wp.wp.desc
                new_wp['id'] = wp.pk
                # Split hours over days  NB: available_hours is updated during the split!
                new_wp['days'], new_wp['generated'] = SplitOverDays(wp, year, month, available_hours)
                # Set by default as 'not the last'
                new_wp['last'] = False
                # Sum up hours
                new_wp['total'] = 0
                for d in new_wp['days']:
                    new_wp['total'] += d['h']
                # Append WP
                new_p['wps'].append(new_wp)

            # Set last WP as last
            new_p['wps'][-1]['last'] = True

            # Sum hours for all WPs for the project totals
            new_p['days'] = [{'h': 0.0, 'mission': False} for i in range(ndays)]  # Will be the sum of all the WPs
            # Cycle over wps and sum
            for wp in new_p['wps']:
                for i in range(ndays):
                    new_p['days'][i]['h'] += wp['days'][i]['h']
            # Total hours of the project
            new_p['total'] = 0.0
            for d in new_p['days']:
                new_p['total'] += d['h']

            # Add project
            data['projects'].append(new_p)

        else:
            for sub_p in p['period']:
                new_p = {}
                # Project without WPs
                new_p['has_wps'] = False
                # Project name
                new_p['name'] = sub_p.project.name
                # Project reference
                new_p['ref'] = sub_p.project.reference
                new_p['id'] = sub_p.pk
                # Split hours over days  NB: available_hours is updated during the split!
                new_p['days'], new_p['generated'] = SplitOverDays(sub_p, year, month, available_hours)
                new_p['total'] = 0.0
                for d in new_p['days']:
                    new_p['total'] += d['h']

                # Add project
                data['projects'].append(new_p)

    # Add internal activities
    internal = {
        'name': 'Internal activities',
        'ref': '',
        'id': -1,
        'has_wps': False,
        'days': [{'h': available_hours[i], 'mission': False} for i in range(len(available_hours))],
        'total': sum(available_hours),
        'generated': 0,
    }
    # Get all missions reported in the month by the researcher
    reported_missions = (
        TimesheetMissionHint.objects
        .filter(Q(reporting_period__researcher=rid))
        .annotate(year=ExtractYear('missionday__day'), month=ExtractMonth('missionday__day'))
        .filter(year=year, month=month)
        .order_by()
    )

    q = Q()
    if reported_missions.count():
        for rpm in reported_missions:
            q |= Q(day=rpm.missionday.day)

    # Get missions not assigned to any period
    missions = (
        PresenceData.objects
        .filter(researcher=rid)
        .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
        .filter(
            Q(year=year) &
            Q(month=month) &
            Q(ts_code=EpasCode.MISSION) &
            Q(ts_hours__gt=0) &
            ~q
        )
        .order_by()
    )

    # Add missions to interal activities
    if missions.count():
        for m in missions:
            internal['days'][m.missionday.day.day - 1]['h'] = m.missionday.hours
            internal['days'][m.missionday.day.day - 1]['mission'] = True

    # Add internal activities as a project
    data['projects'].append(internal)

    # Extend holiday tag and sum hours for each day
    data['day_total'] = [{'h': 0.0, 'holiday': data['days'][i]['holiday']} for i in range(ndays)]
    for p in data['projects']:
        if p['has_wps']:
            for wp in p['wps']:
                for i in range(len(wp['days'])):
                    wp['days'][i]['holiday'] = data['days'][i]['holiday']
                    data['day_total'][i]['h'] += wp['days'][i]['h']
        for i in range(len(p['days'])):
            p['days'][i]['holiday'] = data['days'][i]['holiday']
            if not p['has_wps']:
                data['day_total'][i]['h'] += p['days'][i]['h']

    data['grand_total'] = 0.0
    for d in data['day_total']:
        data['grand_total'] += d['h']

    # Check if TS has been modified since last save
    def updateModified(out, new):
        if out == 1:
            return out
        else:
            return new
    data['modified'] = 0
    for p in data['projects']:
        if p['has_wps']:
            for wp in p['wps']:
                if wp['generated']:
                    data['modified'] = updateModified(data['modified'], wp['generated'])
        else:
            if p['generated']:
                data['modified'] = updateModified(data['modified'], p['generated'])

    return data


def SplitOverDays(period, year, month, available_hours):
    # Days in the month
    ndays = calendar.monthrange(year, month)[1]

    # Output array
    out = [0.0 for i in range(ndays)]

    # First get the hint
    try:
        hint = TimesheetHint.objects.get(reporting_period=period.pk, year=year, month=month)
        hours = hint.hours
    except TimesheetHint.DoesNotExist:
        raise ValueError("Period {0!s} has no hint!".format(period))

    # Check if we should use the full month or just a part of it
    if period.rp_start < datetime.date(year, month, 1):
        first_day = 1
    else:
        first_day = period.rp_start.day
    if period.rp_end > datetime.date(year, month, ndays):
        last_day = ndays
    else:
        last_day = period.rp_end.day

    # Load saved hours per day
    saved_ts = (
        TimesheetHours.objects
        .filter(reporting_period=period.pk)
        .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
        .filter(year=year, month=month)
        .order_by()
    )

    generate = 0
    if saved_ts.count() > 0:
        # Sum saved hours
        saved_hours = 0.0
        for obj in saved_ts:
            saved_hours += obj.hours

        if saved_hours == hours:
            # We alread have all the hours we need
            for obj in saved_ts:
                out[obj.day.day - 1] = obj.hours
                available_hours[obj.day.day - 1] -= obj.hours
        else:
            generate = 1  # Modified
    else:
        generate = 2  # Never generated

    if generate == 2 and not hours:
        generate = 0

    if generate:
        # Hints are changed. We have to split again

        # Guess hours per day
        hpd = 2.0

        # Calculate needed days
        t_days = round(hours / hpd)

        # Check which days have hours available
        av_days = []
        for i in range(first_day - 1, last_day, 1):
            if available_hours[i] > 0:
                av_days.append(i)
        # Add a check if no days are available
        if not len(av_days):
            if hours:
                raise ValueError("Hint for project {0:s} (WP: {1:s}) for month {2:d} requires {3:.1f} hours but there are no days available".format(period.project, period.wp, month, hours))
            # Reset generate as there are nothing that can be done
            generate = 0

        else:
            rand_days = random.sample(av_days, len(av_days))

            if t_days > len(av_days):
                # We have more needed than available days. Change mean hours per day
                hpd = round(hours / len(av_days) * 2) / 2  # Rounded to the nearest half hour
                t_days = len(av_days)

            if t_days <= 3:
                # Sequential allocation
                d = rand_days.pop()
                while hours > 0:

                    if hours > hpd + 0.5:
                        if available_hours[d] >= hpd:
                            out[d] += hpd
                            available_hours[d] -= hpd
                            hours -= hpd
                        elif available_hours[d] >= 0.5:
                            out[d] += available_hours[d]
                            hours -= available_hours[d]
                            available_hours[d] = 0.0

                    else:
                        if available_hours[d] >= hours:
                            out[d] += hours
                            available_hours[d] -= hours
                            hours = 0.0
                        elif available_hours[d] >= 0.5:
                            out[d] += available_hours[d]
                            hours -= available_hours[d]
                            available_hours[d] = 0.0
                    # Go to next day
                    try:
                        d = av_days[av_days.index(d) + 1]
                        try:
                            rand_days.remove(d)
                        except ValueError:
                            pass
                    except IndexError:
                        try:
                            d = rand_days.pop()
                        except IndexError:
                            rand_days = random.sample(av_days, len(av_days))
                            d = rand_days.pop()

            else:
                # Random placing
                while hours > 0:
                    # Pop a random day
                    try:
                        d = rand_days.pop()
                        if hours > hpd + 0.5:
                            if available_hours[d] >= hpd:
                                out[d] += hpd
                                available_hours[d] -= hpd
                                hours -= hpd
                            elif available_hours[d] >= 0.5:
                                out[d] += available_hours[d]
                                hours -= available_hours[d]
                                available_hours[d] = 0.0

                        else:
                            if available_hours[d] >= hours:
                                out[d] += hours
                                available_hours[d] -= hours
                                hours = 0.0
                            elif available_hours[d] >= 0.5:
                                out[d] += available_hours[d]
                                hours -= available_hours[d]
                                available_hours[d] = 0.0
                    except IndexError:
                        av_days = []
                        for i in range(first_day - 1, last_day, 1):
                            if available_hours[i] > 0:
                                av_days.append(i)
                        rand_days = random.sample(av_days, len(av_days))
                        hpd = 0.5

    # Add mission tag
    out = [{'h': h, 'mission': False} for h in out]

    # Add missions if needed
    missions = (
        TimesheetMissionHint.objects
        .filter(reporting_period=period)
        .annotate(year=ExtractYear('missionday__day'), month=ExtractMonth('missionday__day'))
        .filter(year=year, month=month)
    )
    for m in missions:
        d = m.missionday.day.day
        out[d - 1]['h'] = m.missionday.ts_hours
        out[d - 1]['mission'] = True

    return (out, generate)


def LoadTimesheetData(rid, year, month):
    print("Loading timesheets for {0:d}/{1:d}".format(month, year))
    data = {}

    # Build days array, marking Saturdays and Sundays as holiday
    ndays = calendar.monthrange(year, month)[1]
    data['numdays'] = ndays     # Number of days in month
    data['days'] = []           # Array of data for each day
    data['absence_code'] = []   # Absence code for every day
    for d in range(1, ndays + 1, 1):
        day = {}
        day['n'] = d

        # Check Saturday and Sunday
        date = datetime.date(year=year, month=month, day=d)
        if date.weekday() > 4:
            day['holiday'] = True
        else:
            day['holiday'] = False

        # Append day
        data['days'].append(day)

        # Set absence code as public holiday if needed
        absence =  {'a': "", 'holiday': day['holiday']}
        if check_bank_holiday(date):
           absence['a'] = "PH"
        # Append absence
        data['absence_code'].append(absence)

    # Load presence data for the month
    presences = (
        PresenceData.objects
        .filter(
            Q(researcher=rid) &
            Q(day__gte=datetime.date(year, month, 1)) &
            Q(day__lte=datetime.date(year, month, ndays))
        )
        .order_by('day')
    )

    # Extract available hours for each day and absence code if available
    available_hours = [0.0 for i in range(ndays)]
    for p in presences:
        d = p.day.day
        # Set available hours
        if p.ts_code == EpasCode.NONE and p.ts_hours > 0:
            available_hours[d - 1] = p.ts_hours
        # Update absence code
        if p.ts_code == EpasCode.ILLNESS:
            data['absence_code'][d - 1]['a'] = 'SL'
        else:
            if data['absence_code'][d - 1]['a'] != 'PH':
                if p.ts_code == EpasCode.MISSION:
                    data['absence_code'][d - 1]['a'] = 'BT'
                elif p.ts_code == EpasCode.HOLIDAYS:
                    data['absence_code'][d - 1]['a'] = 'AH'
                elif p.ts_code == EpasCode.OTHER:
                    data['absence_code'][d - 1]['a'] = 'OA'

    # Get all reporting periods for the current researcher in the month
    rps = (
        Reporting.objects
        .filter(
            Q(researcher=rid) &
            Q(rp_start__lte=datetime.date(year, month, ndays)) &
            Q(rp_end__gte=datetime.date(year, month, 1))
        )
        .order_by('project__name', 'wp__name')
    )

    # Group all reporting periods by project
    projects = {}
    for p in rps:
        pid = p.project.pk
        if p.wp is None:
            # Project without WPs
            if pid not in projects:
                projects[pid] = {}
                projects[pid]['has_wp'] = False
                projects[pid]['period'] = [p, ]   # NB: this is a list to handle multiple project periods in the same month
            else:
                projects[pid]['period'].append(p)
        else:
            # Project with WPs
            if pid not in projects:
                projects[pid] = {}
                projects[pid]['has_wp'] = True
                projects[pid]['wps'] = []
            projects[pid]['wps'].append(p)

    # Cycle over periods, load hints and split hours over days
    data['projects'] = []
    for pk, p in projects.items():

        new_p = {}

        if p['has_wp']:
            # Project with WPs
            new_p['has_wps'] = True
            # Project name and reference
            new_p['name'] = p['wps'][0].project.name
            new_p['ref'] = p['wps'][0].project.reference
            # PI ID
            new_p['pi_id'] = p['wps'][0].project.pi
            # Cycle over work packages
            new_p['wps'] = []
            for wp in p['wps']:

               # First we need to check if the WP ID is already present
               old_wp = -1
               for i, pwp in enumerate(new_p['wps']):
                   if pwp['id'] == wp.wp.pk:
                       old_wp = i
                       break

               # Split hours over days  NB: available_hours is updated during the split!
               wp_days = LoadHoursOverDays(wp, year, month, available_hours)

               if old_wp == -1:
                   # WP is new
                   new_wp = {}
                   # WP name and description
                   new_wp['name'] = wp.wp.name
                   new_wp['desc'] = wp.wp.desc
                   # WP ID to check for duplicates
                   new_wp['id'] = wp.wp.pk
                   # Set by default as 'not the last'
                   new_wp['last'] = False
                   # Set days
                   new_wp['days'] = wp_days
                   # Append WP
                   new_p['wps'].append(new_wp)

               else:
                   # WP already present. We add hours by day
                   for d in range(len(wp_days)):
                       new_p['wps'][old_wp]['days'][d]['h'] += wp_days[d]['h']

               # Sum up hours
               new_p['wps'][old_wp]['total'] = 0
               for d in new_p['wps'][old_wp]['days']:
                   new_p['wps'][old_wp]['total'] += d['h']

            # Set last WP as last
            new_p['wps'][-1]['last'] = True

            # Sum hours for all WPs for the project totals
            new_p['days'] = [{'h': 0.0, 'mission': False} for i in range(ndays)]  # Will be the sum of all the WPs
            # Cycle over wps and sum
            for wp in new_p['wps']:
                for i in range(ndays):
                    new_p['days'][i]['h'] += wp['days'][i]['h']
            # Total hours of the project
            new_p['total'] = 0.0
            for d in new_p['days']:
                new_p['total'] += d['h']

        else:
            # Project without WPs
            new_p['has_wps'] = False
            # Project name
            new_p['name'] = p['period'][0].project.name
            # PI
            new_p['pi_id'] = p['period'][0].project.pi
            # Project reference
            new_p['ref'] = p['period'][0].project.reference
            new_p['id'] = p['period'][0].pk
            # Split hours over days  NB: available_hours is updated during the split!
            new_p['days'] = LoadHoursOverDays(p['period'][0], year, month, available_hours)
            for period in p['period'][1:]:
                hpd = LoadHoursOverDays(period, year, month, available_hours)
                for i, d in enumerate(hpd):
                    new_p['days'][i]['h'] += d['h']
            new_p['total'] = 0.0
            for d in new_p['days']:
                new_p['total'] += d['h']

        # Add project
        data['projects'].append(new_p)

    # Add internal activities
    internal = {
        'name': 'Internal activities',
        'ref': '',
        'id': -1,
        'has_wps': False,
        'days': [{'h': available_hours[i], 'mission': False} for i in range(len(available_hours))],
        'total': sum(available_hours),
    }
    # Get all missions reported in the month by the researcher
    reported_missions = (
        TimesheetMissionHint.objects
        .filter(Q(reporting_period__researcher=rid))
        .annotate(year=ExtractYear('missionday__day'), month=ExtractMonth('missionday__day'))
        .filter(year=year, month=month)
        .order_by()
    )

    q = Q()
    if reported_missions.count():
        for rpm in reported_missions:
            q |= Q(day=rpm.missionday.day)

    # Get missions not assigned to any period
    missions = (
        PresenceData.objects
        .filter(researcher=rid)
        .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
        .filter(
            Q(year=year) &
            Q(month=month) &
            Q(ts_code=EpasCode.MISSION) &
            Q(ts_hours__gt=0) &
            ~q
        )
        .order_by()
    )

    # Add missions to interal activities
    if missions.count():
        for m in missions:
            internal['days'][m.missionday.day.day - 1]['h'] = m.missionday.hours
            internal['days'][m.missionday.day.day - 1]['mission'] = True

    # Add internal activities as a project
    data['projects'].append(internal)

    # Extend holiday tag and sum hours for each day
    data['day_total'] = [{'h': 0.0, 'holiday': data['days'][i]['holiday']} for i in range(ndays)]
    for p in data['projects']:
        if p['has_wps']:
            for wp in p['wps']:
                for i in range(len(wp['days'])):
                    wp['days'][i]['holiday'] = data['days'][i]['holiday']
                    data['day_total'][i]['h'] += wp['days'][i]['h']
        for i in range(len(p['days'])):
            p['days'][i]['holiday'] = data['days'][i]['holiday']
            if not p['has_wps']:
                data['day_total'][i]['h'] += p['days'][i]['h']

    data['grand_total'] = 0.0
    for d in data['day_total']:
        data['grand_total'] += d['h']

    # Search for a proper signature day
    sign_day = (
        PresenceData.objects
        .filter(
            Q(researcher=rid) &
            Q(day__gt=datetime.date(year, month, ndays)) &
            (Q(code=None) | Q(code__ts_code=EpasCode.NONE)) &
            Q(hours__gt=0)
        )
        .order_by('day')
        .first()
    )
    data['sign_day'] = sign_day.day

    return data


def LoadHoursOverDays(period, year, month, available_hours):
    # Days in the month
    ndays = calendar.monthrange(year, month)[1]

    # Output array
    out = [0.0 for i in range(ndays)]

    # First get the hint
    try:
        hint = TimesheetHint.objects.get(reporting_period=period.pk, year=year, month=month)
        hours = hint.hours
    except TimesheetHint.DoesNotExist:
        raise ValueError("Period {0!s} has no hint!".format(period))

    # Load saved hours per day
    saved_ts = (
        TimesheetHours.objects
        .filter(reporting_period=period.pk)
        .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
        .filter(year=year, month=month)
        .order_by()
    )

    if saved_ts.count() > 0:
        # Sum hours in saved timesheet
        saved_hours = 0.0
        for obj in saved_ts:
            saved_hours += obj.hours

        if saved_hours == hours:
            # We alread have all the hours we need
            for obj in saved_ts:
                out[obj.day.day - 1] = obj.hours
                available_hours[obj.day.day - 1] -= obj.hours

        else:
            # Hints are changed. We have to re-generate timesheet again
            raise ValueError("Saved hours do not match hours in month hint. Please generate the timesheet again")

    else:
        if hours:
            # Hints are changed. We have to re-generate timesheet again
            raise ValueError("No saved data found. Please generate the timesheet first.")

    # Add missions
    out = [{'h': h, 'mission': False} for h in out]

    # Add missions if needed
    missions = (
        TimesheetMissionHint.objects
        .filter(reporting_period=period)
        .annotate(year=ExtractYear('missionday__day'), month=ExtractMonth('missionday__day'))
        .filter(year=year, month=month)
    )
    for m in missions:
        d = m.missionday.day.day
        out[d - 1]['h'] = m.missionday.ts_hours
        out[d - 1]['mission'] = True

    return out


def CheckTimesheetData(rid, year, month):
    print("Checking timesheets data for {0:d}/{1:d}".format(month, year))

    # Number of days in month
    ndays = calendar.monthrange(year, month)[1]

    # Get all reporting periods for the current researcher in the month
    rps = (
        Reporting.objects
        .filter(
            Q(researcher=rid) &
            Q(rp_start__lte=datetime.date(year, month, ndays)) &
            Q(rp_end__gte=datetime.date(year, month, 1))
        )
        .order_by()
    )

    # For each period check that we have a hint, and that the hint hours corresponds to Timesheet hours
    for period in rps:

        # Check hints
        try:
            hint = TimesheetHint.objects.get(reporting_period=period.pk, year=year, month=month)
            hours = hint.hours
        except TimesheetHint.DoesNotExist:
            print("Error: No hints")
            return False

        ts_hours = (
            TimesheetHours.objects
            .filter(reporting_period=period.pk)
            .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
            .filter(year=year, month=month)
            .aggregate(ts_hours=Coalesce(Sum('hours'), 0.0))
        )
        ts_hours = ts_hours['ts_hours']

        # Sum reported missions
        # ms_hours = (
        #     TimesheetMissionHint.objects
        #     .filter(reporting_period=period.pk)
        #     .annotate(year=ExtractYear('missionday__day'), month=ExtractMonth('missionday__day'))
        #     .filter(year=year, month=month)
        #     .aggregate(mission_h=Coalesce(Sum('missionday__hours'), 0.0))
        # )['mission_h']

        if ts_hours != hours:
            print("Error: No ts hours or hints does not match")
            return False

    # Check that reported hours per day does not exceed TS hours per day
    q = (
        TimesheetHours.objects
        .filter(reporting_period__researcher=14)
        .annotate(year=ExtractYear('day'), month=ExtractMonth('day'))
        .filter(year=year, month=month)
        .values('day')
        .annotate(rep_h=Sum('hours'))
        .annotate(
            tot_h=Subquery(
                PresenceData.objects
                .filter(researcher=14, day=OuterRef('day'))
                .values('ts_hours')[:1]
            )
        )
        .filter(rep_h__gt=F('tot_h'))
        .order_by('day')
    )

    if len(q):
        print("Error: reported does not match worked hours")
        return False

    # All tests passed
    return True
