# encoding=utf-8

def parse_float_isl(value):
    try:
        value = value.replace(',', '.')
        return float(value)
    except:
        return float('0')


#
# VIS
#
def convert_ad2email(obj):
    if str(obj).upper().startswith('AD\\'):
        return str(obj)[3:] + '@vis.is'
    else:
        return obj

#
# String, unicode, etc
#
ISL_CHARS = u'áéíóúýþðæöÁÉÍÓÚÝÞÐÆÖ'.split('\n')
ISL_CHARS_REPLACE_SAFE = u'aeiouythdaeoAEIOUYThDAeO'.split('\n')

def isl_enska(obj):
    ret = u""
    for c in obj:
        if c in ISL_CHARS:
            c = ISL_CHARS_REPLACE_SAFE[ISL_CHARS.index(c)]
        ret = ret + c
    return ret

def _insert_substring_at_positions(superstring, substring, positions):
    insertion_count = 0
    for position in sorted(positions):
        position = position + insertion_count
        superstring = superstring[:position] + substring + superstring[position:]
    return superstring

LOCAL_PHONE_NUMBER_SEPARATION_POSITIONS = [3]
def get_localized_phone_number(phone_number, fail_silently=True, separator=' ',
    area_code='354', min_length=7, max_length=7, separate_at_positions=None):
    """
    Given a string containing 10 digits, return it as two groups of the
    last 7 digits (area code removed), separated by a space before the
    last 4 digits.

    If the number of digits after removing non-digit characters is not
    exactly 10, `ValueError` will be raised.  This is unless `fail_silently`
    is specified, the string with non-digits removed is returned unformatted,
    but no exceptions are raised.

    >>> get_localized_phone_number("+354 5 88 55 22")
    '588 5522'

    Because Iceland is the center of the universe, its values are the
    default to localize by, but `area_code`, `max_length` and `min_length`
    can be modified to accept anything on those formats.

    `separate_at_positions` is a list of 1-based positions in the list
    after which a `separator` should be written.
    """
    separate_at_positions = separate_at_positions or LOCAL_PHONE_NUMBER_SEPARATION_POSITIONS
    min_length = len(area_code) + min_length
    max_length = len(area_code) + max_length

    phone_number = filter(lambda char: char.isdigit(), phone_number)  # remove non-digits
    if min_length <= len(phone_number) <= max_length and phone_number.startswith(area_code):
        return _insert_substring_at_positions(phone_number, separator, separate_at_positions)
    else:
        if fail_silently:
            return phone_number
        else:
            raise ValueError("Can't localize unknown phone number '{phone_number}'.".format(
                phone_number=phone_number))