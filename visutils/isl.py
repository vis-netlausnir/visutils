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
