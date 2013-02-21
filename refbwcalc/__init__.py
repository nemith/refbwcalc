import argparse
import re
import sys
from collections import namedtuple


#          Major, Minor, SR
VERSION = (0,     1,     None)


DEFAULT_COMPARISON_BW = ['100g', '40g', '10g', '1g', '100m', '10m', '6.176m',
                         '3.088m', '1.544444444m', '768k', '384k']


def get_version():
    version = '%s.%s' % (VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '%s.%s' % (version, VERSION[2])
    return version


def parse_bandwidth(value, default_unit=None):
    UNIT_TABLE = {
        'p': 2**50,
        't': 2**40,
        'g': 2**30,
        'm': 2**20,
        'k': 2**10,
        'b': 1,
    }

    if isinstance(value, str):
        # See if it is just a number without a uniot
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
    if isinstance(value, (float, int, long)):
        if default_unit:
            if default_unit not in UNIT_TABLE.keys():
                raise ValueError("Invalid unit: '%s'. Unit must be one of the " \
                                 "following '%s" % 
                                 (default_unit, ', '.join(UNIT_TABLE.keys())))
            return parse_bandwidth("%s%s" % (value, default_unit))
        else:
            return value
    else:
        match = re.match(r'(?P<num>[\d.]+)(?P<unit>[ptgmkb](k(bps)?)?)', 
                         value.strip(), flags=re.IGNORECASE)
        if not match:
            raise ValueError("invalid bandwidth string '%s'. Must be digit" \
                             "followed one of the following units: '%s'" % 
                                 (value, ', '.join(UNIT_TABLE.keys())))
        return int(float(match.group('num')) * 
               UNIT_TABLE[match.group('unit').lower()])


def format_bandwidth(num, precision=4):
    FORMAT = "{:,.%dg}{}" % precision
    for x in ['bps', 'Kbps', 'Mbps', 'Gbps']:
        if num < 1024.0:
            return FORMAT.format(num, x)
        num /= 1024.0
    return FORMAT.format(num, 'Tbps')


Cost = namedtuple('Cost', ['refbw', 'compbw', 'cost', 'hops_24bit', 'hops_32bit', 'info'])
def calculate_cost(refbw, compbw):

    cost = refbw/compbw
    info = ""

    if cost < 1:
        cost = 1
        info = "less than min"
 
    if cost > 65535:
        cost = 65535
        info = "greater than max"
 
    hops_24bit = 16777215/cost
    hops_32bit = 4294967295/cost
 
    return Cost(refbw, compbw, cost, hops_24bit, hops_32bit, info)
