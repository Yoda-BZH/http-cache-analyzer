#!/usr/bin/env python3

#import time
#import os
#import sys
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

def show_title(text):
  print("")
  print("{} {} {}".format('-' * 8, text, '-' * (80 - 2 - len(text))))


class http_cache_analyzer:
  options = {}
  request = None
  response = None
  headers = {}
  usefull_headers = {}
  timeout = 30
  max_time = 30
  connect_timeout = 30

  score = 50
  meaningfull_headers = ['Age', 'Cache-Control', 'ETag', 'Expires', 'Last-Modified', 'Pragma']


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
    show_title("HTTP Query")
    self.options = options['options']
    del(self.options['url'])
    #print(self.options)
    urllib3_cn.allowed_gai_family = self.allowed_gai_family

    url = user_url
    scheme_token = url[:5]
    if scheme_token != "https" and scheme_token != "http:":
      url = "{}{}".format(default_scheme, url)

    request_headers = {
      'User-Agent': self.options['user_agent'],
    }

    show_info("Requesting url {}".format(url))
    self.response = requests.get(url, headers = request_headers)
    if self.response.status_code > 299:
      show_warning("HTTP Status code is {}".format(self.response.status_code))
      self.score -= 40
    else:
      show_ok("HTTP Status code is {}".format(self.response.status_code))

    if self.response.url.rstrip('/') != url.rstrip('/'):
      show_warning("Request was redirected to {}".format(self.response.url))

    if len(self.response.history) > 0:
      redirect_strs = [url]
      for history in self.response.history:
        redirect_strs.append(history.url)
      redirect_strs.append(self.response.url)
      redirect_strs = " -> ".join(redirect_strs)
      show_warning("Request was redirected: {}".format(redirect_strs))

    return self.response

  def get_headers(self):
    return self.response.headers

  def detect_public_cache(self):
    public_cache_headers = {
      'X-Varnish': {
        'provider': 'Varnish',
      },
      'X-Cache': {
        'provider': 'AWS or Varnish',
      },
      'X-Cache-Hits': {
        'provider': 'Varnish',
      },
      'X-Datacenter': {
        'provider': 'Azure',
      },
      'Akamai-Cache-Status': {
        'provider': 'Akamai',
      },
      'X-Edge-Location': {
        'provider': 'KeyCDN',
      },
      'Via': {
        'varnish': {
          'match': 'varnish',
          'provider': 'Varnish',
        },
        'cloudfront': {
          'match': 'CloudFront',
          'provider': 'AWS'
        },
      },
      'Server': {
        'cloudflare': {
          'match': 'cloudflare',
          'provider': 'cloudflare',
        },
        'GCP': {
          'match': 'gws',
          'provider': 'GCP',
        }
      },
      'Expect-CT': {
        'cloudflare': {
          'match': 'cloudflare',
          'provider': 'cloudflare',
        }
      },
      'P3P': {
        'GCP': {
          'match': 'CP="This is not a P3P policy! See g.co/p3phelp for more info."',
          'provider': 'GCP',
        }
      },
      'Content-Security-Policy': {
        'cloudflare': {
          'match': 'cloudflare.com',
          'provider': 'cloudflare',
        }
      }
    }
    show_title("Cache systems")
    cache_system_found = False
    for header_name, header_data in public_cache_headers.items():
      #print("Trying {}".format(header_name))
      if header_name in self.response.headers:
        if 'provider' in header_data:
          show_info("Presence of header '{}': '{}'".format(header_name, self.response.headers[header_name]))
          show_info("A cache system is detected: {}".format(header_data['provider']))
          cache_system_found = True
        else:
          for key, header_test in header_data.items():
            if header_test['match'] in self.headers[header_name]:
              show_info("HTTP header '{}': '{}' is matching '{}'".format(header_name, self.headers[header_name], header_test['match']))
              show_info("A cache system is detected: {}".format(header_test['provider']))
              cache_system_found = True

    if cache_system_found == False:
      show_info("No caching system found")
    else:
      self.score += 20

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
    show_title("HTTP Header list")
    for key, value in self.headers.items():
      show_info("{}: {}".format(key, value))

    self.detect_public_cache()

    self.usefull_headers = self.filter_cache_headers()
    #print(self.headers)
    self.analyze_headers()

  def results(self):
    show_title("Final score")
    print("Final score: {}/100".format(self.score))
    print("")

  def analyze_header_cachecontrol(self, cachecontrol):
    score_modifier = 0

    cache_control_values_single = {
      "must-revalidate": -1,
      "no-cache": -20,
      "no-store": -20,
      "no-transform": 5,
      "public": 5,
      "private": 5,
      "proxy-revalidate": -5,
    }
    cache_control_expirations = {
      "max-age=": 5,
      "s-maxage=": 5,
    }

    tokens = cachecontrol.split(', ')
    #print(tokens)
    for cache_control_value, ccv_modifier in cache_control_values_single.items():
      if cache_control_value in tokens:
        #show_info("{} is in cache-control".format(cache_control_value))
        score_modifier += ccv_modifier
        if score_modifier > 0:
          show_ok("Cache-Control has {}, adding {} points".format(cache_control_value, ccv_modifier))
        else:
          show_warning("Cache-Control has {}, removing {} points".format(cache_control_value, ccv_modifier))

    for cache_control_value, ccv_modifier in cache_control_expirations.items():
      for token in tokens:
        if cache_control_value in token:
          (ccv, seconds) = token.split("=")
          show_info("Cache-Control: token '{}' has value '{}'.".format(ccv, str(seconds)))
          if int(seconds) <= 0:
            show_warning("Cache-Control has {} value to 0 or lower, lowering the score by {}".format(ccv, ccv_modifier))
          else:
            show_ok("Cache-Control has {} value to 0 or higher, adding {} points to the score".format(ccv, ccv_modifier))
            ccv_modifier = -ccv_modifier
          score_modifier += ccv_modifier

    return score_modifier

  def analyze_headers(self):

    """
    Age
    """
    show_title("Header Age")
    if 'Age' in self.usefull_headers:
      show_ok("Age is present, current value: '{}'".format(str(self.usefull_headers['Age'])))
      self.score += 10
    else:
      show_info("Age is absent.")

    """
    Cache-Control
    """
    show_title("Header Cache-Control")
    if 'Cache-Control' in self.usefull_headers:
      show_ok("Cache-Control ok, current value: '{}'".format(self.usefull_headers['Cache-Control']))
      self.score += 30
      self.score += self.analyze_header_cachecontrol(self.usefull_headers['Cache-Control'])
      #if 'Age' not in self.usefull_headers:
      #  show_warning("But wait, age is not present ?")
    else:
      show_warning("Cache-Control is absent. Default value is '{}', which deactivate all cache mecanismes".format('no-store, no-cache'))
      self.score -= 30

    """
    ETag
    """
    show_title("Header ETag")
    if 'ETag' in self.usefull_headers:
      etag = self.usefull_headers['ETag'].strip('"\'')
      etag_strs = ["ETag is present, current value: {}.".format(etag)]
      self.score += 10
      if etag[-5:] == "-gzip":
        self.score += 5
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
        self.score -= 10

    """
    Expires
    """
    show_title("Header Expires")
    if 'Expires' in self.usefull_headers:
      if 'Cache-Control' in self.usefull_headers:
        show_ok("Expires is present, but it's value '{}' is ignored since Cache-Control is present".format(self.usefull_headers['Expires']))
      else:
        show_ok("Expires ok, '{}'".format(self.usefull_headers['Expires']))
        self.score += 5
    else:
      if 'Cache-Control' in self.usefull_headers:
        show_ok("Expires is absent, but Cache-Control is present, which is good.")
      else:
        show_info("Expires is absent. It's ok")

    """
    Last-Modified
    """
    show_title("Header Last-Modified")
    if 'Last-Modified' in self.usefull_headers:
      show_ok("Last-Modified is present, current value: '{}'".format(self.usefull_headers['Last-Modified']))
      self.score += 5
    else:
      show_info("Last-Modified is absent, it's okay")

    """
    Pragma
    """
    show_title("Header Pragma")
    if 'Pragma' in self.usefull_headers and self.usefull_headers['Pragma'] != "":
      show_info("Pragma: Pragma is useless since HTTP/1.1. Current value: '{}'".format(self.usefull_headers['Pragma']))
      self.score -= 5
    else:
      show_ok("Pragma is absent or empty. It'good. Pragma is useless since HTTP/1.1. ")

if __name__ == "__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('url', type=str, help="URL to check")
  parser.add_argument('-r', '--resolve',       required=False, help="Resolve domain:port to ip", type=str)
  parser.add_argument('-v', '--verbose',    required=False, help="Set to verbose", action="store_true")
  parser.add_argument('-q', '--quiet',    required=False, help="Set to quiet", action="store_true")

  parser.add_argument('-A', '--user-agent', required=False, help="User agent to use", type=str, default="HTTP Cache Analyzer")

  group_ip = parser.add_mutually_exclusive_group()
  group_ip.add_argument('-4', '--ipv4', required=False, help="Resolve in ipv4 only", action="store_true")
  group_ip.add_argument('-6', '--ipv6', required=False, help="Resolve in ipv6 only", action="store_true")
  args = parser.parse_args()

  hca = http_cache_analyzer()
  r = hca.request(args.url, options = vars(args))
  rr = hca.analyze()
  hca.results()

