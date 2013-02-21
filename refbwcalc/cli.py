import argparse
import csv
import re
import sys
import io
import blessings
import colorama
from refbwcalc import (Bandwidth, Cost, get_version, calculate_cost, 
                       DEFAULT_COMPARISON_BW)

class Color(object):
    def __init__(self, term, enabled):
        self._term = term
        self.enabled = enabled

    def __getattr__(self, name):
        if self.enabled:
            return getattr(self._term, name)
        return ''


def unique(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if x not in seen and not seen_add(x)]


def generate_calc_list(refbw, comp_list):
    for compbw in comp_list:
        yield calculate_cost(refbw, compbw)


def output_terminal(refbw, comp_list, color):
    if color:
        colorama.init()
    term = blessings.Terminal()
    c = Color(term, color)

    print "Calulating the OSPF cost values"\
          "for reference bandwidth: '{c.bright_green}{}{c.normal}'\n".format(
           refbw, c=c)

    for comp in generate_calc_list(refbw, comp_list):
        info = "({})".format(comp.info) if comp.info else ""
        print "Cost at {c.bright_green}{r.compbw.value:>5,.4g}"\
              "{c.green}{r.compbw.unit:<4}{c.normal}:  "\
              "{c.cyan}{r.cost:5}{c.normal} {c.bright_yellow}{info:18}{c.normal} "\
              "hops @ 24-bit {c.magenta}{r.hops_24bit:10}{c.normal}   "\
              "hops @ 32-bit {c.magenta}{r.hops_32bit:10}{c.normal}".format(
               r=comp, info=info, c=c)


def output_csv(refbw, comp_list):
    output = io.BytesIO()
    csv_out = csv.DictWriter(output, Cost._fields)
    csv_out.writeheader()
    csv_out.writerows([comp._asdict() for comp in generate_calc_list(refbw, comp_list)])
    print output.getvalue()


def is_color_supported():
    term = blessings.Terminal()
    try:
        return bool(term.number_of_colors)
    except blessings.curses.error:
        return False


def main(argv=sys.argv[1:]):
    # Test for color support to setup options 
    # We may be able to just remove this.
    color_support = is_color_supported()

    parser = argparse.ArgumentParser(description="""
        Find optimal autocost reference bandwidth for OSPF by comparing 
        the calulated value against common links found in modern networks.""")
    parser.add_argument('ref_bw', metavar='REFBW',
                        help="Reference bandwidth to calulate against")
    default_compairisons = [str(Bandwidth(x)) for x in DEFAULT_COMPARISON_BW]
    parser.add_argument('-b', '--comparison-bw', metavar='BW', nargs='*', 
                        default=DEFAULT_COMPARISON_BW, dest="bw_values",
                        help="Bandwith values to test (default: %s)" % 
                              ', '.join(default_compairisons))
    parser.add_argument('-a', '--add-comparison', metavar='BW', nargs='*',
                        default = [], dest="add_bw_values",
                        help="Add additional bandwidth values to test.")
    parser.add_argument('-n', '--no-color', action='store_false', 
                        dest='color', default=color_support,
                        help="Don't show any colors in the output.")
    parser.add_argument('-c', '--color', action='store_true', dest='color', 
                        default=color_support, help="Force output of colors.")
    parser.add_argument('-f', '--format', choices=['normal', 'csv'], 
                        default='normal',
                        help="Output format. 'normal' outputs fancy formating "\
                             "(optionally colored). 'csv' outputs CSV format "\
                             "with header.")
    parser.add_argument('--version', action='version', 
                        version='%(prog)s ' + get_version())

    args = parser.parse_args(argv)  
    refbw = Bandwidth(args.ref_bw, default_unit='m')

    comp_list = [Bandwidth(x) for x in args.bw_values + args.add_bw_values]
    comp_list = unique(sorted(comp_list, reverse=True))

    if args.format == 'normal':
        output_terminal(refbw, comp_list, args.color)
    elif args.format == 'csv':
        output_csv(refbw, comp_list)


if __name__ == '__main__':
    main()