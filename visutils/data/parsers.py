# encoding=utf-8
import datetime
from dateutil import parser
from iso8601 import parse_date
#
# Boolean
#
def parse_boolean(obj):
    s = str(obj).strip().lower()
    return not s in ['false', 'f', 'n', '0', '']

#
# Utils
#
def skip_parsing(value):
    """
    Parser that leaves the string unparsed, stopping the parser when trying
    to be smart.  For example, ``'0001'`` is not converted into ``1L``.
    """
    return value

#
# Dates
#

NULL_DATES = ('0001-01-01', '0001-01-01T00:00:00')

def parse_epoch_datetime(time_value):
    if time_value == '0':
        return None
    return datetime.datetime.fromtimestamp(float(time_value) / 1000)


def parse_iso_datetime(obj):
    # todo - find a slightly more tolerant way to parse iso dates or force all the implementors to get it right
    date_formats = ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S.%f+00:00', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT:%H:%M:%S',
                    '%Y-%m-%dT%H:%M:%S','%Y-%m-%d']

    date_string = str(obj)
    if date_string in NULL_DATES:
        return

    try:
        return parse_date(date_string)
    except:
        pass

    try:
        return parser.parse(date_string)
    except:
        pass

    for date_format in date_formats:
        # repeatedly try matching with different date formats, exiting as soon as one matches
        try:
            date = datetime.datetime.strptime(date_string, date_format)
        except:
            continue
        else:
            break
    else:
        date = obj

    # The null date has year 1.
    if getattr(date, 'year', None) == 1:
        return None

    return date


def parse_iso_date(obj):
    date_string = str(obj)
    try:
        if date_string in NULL_DATES:
            return
        else:
            return datetime.datetime.strptime(date_string, '%Y-%m-%d')
    except:
        return obj


def parse_iso_date2str(obj):
    date_string = str(obj)
    if date_string in NULL_DATES:
        return
    try:
        return datetime.datetime.strptime(date_string, '%Y-%m-%d').strftime("%d.%m.%y")
    except:
        return obj


def format_sap_period(obj):
    try:
        strDates = str(obj).split('-')
        if len(strDates) == 2:
            newDate = datetime.datetime.strptime(strDates[0], '%d%m%Y').strftime("%d.%m.%y")
            newDate = newDate + ' - ' + datetime.datetime.strptime(strDates[1], '%d%m%Y').strftime("%d.%m.%y")
            return newDate
        else:
            return obj
    except:
        return obj


def remove_xml_version(src):
    return src[src.find('?>') + 2:]


def inject_xml_version(src):
    return u'<?xml version="1.0" encoding="UTF-8"?>' + src
