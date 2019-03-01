#!/usr/bin/env python

# Author: Andrei Buzoianu <andrei@buzoianu.info>
# 2019-02-28 Version 0.1

import requests
import time
import sys
import json
import logging
from optparse import OptionParser

url = 'https://api.ssllabs.com/api/v2/analyze'

# Possible scores: 'A+', 'A', 'A-', 'B', 'C', 'D', 'E', 'F', 'T' (trust issues) and 'M' (certificate name mismatch).
scores = {'A+': 1, 'A': 1, 'A-': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'T': 6, 'M': 6}

# Nagios status codes
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

def main():

    parser = OptionParser(usage="usage: %prog -w limit -c limit", version="%prog 0.1")
    parser.add_option("-H", "--host", dest="host", metavar="STRING", type="string")
    parser.add_option("-p", "--publish", action="store_true", default=False, dest="publish", help="publish results at Qualys SSL Labs")
    parser.add_option("-u", "--use-cache", action="store_true", default=False, dest="cache", help="do not accept results from cache")
    parser.add_option("-w", "--warning", dest="warn", metavar="STRING", type="string")
    parser.add_option("-c", "--critical", dest="crit", metavar="STRING", type="string")
    (options, args) = parser.parse_args()

    if len(sys.argv[1:]) < 3:
        parser.print_help()
        sys.exit(STATE_UNKNOWN)

    CRIT = str(options.crit)
    WARN = str(options.warn)

    data = requestScan(options.host, options.publish, options.cache)
    score = data['endpoints'][0]['grade']
    sys.stdout.write(score)

    if scores[score] >= scores[CRIT]:
        sys.exit(STATE_CRITICAL)
    elif scores[score] >= scores[WARN]:
        sys.exit(STATE_WARNING)
    else:
        sys.exit(STATE_OK)

def requestScan(host, publish, cache):
    payload = {
                'host': host,
                'all': 'done',
              }

    if publish:
        payload['publish'] = 'on';

    if cache:
        payload['startNew'] = 'off';
        payload['fromCache'] = 'on';
        results = callAPI(url, payload)
    else:
        payload['startNew'] = 'on';
        payload['ignoreMismatch'] = 'on';
        results = callAPI(url, payload)
        payload.pop('startNew')

        while results['status'] != 'READY' and results['status'] != 'ERROR':
            time.sleep(60)
            results = callAPI(url, payload)

    return results

def callAPI(url, payload={}):
    try:
        response = requests.get(url, params=payload, timeout=5)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.exception("Request failed: {0}".format(e.message))
        sys.exit(STATE_UNKNOWN)
    except requests.exceptions.HTTPError as h:
        logging.exception("HTTP Error: {}".format(h.message))
        sys.exit(STATE_UNKNOWN)
    except requests.exceptions.ConnectionError as c:
        logging.exception("Error Connecting: {0}".format(c.message))
        sys.exit(STATE_UNKNOWN)
    except requests.exceptions.Timeout as t:
        logging.exception("Timeout Error: {0}".format(t.message))
        sys.exit(STATE_UNKNOWN)

    return response.json()

if __name__ == '__main__':
    main()
