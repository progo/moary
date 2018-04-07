""" Statistics """

from itertools import islice, groupby
from collections import defaultdict
import tempfile
import subprocess
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

    text = FORMATTERS[formatter](watcheddict)

    if args.open:
        with tempfile.NamedTemporaryFile(suffix='.html') as tf:
            # At least Firefox in linux will not throw the page away
            # even when the tempfile under it is removed quite
            # immediately.
            tf.write(text)
            tf.flush()
            subprocess.call(["xdg-open", tf.name])
    else:
        print(text)

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


def draw_view_graph(watched):
    """Draw and return an SVG code snippet of views cumulating over time."""
    try:
        import pygal
    except ImportError:
        return "ERROR: pygal not installed"

    chart = pygal.Line(width=600, height=400,
                       disable_xml_declaration=True,
                       style=pygal.style.LightStyle)

    chart.title = 'Views over time'
    chart.show_legend = False
    chart.show_dots = False

    wsorted = sorted(watched.keys())

    cumsum = [(wsorted[0], watched[wsorted[0]])]
    for key in wsorted[1:]:
        lastval = cumsum[-1][1]
        cumsum.append((key, lastval + watched[key]))

    xlabels = [''] * len(cumsum)
    for ind in range(0, len(cumsum), 7):
        xlabels[ind] = cumsum[ind][0].strftime("%a %b %Y")

    chart.x_labels = xlabels
    chart.x_label_rotation = 45
    chart.add('View count', [s[1] for s in cumsum])

    return "<figure style='width: 800px;'>{0}</figure>".format(chart.render())

def actcal_html(watched):
    """Format activity calendar in HTML. Also include a SVG graph of
    views cumulating."""
    dateint = get_date_interval(start_date=sorted(watched.keys())[0])
    weekstarts = get_weekstarts(dateint)

    result = [
        '<html>',
        '<head>',
        '<style> table { border: 0; }',
        'td { border-right: dashed thin black; padding: 2px; }',
        'td.one { background-color: #BDFFB7; }',
        'td.good { background-color: #80FF75; }',
        'td.lots { background-color: #52CC48; }',
        'td.heading { font-size: 4pt; }',
        '</style>',
        '</head>',
        '<body>'
    ]

    result.append("<h1>Films watched in {0}...{1}</h1>".format(
        dateint[0], dateint[-1]))
    result.append("<table>")

    def silent_coercion(i):
        """Coerce given object to integer. If not integer, throw
        something negative."""
        try:
            return int(i)
        except ValueError:
            return -1

    def make_row(items, force_class=None):
        res = ['<tr>']
        for i in items:
            format_class = ''
            if silent_coercion(i) > 2:
                format_class = 'lots'
            elif i == 2:
                format_class = 'good'
            elif i == 1:
                format_class = 'one'

            if force_class:
                format_class = force_class

            format_string = '<td class=\"' + format_class + '\">{0}</td>'
            res.append(format_string.format(i))
        res.append('</tr>')
        return ''.join(res)

    monthline = [d.strftime("%b <br/> %d") for d in weekstarts]
    result.append(make_row([''] + monthline, 'heading'))
    for weekday in range(0, 7):
        row = make_row([WEEKDAY_STR[weekday]] +
                       [watched[d]
                        for d in islice(dateint, weekday, None, 7)])
        result.append(row)
            
    
    result.append("</table>")

    # result.append("<h1>Views over time</h1>")
    result.append(draw_view_graph(watched))

    result.append("</body>")
    result.append("</html>")

    return '\n'.join(result)
    

FORMATTERS = {'text': actcal_text,
              'html': actcal_html}
