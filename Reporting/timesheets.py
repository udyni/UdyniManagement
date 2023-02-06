import datetime
import calendar
import random

from django.db.models import Q, F, Sum, Value
from django.db.models.functions import ExtractYear, ExtractMonth, Coalesce
from .models import EpasCode, PresenceData, ReportedWork, ReportedMission, TimesheetHours
from .utils import check_bank_holiday, get_workpackages_fractions
from .utils import ReportingError


# Structure of TS data for display/printing
#
# ts = {
#   'numdays': n         # Number of days in month
#   'days': [            # Array of data for each day
#       {
#           'n': n,
#           'holiday': True/False
#       },
#       ...
#   ],
#   'absence_code': [   # Absence code for every day
#       {
#           'a': code,
#           'holiday': True/False
#       },
#       ...
#   ],
#   'projects': [
#       {
#           'has_wps': True,
#           'name':,
#           'refe':,
#           'wps': [
#               {
#                   'name': wp name
#                   'desc': wp desc
#                   'id':   wp pk   ???
#                   'days': [
#                        {
#                            'h': hours,
#                            'mission': True/False,
#                            'holiday': True/False,
#                        },
#                        ...
#                   ]
#                   'total': sum
#                   'last': False
#               },
#               ...
#               {
#                   'name': wp name
#                   'desc': wp desc
#                   'id':   wp pk   ???
#                   'days': [
#                       {
#                           'h': hours,
#                           'mission': True/False,
#                           'holiday': True/False,
#                       },
#                       ...
#                   ]
#                   'total': sum
#                   'last': True
#               },
#           ],
#           'days': [
#               {
#                   'h': hours,
#                   'mission': True/False,
#                   'holiday': True/False,
#               },
#               ...
#           ],
#           '':,
#
#       },
#       {
#
#       },
#       ...
#       NOTE: last project is 'internal activities' with all the left hours and missions
#   ],
#   'day_total': [
#       {
#           'h': hours,
#           'holiday': True/False,
#       },
#   ],
#   'grand_total': total hours
# }


def round2first(value):
    """ Round the number to the first decimal digit (used to remove rounding errors in sums)
    """
    return round(value * 10.0) / 10.0


def CheckTimesheetData(rid, year, month):
    """ Check that the TS data is consistent with the reported work.
    Return True if it is, False otherwise
    """

    # Get reported work
    work = (
        ReportedWork.objects
        .filter(
            researcher=rid,
            year=year,
            month=month,
        )
        .order_by(
            'period__project__name',
            'period__rp_start',
        )
    )

    # Get timesheet hours summary
    ts_data_summary = (
        TimesheetHours.objects
        .annotate(
            year=ExtractYear('day'),
            month=ExtractMonth('day')
        )
        .filter(
            Q(report__researcher=rid) &
            Q(year=year) &
            Q(month=month)
        )
        .order_by(
            'report__period__project__name',
            'report__period__rp_start',
            'report_wp__workpackage__name',
            'day',
        )
        .values('report', 'report_wp')
        .annotate(total_hours=Coalesce(Sum('hours'), Value(0.0)))
        .order_by()
    )

    # Check that TS hours match reported work
    for w in work:
        # Get WPs
        wps = get_workpackages_fractions(w)
        f = filter(lambda x: x['report'] == w.pk, ts_data_summary)
        if wps:
            # Splitted on WPs
            for wp in wps:
                for ts in f:
                    if ts['report_wp'] == wp['pk']:
                        if abs(w.hours * wp['fraction'] - ts['total_hours']) > 0.01:
                            print("TS hours does not match report. Project: {0:s}, Workpackage: {1:s} ({2:.1f} != {3:.1f})".format(w.period.project.name, wp['wp'], w.hours * wp['fraction'], ts['total_hours']))
                            # Failed!
                            return False
                        break
        else:
            # No workpackages
            try:
                # No workpackages
                ts = next(f)
                if ts['total_hours'] != w.hours:
                    return False
            except StopIteration:
                return False

    # Everything matched!
    return True


def GetTimesheetData(rid, year, month, generate=False):
    """ Get timesheet data for the given researcher, year, month
    Return a tuple: the first element is a boolean indicating if there was a modification
    since last save, the second is the updated timesheet data
    Raise ReportingError on error
    """

    # If we are not generating and the data is not consistent return
    consistent = CheckTimesheetData(rid, year, month)
    if not consistent and not generate:
        raise ReportingError("Timesheet data for RID {0:d} for month {1:d}/{2:d} is not consistent".format(rid, year, month))

    # Get reported work
    work = (
        ReportedWork.objects
        .filter(
            researcher=rid,
            year=year,
            month=month,
        )
        .order_by(
            'period__project__name',
            'period__rp_start',
        )
    )

    # Get timesheet hours
    ts_data = (
        TimesheetHours.objects
        .annotate(
            year=ExtractYear('day'),
            month=ExtractMonth('day'),
            project_name=F('report__period__project__name'),
            workpackage_name=F('report_wp__workpackage__name'),
        )
        .filter(
            Q(report__researcher=rid) &
            Q(year=year) &
            Q(month=month)
        )
        .order_by(
            'report__period__project__name',
            'report__period__rp_start',
            'report_wp__workpackage__name',
            'day',
        )
    )

    # Get presences
    presences = (
        PresenceData.objects
        .filter(researcher=rid)
        .annotate(
            year=ExtractYear('day'),
            month=ExtractMonth('day'),
        )
        .filter(
            Q(year=year) &
            Q(month=month)
        )
        .order_by('day')
    )

    # Initialize data
    data = {}
    ndays = calendar.monthrange(year, month)[1]
    data['numdays'] = ndays
    data['days'] = []
    data['absence_code'] = []
    data['projects'] = []
    data['day_total'] = []
    data['grand_total'] = 0.0
    data['modified'] = 0

    # Setup days and holiday tag
    for d in range(1, ndays + 1, 1):
        date = datetime.date(year=year, month=month, day=d)

        we = False
        # Check Saturday and Sunday
        if date.weekday() > 4:
            we = True

        # Check bank holiday
        bh = False
        if check_bank_holiday(date):
            bh = True

        # Append day
        data['days'].append({'n': d, 'holiday': we | bh, 'mission': False})

        # Append absence code
        data['absence_code'].append({'a': "PH" if bh else "", 'holiday': we | bh})

        # Append day total
        data['day_total'].append({'h': 0.0, 'mission': False, 'holiday': we | bh})

    # Process presences
    available_hours = [0.0 for i in range(ndays)]
    for p in presences:
        # Day index
        d = p.day.day - 1

        # Store hours (only for working days)
        if p.hours > 0 and p.ts_code is None or p.ts_code == EpasCode.NONE:
            h = round2first(p.hours)
            data['day_total'][d]['h'] = h
            available_hours[d] = h

        # Set mission flag
        if p.ts_code == EpasCode.MISSION:
            data['days'][d]['mission'] = True
            data['day_total'][d]['mission'] = True

        # Store absence code
        if p.ts_code == EpasCode.ILLNESS:
            data['absence_code'][d]['a'] = "IL"
        elif data['absence_code'][d]['a'] != "PH":
            if p.ts_code == EpasCode.MISSION:
                data['absence_code'][d]['a'] = "BT"
            elif p.ts_code == EpasCode.HOLIDAYS:
                data['absence_code'][d]['a'] = "AH"

    # Add projects
    p_names = []
    for w in work:
        name = w.period.project.name
        if name not in p_names:
            # First time we got the project. Create new.
            p_names.append(name)

            new_p = {}
            new_p['id'] = w.period.project.pk           # Project ID
            new_p['name'] = name                        # Project name
            new_p['ref'] = w.period.project.reference   # Project reference
            new_p['pi_id'] = w.period.project.pi.pk if w.period.project.pi is not None else None    # Project PI
            data['projects'].append(new_p)

        else:
            # Project already created. We get it from the list
            new_p = data['projects'][p_names.index(name)]

        # Get report workpackages
        wps = get_workpackages_fractions(w)
        if len(wps):
            new_p['has_wps'] = True   # Period has split over WP
            new_p['wps'] = []
            for wp in wps:           # Cycle over WPs
                # Filter already saved TS data
                ts = ts_data.filter(project_name=name, workpackage_name=wp['wp'])

                # Get the hours split over days
                modified, wp_days = GetHoursOverDays(w.period, w.hours * wp['fraction'], ts, year, month, available_hours)  # NB: available_hours is updated!
                if modified:
                    print("Modification detected in project {0:s}, workpackage {1:s}".format(name, wp['wp']))
                    data['modified'] = 1

                # First check if we already have the WP
                for new_wp in new_p['wps']:
                    if new_wp['id'] == wp['wp_pk']:
                        # Alread present
                        for i, d in enumerate(wp_days):
                            new_wp['days'][i]['h'] += d['h']
                        # Update WP total
                        new_wp['total'] += sum(wp_days)
                        break
                else:
                    # New workpackage
                    new_wp = {}
                    new_wp['id'] = wp['wp_pk']   # WP ID to check for duplicates
                    new_wp['name'] = wp['wp']    # WP name
                    new_wp['desc'] = wp['desc']  # WP description
                    new_wp['days'] = [{'h': d, 'mission': data['days'][i]['mission'], 'holiday': data['days'][i]['holiday']} for i, d in enumerate(wp_days)]
                    new_wp['last'] = False       # Set by default as 'not the last'
                    new_wp['total'] = sum(wp_days)
                    new_p['wps'].append(new_wp)  # Append WP

            new_p['days'] = [{'h': 0.0, 'mission': data['days'][i]['mission'], 'holiday': data['days'][i]['holiday']} for i in range(ndays)]
            # Sum data on wps
            new_p['total'] = 0.0
            for wp in new_p['wps']:
                for i in range(ndays):
                    new_p['days'][i]['h'] += wp['days'][i]['h']
                    new_p['total'] += wp['days'][i]['h']

        else:
            # Project has no WP
            new_p['has_wps'] = False

            # Filter already saved TS data
            ts = ts_data.filter(project_name=name, workpackage_name=None)

            # Split hours over days
            modified, p_days = GetHoursOverDays(w.period, w.hours, ts, year, month, available_hours)

            if 'days' not in new_p:
                new_p['days'] = [{'h':d , 'mission': data['days'][i]['mission'], 'holiday': data['days'][i]['holiday']} for i, d in enumerate(p_days)]
                new_p['total'] = sum(p_days)
            else:
                for i, d in enumerate(p_days):
                    new_p['days'][i]['h'] += d['h']
                new_p['total'] += sum(p_days)

    # Tag last WP in all projects
    for prj in data['projects']:
        if 'wps' in prj:
            # Tag last WP
            prj['wps'][-1]['last'] = True

    # Add reported missions
    rep_m = (
        ReportedMission.objects
        .filter(Q(day__researcher=rid))
        .annotate(
            year=ExtractYear('day__day'),
            month=ExtractMonth('day__day')
        )
        .filter(year=year, month=month)
        .order_by(
            'period__project__name',
            'period__rp_start',
            'day__day',
        )
    )

    q = Q()
    for m in rep_m:
        # Add day to query
        q |= Q(day=m.day.day)
        pname = m.period.project.name
        if pname not in p_names:
            # Project has only missions. We have to add it
            new_p = {}
            new_p['id'] = m.period.project.pk           # Project ID
            new_p['name'] = pname                       # Project name
            new_p['ref'] = m.period.project.reference   # Project reference
            new_p['pi_id'] = m.period.project.pi.pk if m.period.project.pi is not None else None     # Project PI
            if m.period.project.workpackage_set.all().count() > 0:
                new_p['has_wps'] = True   # Project has WPs
                new_p['wps'] = []
            else:
                new_p['has_wps'] = False
            new_p['days'] = [{'h': 0.0, 'mission': data['days'][i]['mission'], 'holiday': data['days'][i]['holiday']} for i in range(ndays)]
            new_p['total'] = 0.0

            # Insert project in the right place
            if len(p_names):
                for i, p in enumerate(p_names):
                    if pname > p:
                        continue
                    else:
                        p_names.insert(i, pname)
                        data['projects'].insert(i, new_p)
                        break
                else:
                    p_names.append(pname)
                    data['projects'].append(new_p)
            else:
                p_names.append(pname)
                data['projects'].append(new_p)

        if m.workpackage is not None:
            wid = m.workpackage.pk
            for wp in data['projects'][p_names.index(pname)]['wps']:
                if wp['id'] == wid:
                    break
            else:
                # WP not found! There are no hours reported on this WP, we have to add it
                wp = {}
                wp['id'] = wid                   # WP ID to check for duplicates
                wp['name'] = m.workpackage.name  # WP name
                wp['desc'] = m.workpackage.desc  # WP description
                wp['days'] = [{'h': 0.0, 'mission': data['days'][i]['mission'], 'holiday': data['days'][i]['holiday']} for i in range(ndays)]
                wp['last'] = False       # Set by default as 'not the last'
                wp['total'] = 0.0

                # Insert WP in the right place
                if len(data['projects'][p_names.index(pname)]['wps']):
                    for i, old_wp in enumerate(data['projects'][p_names.index(pname)]['wps']):
                        if wp['name'] > old_wp['name']:
                            continue
                        else:
                            data['projects'][p_names.index(pname)]['wps'].insert(i, wp)
                            break
                    else:
                        data['projects'][p_names.index(pname)]['wps'].append(wp)
                else:
                    data['projects'][p_names.index(pname)]['wps'].append(wp)

            # Add mission to WP
            wp['days'][m.day.day.day - 1]['h'] = m.day.hours
            # Update WP total
            wp['total'] += m.day.hours
            # Update project day
            data['projects'][p_names.index(pname)]['days'][m.day.day.day - 1]['h'] = m.day.hours
            # Update project total
            data['projects'][p_names.index(pname)]['total'] += m.day.hours
            # Update day total
            data['day_total'][m.day.day.day - 1]['h'] += m.day.hours

        else:
            # Add mission to project
            data['projects'][p_names.index(pname)]['days'][m.day.day.day - 1]['h'] = m.day.hours
            data['projects'][p_names.index(pname)]['total'] += m.day.hours

    # Add internal activities
    internal = {
        'name': 'Internal activities',
        'ref': '',
        'id': -1,
        'has_wps': False,
        'days': [{'h': round2first(d), 'mission': data['days'][i]['mission'], 'holiday': data['days'][i]['holiday']} for i, d in enumerate(available_hours)],
        'total': sum(available_hours),
        'generated': 0,
    }

    # Add missions not assigned to any period
    missions = presences.filter(Q(ts_code=EpasCode.MISSION) & Q(hours__gt=0) & ~q).order_by('day')
    for m in missions:
        # Add mission
        internal['days'][m.day.day - 1]['h'] = m.hours
        # Update internal activities total
        internal['total'] += m.hours
        # Update day total
        data['day_total'][m.day.day - 1]['h'] += m.hours

    # Add internal activities as last project
    data['projects'].append(internal)

    # Round all sums
    for prj in data['projects']:
        if prj['has_wps']:
            for wp in prj['wps']:
                wp['total'] = round2first(wp['total'])
        prj['total'] = round2first(prj['total'])

    # Compute grand total
    for d in data['day_total']:
        data['grand_total'] += d['h']
    data['grand_total'] = round2first(data['grand_total'])

    return data


def GetHoursOverDays(period, hours, ts, year, month, available_hours):

    # Round hours to avoid errors due to fractions...
    hours = round2first(hours)

    # Check if project is HorizonEU
    horizon = (period.project.agency == "EU-HorizonEu")

    # Days in the month
    ndays = calendar.monthrange(year, month)[1]

    # Check which days of the month are in the reporting period
    if period.rp_start < datetime.date(year, month, 1):
        first_day = 1
    else:
        first_day = period.rp_start.day
    if period.rp_end > datetime.date(year, month, ndays):
        last_day = ndays
    else:
        last_day = period.rp_end.day

    # Initialize days
    days = [0.0 for d in range(ndays)]

    # Start adding saved hours if any
    for d in ts:
        # Add hours
        days[d.day.day-1] = d.hours
        # Subtract from available hours
        available_hours[d.day.day-1] -= d.hours
        # Subtract from hours
        hours -= d.hours

    if abs(hours) < 0.001:
        # Not modified, so we can return
        # NOTE: if the saved hours match the total hours but are more that the available hours
        # we will leave the hours negative. This happens when another period is updated with more
        # hours after first generation. This will require manual correction.
        return (False, days)

    else:
        print(hours)
        # We handle Horizon EU projects separately to enforce the half day minimum reporting quantum
        if horizon:
            # Horizon EU project. We work in half days
            half_days = hours / 3.6   # Number of half days
            if abs(half_days - round(half_days)) > 0.0:
                # On horizon EU minimum quantum of reporting is half day, i.e. 3.6 hours
                raise ReportingError("Project {0:s} is horizon EU but reported hours are not multiple of a half-day".format(period.project.name))
            half_days = round(half_days)

            if half_days < 0:
                # We have set more hours than needed. We need to remove hours.
                while half_days < 0:
                    av_days = []
                    try:
                        # Get day
                        i = av_days.pop()
                        assert(days[i] > 0 and abs(days[i] / 3.6 - round(days[i] / 3.6)) < 0.01)
                        days[i] -= 3.6
                        half_days += 1
                        available_hours[i] += 3.6

                    except IndexError:
                        # We need to restore the day list
                        av_days = [i for i, d in enumerate(days) if d > 0 and i+1 >= first_day and i+1 <= last_day]
                        random.shuffle(av_days)
                        assert(len(av_days))

            else:
                # We have set less hours than needed. We need to add hours.
                while half_days > 0:
                    av_days = []
                    try:
                        # Get day
                        i = av_days.pop()
                        assert(available_hours[i] > 0 and abs(available_hours[i] / 3.6 - round(available_hours[i] / 3.6)) < 0.01)
                        days[i] += 3.6
                        half_days -= 1
                        available_hours[i] -= 3.6

                    except IndexError:
                        # We need to restore the day list
                        av_days = [i for i, d in enumerate(available_hours) if d >= 3.6 and i+1 >= first_day and i+1 <= last_day]
                        random.shuffle(av_days)
                        assert(len(av_days))
        else:
            # Not horizon
            if hours < 0:
                # We have set more hours than needed. We need to remove hours.
                av_days = [i for i, d in enumerate(days) if d > 0 and i+1 >= first_day and i+1 <= last_day]
                for i in av_days:
                    # Check every days to remove spare hours to free half days
                    if days[i] < 2.0 and days[i] < abs(hours):
                        available_hours[i] += days[i]
                        hours += days[i]
                        days[i] = 0

                    elif days[i] - (3.6 - available_hours[i] % 3.6) > 1.0:
                        h = round2first(3.6 - available_hours[i] % 3.6)  # Just to be sure not to have rounding errors...
                        if h > abs(hours):
                            h = abs(hours)
                        available_hours[i] += h
                        days[i] -= h
                        hours += h

                    if hours == 0:
                        break

                else:
                    # We still have some hours to fix
                    av_days = []
                    while hours < 0:
                        try:
                            i = av_days.pop()
                            if abs(hours) < days[i] and days[i] - abs(hours) > 1.0:
                                days[i] -= abs(hours)
                                available_hours[i] += abs(hours)
                                hours = 0

                            elif abs(hours) > days[i]:
                                available_hours[i] += days[i]
                                hours += days[i]
                                days[i] = 0

                        except IndexError:
                            av_days = [i for i, d in enumerate(days) if d > 0]
                            random.shuffle(av_days)
                            assert(len(av_days))

            else:
                # We have set less hours than needed. We need to add hours.
                av_days = []
                while hours < 0:
                    try:
                        i = av_days.pop()
                        if available_hours[i] <= 3.6 and available_hours[i] > 1.0:
                            # We have less than half a day but more that 1.0h
                            if hours >= available_hours[i]:
                                if hours - available_hours[i] >= 1.0:
                                    # More than 1h left
                                    days[i] += available_hours[i]
                                    hours -= available_hours[i]
                                    available_hours[i] = 0
                                else:
                                    # Less than 1h left. Not good!
                                    if available_hours[i] > 2.0:
                                        h = available_hours[i] - 1.0
                                        days[i] += h
                                        hours -= h
                                        available_hours[i] -= h
                                    else:
                                        # No solution. We need to look for another day
                                        pass
                            else:
                                days[i] += hours
                                available_hours[i] -= hours
                                hours = 0

                        elif available_hours[i] > 3.6 and available_hours < 7.2:
                            h = available_hours[i] - 3.6
                            if h < 2.0:  # We need at least two hours or we get the full amount
                                h = available_hours[i]

                            if hours >= h:
                                if hours - h >= 1.0:
                                    # More that 1h left
                                    days[i] += h
                                    available_hours[i] -= h
                                    hours -= h

                                else:
                                    # Less than 1h left. Not good!
                                    if available_hours[i] > 2.0:
                                        h -= 1.0 # Remove one hour...
                                        days[i] += h
                                        hours -= h
                                        available_hours[i] -= h

                                    else:
                                        # No solution. We need to look for another day
                                        pass

                            else:
                                days[i] += hours
                                available_hours[i] -= hours
                                hours = 0

                        elif available_hours[i] >= 7.2:
                            if hours > 3.6:
                                days[i] += 3.6
                                hours -= 3.6
                                available_hours[i] -= 3.6
                            else:
                                h = available_hours[i] - 3.6
                                days[i] += h
                                hours -= h

                    except IndexError:
                        av_days = [i for i, d in enumerate(available_hours) if d > 0 and i+1 >= first_day and i+1 <= last_day]
                        random.shuffle(av_days)
                        assert(len(av_days))

        return (True, days)
