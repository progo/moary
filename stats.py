""" Statistics """

from itertools import islice, groupby
from collections import defaultdict
import datetime

import data
from entry import Entry

def activity_calendar(args, span=None):
    """Build a github-like activity calendar for the last `span` days."""

    span = span or args.days or 365
    day_modifier = '-{0} days'.format(span)

    db = data.DataFacilities(dbfile=args.db_file)

    watched = db.query("SELECT origdate, count(movie) FROM movies "
                       + "WHERE origdate >= date('now', ?) "
                       + "GROUP BY date(origdate) "
                       + "ORDER BY origdate ASC "
                       , (day_modifier,))

    watcheddict = defaultdict(lambda: 0)
    gh_array = {}
    for date, count in watched:
        d = date.date()
        watcheddict[d] = count

        # keys are (week number, week day)
        key = (d.isocalendar()[1], d.isoweekday())
        gh_array[key] = {'count': count,
                         'date': d}

    # round up to full weeks
    start_date = watched[0][0].date()
    start_date += datetime.timedelta(days=-start_date.weekday())
    end_date = datetime.date.today()
    end_date += datetime.timedelta(days=(6-end_date.weekday()))

    # print 'Starting', start_date.strftime("%A %F")
    # print 'Finishing', end_date.strftime("%A %F")

    dateint = []
    while start_date <= end_date:
        dateint.append(start_date)
        start_date += datetime.timedelta(days=1)

    WEEKDAY_STR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # check the months appearing in the date interval above
    months = [d.strftime("%b") for d in islice(dateint, 0, None, 7)]

    # and why not the start dates as well
    weekstarts = [d.day for d in islice(dateint, 0, None, 7)]

    print " " * 4 + "|",
    print ' '.join(months)
    print " " * 4 + "|",
    print ' '.join('{0:<3}'.format(ws) for ws in weekstarts)
    print '=' * (len(' '.join(months)) + 6)

    for weekday in range(0, 7):
        print '{0} |'.format(WEEKDAY_STR[weekday]),
        for d in islice(dateint, weekday, None, 7):
            print '{0}  '.format(watcheddict[d]),
        print
