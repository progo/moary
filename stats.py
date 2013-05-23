""" Statistics """

from itertools import islice, groupby
from collections import defaultdict
import datetime

import data
from entry import Entry

WEEKDAY_STR = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

def activity_calendar(args, formatter='text', span=None):
    """Build a github-like activity calendar for the last `span` days.
    Positional argument `formatter` determines the driver used,
    defaulting to text. """

    formatter = 'html' if args.html else 'text'

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

    print FORMATTERS[formatter](watcheddict)

### FORMATTERS
## Take the dict of {date: count} and return string outputs for
## files/stdout.


### Formatter helpers

def get_date_interval(start_date, end_date=None):
    """Get two date objects, return a list of dates in between. Rounds
    in full weeks."""

    # round up to full weeks
    start_date += datetime.timedelta(days=-start_date.weekday())

    end_date = end_date or datetime.date.today()
    end_date += datetime.timedelta(days=(6-end_date.weekday()))

    dateint = []
    while start_date <= end_date:
        dateint.append(start_date)
        start_date += datetime.timedelta(days=1)
    
    return dateint

def get_weekstarts(date_interval):
    """Collect beginning date of each week in separate list. We do
    assume that the list begins with your begin date of choice."""
    return [d for d in islice(date_interval, 0, None, 7)]

def actcal_text(watched):
    """Format activity calendar in text."""

    dateint = get_date_interval(start_date=sorted(watched.keys())[0])
    weekstarts = get_weekstarts(dateint)

    monthline = ' '.join(d.strftime("%b") for d in weekstarts)
    result = []
    result.append(" " * 4 + "| " + monthline)
    result.append(" " * 4 + "| "
                  + ' '.join('{0:<3}'.format(ws.day) for ws in weekstarts))
    result.append('=' * (len(monthline) + 6))

    for weekday in range(0, 7):
        row = '{0} | '.format(WEEKDAY_STR[weekday])
        for d in islice(dateint, weekday, None, 7):
            row += '{0}   '.format(watched[d])
        result.append(row)

    return '\n'.join(result)

def actcal_html(watched):
    """Format activity calendar in HTML."""
    return "HTML"

FORMATTERS = {'text': actcal_text,
              'html': actcal_html}
