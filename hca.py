#!/usr/bin/env python3

import time
import os
import sys
import argparse
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn


class http_cache_analyzer:
  options = {}
  request = None
  response = None
  headers = {}
  usefull_headers = {}
  timeout = 30
  max_time = 30
  connect_timeout = 30

  meaningfull_headers = ['Age', 'Cache-Control', 'ETag', 'Expire', 'Last-Modified', 'Pragma']


  def allowed_gai_family(self):
    """
     https://github.com/shazow/urllib3/blob/master/urllib3/util/connection.py
    """
    family = socket.AF_INET

    if self.options['ipv4']:
      print('forcing ipv4')
      family = socket.AF_INET
    elif self.options['ipv6']:
      print('forcing ipv6')
      family = socket.AF_INET6

    return family


  def request(self, url, **options):
    self.options = options['options']
    del(self.options['url'])
    #print(self.options)
    urllib3_cn.allowed_gai_family = self.allowed_gai_family

    print("Requesting url {}".format(url))
    self.response = requests.get(url)
    print(self.response.status_code)

    return self.response

  def get_headers(self):
    return self.response.headers

  def filter_cache_headers(self):
    h = {}
    for meaningfull_header in self.meaningfull_headers:
      if meaningfull_header in self.headers:
        h.update({meaningfull_header: self.headers[meaningfull_header]})

    return h

  def analyze(self, response = None):
    if response:
      self.response = response

    self.headers = self.get_headers()
    print(self.headers)
    self.usefull_headers = self.filter_cache_headers()
    #print(self.headers)
    self.analyze_headers()

  def analyze_header_cachecontrol(self, cachecontrol):
    cache_control_values_single = [
      "must-revalidate",
      "no-cache",
      "no-store",
      "no-transform",
      "public",
      "private",
      "proxy-revalidate",
    ]
    cache_control_expirations = [
      "max-age=",
      "s-maxage="
    ]
    tokens = cachecontrol.split(', ')
    print(tokens)
    for cache_control_value in cache_control_values_single:
      if cache_control_value in tokens:
        print("{} is in cache-control".format(cache_control_value))

    for cache_control_value in cache_control_expirations:
      for token in tokens:
        if cache_control_value in token:
          (ccv, seconds) = token.split("=")
          print("Cache-Control: token '{}' has value '{}'.".format(ccv, str(seconds)))



  def analyze_headers(self):
    print("")

    """
    Age
    """
    if 'Age' in self.usefull_headers:
      print("Age is present, current value: '{}'".format(str(self.usefull_headers['Age'])))
    else:
      print("Age is absent.")

    """
    Cache-Control
    """
    if 'Cache-Control' in self.usefull_headers:
      print("Cache-Control ok, current value: '{}'".format(self.usefull_headers['Cache-Control']))
      self.analyze_header_cachecontrol(self.usefull_headers['Cache-Control'])
    else:
      print("Cache-Control: NOK")

    """
    ETag
    """
    if 'ETag' in self.usefull_headers:
      print("ETag ok")
    else:
      print("ETag NOK")

    """
    Expire
    """
    if 'Expire' in self.usefull_headers:
      if 'Cache-Control' in self.usefull_headers:
        print("Expire is present, but it's value '{}' is ignored since Cache-Control is present".format(self.usefull_headers['Expire']))
      else:
        print("Expire ok, '{}'".format(self.usefull_headers['Expire']))
    else:
      if 'Cache-Control' in self.usefull_headers:
        print("Expire is absent, but Cache-Control is present, which is good.")
      else:
        print("Expire is absent. It's ok")

    """
    Last-Modified
    """
    if 'Last-Modified' in self.usefull_headers:
      print("Last-Modified ok")
    else:
      print("Last-Modified is absent, it's okay")

    """
    Pragma
    """
    if 'Pragma' in self.usefull_headers:
      print("Pragma: Pragma is useless since HTTP/1.1. Current value: '{}'".format(self.usefull_headers['Pragma']))
    else:
      print("Pragma is absent. good.")


if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('url', type=str, help="URL to check")
  parser.add_argument('-r', '--resolve',       required=False, help="Resolve domain:port to ip", type=str)
  parser.add_argument('-v', '--verbose',    required=False, help="Set to verbose", action="store_true")
  parser.add_argument('-q', '--quiet',    required=False, help="Set to quiet", action="store_true")

  group_ip = parser.add_mutually_exclusive_group()
  group_ip.add_argument('-4', '--ipv4', required=False, help="Resolve in ipv4 only", action="store_true")
  group_ip.add_argument('-6', '--ipv6', required=False, help="Resolve in ipv6 only", action="store_true")
  args = parser.parse_args()

  hca = http_cache_analyzer()
  r = hca.request(args.url, options = vars(args))
  rr = hca.analyze()

