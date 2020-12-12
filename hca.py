#!/usr/bin/env python3

#import time
#import os
#import sys
import argparse

"""
for --out option, always write as json data
"""
import json

import http_cache_analyzer

#dns_cache = {}
## Capture a dict of hostname and their IPs to override with
#def override_dns(domain, ip):
#    dns_cache[domain] = ip
#
#
#prv_getaddrinfo = socket.getaddrinfo
## Override default socket.getaddrinfo() and pass ip instead of host
## if override is detected
#def new_getaddrinfo(*args):
#    if args[0] in dns_cache:
#        print("Forcing FQDN: {} to IP: {}".format(args[0], dns_cache[args[0]]))
#        return prv_getaddrinfo(dns_cache[args[0]], *args[1:])
#    else:
#        return prv_getaddrinfo(*args)
#
#
#socket.getaddrinfo = new_getaddrinfo


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('url', type=str, help="URL to check")
  #parser.add_argument('-r', '--resolve',       required=False, help="Resolve domain:port to ip", type=str)
  parser.add_argument('-v', '--verbose',    required=False, help="Set to verbose", action="store_true")
  parser.add_argument('-q', '--quiet',    required=False, help="Set to quiet", action="store_true")

  parser.add_argument('-A', '--user-agent', required=False, help="User agent to use", type=str, default="HTTP Cache Analyzer https://github.com/Yoda-BZH/http-cache-analyzer")
  parser.add_argument('-a', '--assets',     required=False, help="Parse all assets too", action="store_true")

  parser.add_argument('-o', '--out',        required=False, help="Store results in given file", type=argparse.FileType('w'))

  group_ip = parser.add_mutually_exclusive_group()
  group_ip.add_argument('-4', '--ipv4', required=False, help="Resolve in ipv4 only", action="store_true")
  group_ip.add_argument('-6', '--ipv6', required=False, help="Resolve in ipv6 only", action="store_true")
  args = parser.parse_args()

  hca = http_cache_analyzer.analyzer()
  hca.request(args.url, options = vars(args))
  hca.analyze()
  if args.assets:
    http_parser = http_cache_analyzer.parser(hca)
    http_parser.parse()

    hca.show_results()
    #print("CALLING RESULTS")
    http_parser.show_results()
  else:
    hca.show_results()

  if args.out:
    r = {}
    r['main'] = hca.get_results()
    if args.assets:
      r['assets'] = http_parser.get_results()
    args.out.write(json.dumps(r, cls=http_cache_analyzer.jsonencoder))
