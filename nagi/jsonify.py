#/usr/bin/env python

"""
The module provide the json serialize and parse functions
"""

from functools import wraps


import datetime
import decimal

try:
    import simplejson as json  # try external module
except ImportError:
    import json 

def custom_json(o):
    """Returns the json serialize content
    when the o is a object isinstance and has as_json method, then it will call the method, 
    and dumps the return content. Also it can handle the datetime.date and decimal dumps
    """
    if hasattr(o, 'as_json') and callable(o.as_json):
        return o.as_json()
    if isinstance(o, (datetime.date,
                      datetime.datetime,
                      datetime.time)):
        return o.isoformat()[:19].replace('T', ' ')
    elif isinstance(o, (int, long)):
        return int(o)
    elif isinstance(o, decimal.Decimal):
        return str(o)
    else:
        raise TypeError(repr(o) + " is not JSON serializable")

loads = json.loads

def dumps(value, default=custom_json):
    """Returns the json serialize stream"""
    return json.dumps(value,
        default=default).replace(ur'\u2028',
                                 '\\u2028').replace(ur'\2029',
                                                    '\\u2029')
