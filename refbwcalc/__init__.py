import re
from collections import OrderedDict, namedtuple
from functools import total_ordering

DEFAULT_COMPARISON_BW = [
    "800g",
    "400g",
    "100g",
    "40g",
    "10g",
    "1g",
    "100m",
    "10m",
    "6.176m",
    "3.088m",
    "1.544444444m",
    "768k",
    "384k",
]


@total_ordering
class Bandwidth(object):
    """Object to represent and parse bandwith values"""

    UNITS = {
        "bps": 1,
        "Kbps": 2**10,
        "Mbps": 2**20,
        "Gbps": 2**30,
        "Tbps": 2**40,
        "Pbps": 2**50,
    }
    # Use lower case for matching
    MATCHING_UNITS = {x.lower(): y for (x, y) in UNITS.items()}
    # Also allow matching on the first letter ommiting bps
    MATCHING_UNITS.update({x[0]: y for (x, y) in MATCHING_UNITS.items()})

    def __init__(self, value=None, default_unit=None):
        if value:
            self.parse(value, default_unit=default_unit)
        else:
            self.bw = 0

    def parse(self, value, default_unit=None):
        if isinstance(value, str):
            # See if it is just a number without a units
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass

        if isinstance(value, (float, int)):
            if default_unit:
                if default_unit not in self.MATCHING_UNITS.keys():
                    raise ValueError(
                        "Invalid unit: '%s'. Unit must be one of the "
                        "following '%s"
                        % (default_unit, ", ".join(self.MATCHING_UNITS.keys()))
                    )
                return self.parse("%s%s" % (value, default_unit))
        else:
            match = re.match(
                r"(?P<num>[\d.]+)(?P<unit>[ptgmkb](k(bps)?)?)",
                value.strip(),
                flags=re.IGNORECASE,
            )
            if not match:
                raise ValueError(
                    "invalid bandwidth string '%s'. Must be digit"
                    "followed one of the following units: '%s'"
                    % (value, ", ".join(self.MATCHING_UNITS.keys()))
                )
            value = int(
                float(match.group("num"))
                * self.MATCHING_UNITS[match.group("unit").lower()]
            )
        self.bw = value
        return self

    def _update_optimal_unit(self):
        # Start of with value in bps
        bw = self._bw
        for unit in list(self.UNITS.keys())[:-1]:
            if bw < 1024.0:
                break
            bw /= 1024.0
        else:
            # We ran out.  Wow that is fast bandwidth
            unit = list(self.UNITS.keys())[-1]
        (self.value, self.unit) = (bw, unit)

    def format_pretty(self, precision=4):
        return "{value:,.{precision}g}{unit}".format(
            value=self.value, unit=self.unit, precision=precision
        )

    @property
    def bw(self):
        return self._bw

    @bw.setter
    def bw(self, val):
        self._bw = val
        self._update_optimal_unit()

    def __str__(self):
        return self.format_pretty()

    def __eq__(self, other):
        if isinstance(other, Bandwidth):
            return self.bw == other.bw
        else:
            return self.bw == Bandwidth(other)

    def __lt__(self, other):
        if isinstance(other, Bandwidth):
            return self.bw < other.bw
        else:
            return self.bw < Bandwidth(other)


Cost = namedtuple(
    "Cost", ["refbw", "compbw", "cost", "hops_24bit", "hops_32bit", "info"]
)


def calculate_cost(refbw, compbw):
    cost = int(refbw.bw / compbw.bw)
    info = ""

    if cost < 1:
        cost = 1
        info = "less than min"

    if cost > 65535:
        cost = 65535
        info = "greater than max"

    hops_24bit = int(16777215 / cost)
    hops_32bit = int(4294967295 / cost)

    return Cost(refbw, compbw, cost, hops_24bit, hops_32bit, info)
