
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn

from .result import result
from .section import section

default_scheme = "https://"

class analyzer():
  timeout = 30
  max_time = 30
  connect_timeout = 30

  meaningfull_headers = ['Age', 'Cache-Control', 'ETag', 'Expires', 'Last-Modified', 'Pragma']


  def __init__(self):
    self.options = {}
    self.response = None
    self.headers = {}
    self.usefull_headers = {}
    self.score = 50
    self.results = []
    self.current_results = []
    self.current_results_title = ""

  def get_results(self):
    return self.results

  def add_section(self, text):
    if len(self.current_results) > 0:
      self.results.append(
        section(
          self.current_results_title,
          self.current_results
        )
      )
      self.current_results = []

    self.current_results_title = text

  def add_result(self, result_type, text, recommendation = None):
    self.current_results.append(result(result_type, text, recommendation))

  def finalize_results(self):
    if self.current_results_title == "":
      print("ERROR, no section title previously defined !")
      return
    self.results.append(section(self.current_results_title, self.current_results))

  def show_results(self):
    if not self.results:
      print("ERROR, this hca has not been analyzed")
      return
    self.add_section("Final score")
    self.add_result("result", "Final score: {}/100".format(self.score))

    self.finalize_results()
    [section.show_results() for section in self.results]

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
    self.add_section("HTTP Query")

    """
    vars(args) is passing in **options
    since url is part of this list, remove it
    note: for subrequest (when using parser), url is already removed, hence the
          check
    """
    self.options = options['options']
    if 'url' in self.options:
      del(self.options['url'])

    urllib3_cn.allowed_gai_family = self.allowed_gai_family

    url = user_url
    scheme_token = url[:5]
    if scheme_token != "https" and scheme_token != "http:":
      url = "{}{}".format(default_scheme, url)

    request_headers = {
      'User-Agent': self.options['user_agent'],
    }

    self.add_result('ok', "Requesting url {}".format(url))
    self.response = requests.get(url, headers = request_headers)
    if self.response.status_code > 299:
      self.add_result('warning', "HTTP Status code is {}".format(self.response.status_code))
      self.score -= 40
    else:
      self.add_result('ok', "HTTP Status code is {}".format(self.response.status_code))

    if self.response.url.rstrip('/') != url.rstrip('/'):
      self.add_result('warning', "Request was redirected to {}".format(self.response.url))

    if len(self.response.history) > 0:
      redirect_strs = [url]
      for history in self.response.history:
        redirect_strs.append(history.url)
      redirect_strs.append(self.response.url)
      redirect_strs = " -> ".join(redirect_strs)
      self.add_result('warning', "Request was redirected: {}".format(redirect_strs))

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
    self.add_section("Cache systems")
    cache_system_found = False
    for header_name, header_data in public_cache_headers.items():
      #print("Trying {}".format(header_name))
      if header_name in self.response.headers:
        if 'provider' in header_data:
          self.add_result('ok', "Presence of header '{}': '{}'".format(header_name, self.response.headers[header_name]))
          self.add_result('ok', "A cache system is detected: {}".format(header_data['provider']))
          cache_system_found = True
        else:
          for key, header_test in header_data.items():
            if header_test['match'] in self.headers[header_name]:
              self.add_result('ok', "HTTP header '{}': '{}' is matching '{}'".format(header_name, self.headers[header_name], header_test['match']))
              self.add_result('ok', "A cache system is detected: {}".format(header_test['provider']))
              cache_system_found = True

    if cache_system_found == False:
      self.add_result('ok', "No caching system found")
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
    self.add_section("HTTP Header list")
    for key, value in self.headers.items():
      self.add_result('ok', "{}: {}".format(key, value))

    self.detect_public_cache()

    self.usefull_headers = self.filter_cache_headers()
    #print(self.headers)
    self.analyze_headers()

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
        #self.add_result('ok', "{} is in cache-control".format(cache_control_value))
        score_modifier += ccv_modifier
        if score_modifier > 0:
          self.add_result('ok', "Cache-Control has {}, adding {} points".format(cache_control_value, ccv_modifier))
        else:
          self.add_result('warning', "Cache-Control has {}, removing {} points".format(cache_control_value, ccv_modifier))

    for cache_control_value, ccv_modifier in cache_control_expirations.items():
      for token in tokens:
        if cache_control_value in token:
          (ccv, seconds) = token.split("=")
          self.add_result('ok', "Cache-Control: token '{}' has value '{}'.".format(ccv, str(seconds)))
          if int(seconds) <= 0:
            self.add_result('warning', "Cache-Control has {} value to 0 or lower, lowering the score by {}".format(ccv, ccv_modifier))
          else:
            self.add_result('ok', "Cache-Control has {} value to 0 or higher, adding {} points to the score".format(ccv, ccv_modifier))
            ccv_modifier = -ccv_modifier
          score_modifier += ccv_modifier

    return score_modifier

  def analyze_headers(self):

    """
    Age
    """
    self.add_section("Header Age")
    if 'Age' in self.usefull_headers:
      self.add_result('ok', "Age is present, current value: '{}'".format(str(self.usefull_headers['Age'])))
      self.score += 10
    else:
      self.add_result('ok', "Age is absent.")

    """
    Cache-Control
    """
    self.add_section("Header Cache-Control")
    if 'Cache-Control' in self.usefull_headers:
      self.add_result('ok', "Cache-Control ok, current value: '{}'".format(self.usefull_headers['Cache-Control']))
      self.score += 30
      self.score += self.analyze_header_cachecontrol(self.usefull_headers['Cache-Control'])
      #if 'Age' not in self.usefull_headers:
      #  self.add_result('warning', "But wait, age is not present ?")
    else:
      self.add_result('warning', "Cache-Control is absent. Default value is '{}', which deactivate all cache mecanismes".format('no-store, no-cache'))
      self.score -= 30

    """
    ETag
    """
    self.add_section("Header ETag")
    if 'ETag' in self.usefull_headers:
      etag = self.usefull_headers['ETag'].strip('"\'')
      etag_strs = ["ETag is present, current value: {}.".format(etag)]
      self.score += 10
      if etag[-5:] == "-gzip":
        self.score += 5
        etag_strs.append("Etag is gzipped, bonus points")
      self.add_result('ok', " ".join(etag_strs))

    else:
      etag_strs = ["ETag is absent."]
      if 'Cache-Control' in self.usefull_headers:
        etag_strs.append("But it's ok, Cache-Control can be used too.")
        self.add_result('ok', " ".join(etag_strs))
      else:
        etag_strs.append("Cache-Control is absent too. No cache can be made.")
        self.add_result('warning', " ".join(etag_strs))
        self.score -= 10

    """
    Expires
    """
    self.add_section("Header Expires")
    if 'Expires' in self.usefull_headers:
      if 'Cache-Control' in self.usefull_headers:
        self.add_result('ok', "Expires is present, but it's value '{}' is ignored since Cache-Control is present".format(self.usefull_headers['Expires']))
      else:
        self.add_result('ok', "Expires ok, '{}'".format(self.usefull_headers['Expires']))
        self.score += 5
    else:
      if 'Cache-Control' in self.usefull_headers:
        self.add_result('ok', "Expires is absent, but Cache-Control is present, which is good.")
      else:
        self.add_result('ok', "Expires is absent. It's ok")

    """
    Last-Modified
    """
    self.add_section("Header Last-Modified")
    if 'Last-Modified' in self.usefull_headers:
      self.add_result('ok', "Last-Modified is present, current value: '{}'".format(self.usefull_headers['Last-Modified']))
      self.score += 5
    else:
      self.add_result('ok', "Last-Modified is absent, it's okay")

    """
    Pragma
    """
    self.add_section("Header Pragma")
    if 'Pragma' in self.usefull_headers and self.usefull_headers['Pragma'] != "":
      self.add_result('ok', "Pragma: Pragma is useless since HTTP/1.1. Current value: '{}'".format(self.usefull_headers['Pragma']))
      self.score -= 5
    else:
      self.add_result('ok', "Pragma is absent or empty. It's good. Pragma is useless since HTTP/1.1. ")

    self.add_section("Cookie")
    if 'Set-Cookie' in self.headers:
      self.add_result('warning', "Cookies are being defined. This may deactivates caching capabilities: '{}'".format(self.headers['Set-Cookie']))
      self.score -= 30
    else:
      self.add_result('ok', "No cookie defined.")

