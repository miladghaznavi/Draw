import sys
import os.path
import argparse
import csv
import math
import webbrowser
from StringIO import StringIO

from nvd3 import lineChart, lineWithFocusChart

DELIM = ","
NEWLINE = "\n"

ACCEPTANCE = "acceptance"
COST = "cost"
REJECTED = "rejected"
TIME = "time"
UTIL = "util"

ACCEPTANCE_FILE = "acceptance.txt"
COST_FILE = "cost.txt"
REJECTED_FILE = "rejected.txt"
TIME_FILE = "time.txt"
UTIL_FILE = "util.txt"
LINE_CHART = "line"
LINE_WITH_FOCUS_CHART = "focus"


def def_parser():
    parser = argparse.ArgumentParser(description='Draw graphs for EVNFP')
    parser.add_argument('-i', '--input', dest='i', help='Folder containing output folders',
                        type=str, required=True)
    parser.add_argument('-m', '--measure', dest='m',
                        help='Which measurement (one of "acceptance", "cost", "time", "util")',
                        type=str, required=True)
    parser.add_argument('-x', '--xfield', dest='x', help='Which field',
                        type=str, required=True)
    parser.add_argument('-y', '--yfield', dest='y', help='Which field',
                        type=str, required=True)
    parser.add_argument('-c', '--clean', dest='c', help='Clean data in y (default is None)',
                        type=int, default=None)
    parser.add_argument('-t', '--type', dest='t',
                        help='Chart type (default is %s). <%s, %s>' % (LINE_CHART, LINE_CHART, LINE_WITH_FOCUS_CHART),
                        type=str, default=LINE_CHART)
    parser.add_argument('-e', '--exclude', dest='e', help='exclude these floders',
                        type=str, default=None)
    parser.add_argument('-l', '--log', dest='l', help='Log output path',
                        type=str, default=None)
    parser.add_argument('-d', '--draw', dest='d', help='Draw file name',
                        type=str, default=None)
    return parser


def parse_args(parser):
    opts = vars(parser.parse_args(sys.argv[1:]))
    if not os.path.isdir(opts['i']):
        raise Exception('Folder \'%s\' does not exist!' % opts['i'])
    if opts['l'] == None:
        opts['l'] = "%s.csv" % opts['y']
    if opts['d'] == None:
        opts['d'] = "%s.html" % opts['y']
    if opts['e'] != None:
        opts['e'] = opts['e'].lower().split(',')
    if opts['t'] != LINE_CHART and opts['t'] != LINE_WITH_FOCUS_CHART:
        raise Exception('No chart type "%s"' % opts['t'])
    return opts


def which_file(arg):
    if arg == ACCEPTANCE:
        result = ACCEPTANCE_FILE
    elif arg == COST:
        result = COST_FILE
    elif arg == TIME:
        result = TIME_FILE
    elif arg == UTIL:
        result = UTIL_FILE
    else:
        raise Exception("Not valid file option")
    return result


def parse_file(path, xfield, yfield):
    x = []
    y = []
    with open(path) as handle:
        content = handle.read()
        dictReader = csv.DictReader(StringIO(content))
        for row in dictReader:
            x.append(row[xfield])
            y.append(row[yfield])
    return {'x': x, 'y': y}


def clean(logs, what):
    for alg in logs:
        i = 0
        while True:
            if i >= len(logs[alg]['y']):
                break
            if float(logs[alg]['y'][i]) <= what:
                del logs[alg]['x'][i]
                del logs[alg]['y'][i]
                i -= 1
            i += 1


def xAxisScale(logs):
    result = 0
    for alg in logs:
        for x in logs[alg]['x']:
            result = max(float(x), result)

    result = math.ceil(float(result) / 10) * 10
    return [0, result]


def yAxisScale(logs):
    result = 0
    for alg in logs:
        for y in logs[alg]['y']:
            result = max(float(y), result)

    result = math.ceil(float(result) / 10) * 10
    return [0, result]


def log(handle, logs, xfield):
    minsize = float('inf')

    handle.write(xfield)
    for alg in logs:
        handle.write(DELIM + alg)
        minsize = min(minsize, len(logs[alg]['x']))

    for i in range(0, minsize):
        xwritten = False
        handle.write(NEWLINE)
        for alg in logs:
            if not xwritten:
                handle.write(logs[alg]['x'][i])
                xwritten = True
            handle.write(DELIM + logs[alg]['y'][i])


def draw(handle, type, logs, **kwargs):
    kwparams = {
        'name': "lineChart",
        'width': 1000,
        'height': 500,
        'chart_attr': {
            'forceY': yAxisScale(logs),
            'forceX': xAxisScale(logs),
            'xAxis.axisLabel': ('"%s"' % kwargs['xlabel']),
            'yAxis.axisLabel': ('"%s"' % kwargs['ylabel']),
        },
    }
    chart = None
    if type == LINE_CHART:
        chart = lineChart(**kwparams)
    elif type == LINE_WITH_FOCUS_CHART:
        chart = lineWithFocusChart(**kwparams)

    chart.show_labels = True

    for alg in logs:
        extra_serie = {"tooltip": {"y_start": kwargs['ylabel'] + "is ", "y_end": "!"}}
        chart.add_serie(y=logs[alg]['y'], x=logs[alg]['x'], extra=extra_serie, name=alg)

    chart.buildhtml()
    handle.write(str(chart))


def main():
    try:
        args = parse_args(def_parser())
        base_dir = args['i']
        xfield = args['x']
        yfield = args['y']
        type = args['t']

        dirs = next(os.walk(base_dir))[1]
        wh_file = which_file(args['m'])

        logs = {}
        for dir in dirs:
            if dir.lower() in args['e']:
                continue
            logs[dir] = parse_file(os.path.join(base_dir, dir, wh_file), xfield, yfield)

        clean(logs, args['c'])

        path = os.path.abspath(args['l'])
        with open(path, 'w') as handle:
            log(handle, logs, xfield)
        path = os.path.abspath(args['d'])
        with open(path, 'w') as handle:
            draw(handle, type, logs, xlabel=xfield, ylabel=yfield)

        uri = "file://" + path
        webbrowser.open(uri, new=2)
    except argparse.ArgumentError as exc:
        print(exc)
    except Exception as exc:
        print(exc)


if __name__ == "__main__":
    main()
