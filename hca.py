#!/usr/bin/env python3

import time
import os
import sys
import argparse
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn

default_scheme = "https://"

def show_ok(text):
  print("[OK] {}".format(text))

def show_warning(text):
  print("[!!] {}".format(text))

def show_info(text):
  print("[--] {}".format(text))


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


  def request(self, user_url, **options):
    self.options = options['options']
    del(self.options['url'])
    #print(self.options)
    urllib3_cn.allowed_gai_family = self.allowed_gai_family

    url = user_url
    scheme_token = url[:5]
    if scheme_token != "https" and scheme_token != "http:":
      url = "{}{}".format(default_scheme, url)

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
    score_modifier = 0

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
        show_ok("{} is in cache-control".format(cache_control_value))

    for cache_control_value in cache_control_expirations:
      for token in tokens:
        if cache_control_value in token:
          (ccv, seconds) = token.split("=")
          print("Cache-Control: token '{}' has value '{}'.".format(ccv, str(seconds)))

    return score_modifier

  def analyze_headers(self):
    print("")

    score = 50

    """
    Age
    """
    if 'Age' in self.usefull_headers:
      show_ok("Age is present, current value: '{}'".format(str(self.usefull_headers['Age'])))
      score += 10
    else:
      show_info("Age is absent.")

    """
    Cache-Control
    """
    if 'Cache-Control' in self.usefull_headers:
      show_ok("Cache-Control ok, current value: '{}'".format(self.usefull_headers['Cache-Control']))
      score += 30
      score += self.analyze_header_cachecontrol(self.usefull_headers['Cache-Control'])
      #if 'Age' not in self.usefull_headers:
      #  show_warning("But wait, age is not present ?")
    else:
      show_warning("Cache-Control is absent. Default value is '{}', which deactive all cache mecanismes".format('no-store, no-cache'))
      score -= 30

    """
    ETag
    """
    if 'ETag' in self.usefull_headers:
      etag = self.usefull_headers['ETag'].strip('"\'')
      etag_strs = ["ETag is present, current value: {}.".format(etag)]
      score += 10
      if etag[-5:] == "-gzip":
        score += 5
        etag_strs.append("Etag is gzipped, bonus points")
      show_ok(" ".join(etag_strs))

    else:
      etag_strs = ["ETag is absent."]
      if 'Cache-Control' in self.usefull_headers:
        etag_strs.append("But it's ok, Cache-Control can be used too.")
        show_info(" ".join(etag_strs))
      else:
        etag_strs.append("Cache-Control is absent too. No cache can be made.")
        show_warning(" ".join(etag_strs))
        score -= 10

    """
    Expire
    """
    if 'Expire' in self.usefull_headers:
      if 'Cache-Control' in self.usefull_headers:
        show_ok("Expire is present, but it's value '{}' is ignored since Cache-Control is present".format(self.usefull_headers['Expire']))
      else:
        show_ok("Expire ok, '{}'".format(self.usefull_headers['Expire']))
        score += 5
    else:
      if 'Cache-Control' in self.usefull_headers:
        show_ok("Expire is absent, but Cache-Control is present, which is good.")
      else:
        show_info("Expire is absent. It's ok")

    """
    Last-Modified
    """
    if 'Last-Modified' in self.usefull_headers:
      show_ok("Last-Modified is presnt, current value: '{}'".format(self.usefull_headers['Last-Modified']))
      score += 5
    else:
      show_info("Last-Modified is absent, it's okay")

    """
    Pragma
    """
    if 'Pragma' in self.usefull_headers:
      show_info("Pragma: Pragma is useless since HTTP/1.1. Current value: '{}'".format(self.usefull_headers['Pragma']))
      score -= 5
    else:
      show_ok("Pragma is absent. It'good. Pragma is useless since HTTP/1.1. ")

    print("Final score: {}/100".format(score))

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

