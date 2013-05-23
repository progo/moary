""" Statistics """

from itertools import islice, groupby
from collections import defaultdict
import datetime

import data
from entry import Entry

WEEKDAY_STR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

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
    for date, count in watched:
        d = date.date()
        watcheddict[d] = count

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

    # Collect beginning of each week in separate list
    weekstarts = [d for d in islice(dateint, 0, None, 7)]

    monthline = ' '.join(d.strftime("%b") for d in weekstarts)
    print " " * 4 + "|",
    print monthline
    print " " * 4 + "|",
    print ' '.join('{0:<3}'.format(ws.day) for ws in weekstarts)
    print '=' * (len(monthline) + 6)

    for weekday in range(0, 7):
        print '{0} |'.format(WEEKDAY_STR[weekday]),
        for d in islice(dateint, weekday, None, 7):
            print '{0}  '.format(watcheddict[d]),
        print
