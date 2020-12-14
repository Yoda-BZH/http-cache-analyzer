
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn

from .result import result
from .section import section

default_scheme = "https://"

class score():
  http_code = 30
  transfer_speed = 20
  cache_control_must_revalidate = -1
  cache_control_must_no_cache = -20
  cache_control_must_no_store = -20
  cache_control_must_no_transform = 5
  cache_control_public = 5
  cache_control_private = -5
  cache_control_proxy_revalidate = -5
  cache_control_max_age = 5
  cache_control_s_maxage = 5
  age = 10
  etag = 10
  expires = 5
  last_modified = 10
  pragma = -5
  no_cookies = 30

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
    self.score = 0
    self.results = []
    self.current_results = []
    self.current_results_title = ""
    self.elapsed_ms = []
    self.document_size = 0
    self.cache_control_values_single = {
      "must-revalidate": score.cache_control_must_revalidate,
      "no-cache": score.cache_control_must_no_cache,
      "no-store": score.cache_control_must_no_store,
      "no-transform": score.cache_control_must_no_transform,
      "public": score.cache_control_public,
      "private": score.cache_control_private,
      "proxy-revalidate": score.cache_control_proxy_revalidate,
    }
    self.cache_control_expirations = {
      "max-age=": score.cache_control_max_age,
      "s-maxage=": score.cache_control_s_maxage,
    }

  def get_results(self):
    r = {
      'score': self.score,
      'url': self.response.url,
      'headers': dict(self.headers),
      'http_code': self.response.status_code,
      'is_redirected': len(self.response.history) > 0,
      'elapsed_ms': self.convert_timedeleta_to_ms(self.response.elapsed.microseconds)
    }
    results_flattened = {}
    for i in self.results:
      results_flattened.update(i.default())
    r['results'] = results_flattened
    return r

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

  def add_result(self, result_type, text, recommendation = None, score = 0):
    self.current_results.append(result(result_type, text, recommendation, score))
    self.score += score

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

    self.add_result('info', "Requesting url {}".format(url))
    self.response = requests.get(url, headers = request_headers)
    if self.response.status_code > 299:
      self.add_result('warning', "HTTP Status code is {}".format(self.response.status_code))
    else:
      self.add_result('ok', "HTTP Status code is {}".format(self.response.status_code), score = score.http_code)

    if self.response.url.rstrip('/') != url.rstrip('/'):
      self.add_result('warning', "Request was redirected to {}".format(self.response.url))

    self.elapsed_ms.append(self.convert_timedeleta_to_ms(self.response.elapsed.microseconds))

    if len(self.response.history) > 0:
      redirect_strs = [url]
      for history in self.response.history:
        redirect_strs.append(history.url)
        self.elapsed_ms.append(self.convert_timedeleta_to_ms(history.elapsed.microseconds))
      redirect_strs.append(self.response.url)
      redirect_strs = " -> ".join(redirect_strs)
      self.add_result('warning', "Request was redirected: {}".format(redirect_strs))

    total_elapsed = sum(self.elapsed_ms)
    if total_elapsed < 500:
      self.add_result('ok', 'The request took {} ms'.format(total_elapsed), score = score.transfer_speed)
    else:
      self.add_result('warning', 'The request took {} ms, this is too long'.format(total_elapsed))

    """
    check for the request length
    """
    if 'Content-Length' in self.response.headers:
      data_length = int(self.response.headers['Content-Length'])
    else:
      data_length = len(self.response.text)
    self.document_size = data_length

    data_length_format = 'bytes'
    if data_length < 1048576: # 1024 * 1024
      data_length /= 1024
      data_length_format = 'kilobytes'
    elif data_length < 1073741824:
      data_length /= 1048576
      data_length_format = 'megabytes'
    else:
      data_length /= 1073741824
      data_length_format = 'gigabytes'
    self.add_result('info', 'Document size: {} {}'.format(round(data_length, 2), data_length_format))
    #print("content length: {}, raw length: {}".format(self.response.headers['Content-Length'], len(self.response.text)))

    return self.response

  def convert_timedeleta_to_ms(self, value):
    return round(value / 1000)

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
      self.add_result('info', "No caching system found")
    else:
      self.add_result('info', "A cache system was found", score = 20)

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
      self.add_result('info', "{}: {}".format(key, value))

    self.detect_public_cache()

    self.usefull_headers = self.filter_cache_headers()
    self.analyze_headers()

  def analyze_header_cachecontrol(self, cachecontrol):

    tokens = cachecontrol.split(', ')

    has_private = False
    has_public = False
    for cache_control_value, ccv_modifier in self.cache_control_values_single.items():
      if cache_control_value in tokens:
        #self.add_result('ok', "{} is in cache-control".format(cache_control_value))
        if cache_control_value == 'private':
          has_private = True
        if cache_control_value == 'public':
          has_public = True

        if ccv_modifier > 0:
          self.add_result('ok', "Cache-Control has {}".format(cache_control_value), score = ccv_modifier)
        else:
          self.add_result('warning', "Cache-Control has {}".format(cache_control_value), score = ccv_modifier)

    if has_private and has_public:
      self.add_result('warning', "Cache-Control has bot '{}' and '{}'. In this situation, only '{}' is kept !".format('private', 'public', 'private'))

    for cache_control_value, ccv_modifier in self.cache_control_expirations.items():
      for token in tokens:
        if cache_control_value in token:
          (ccv, seconds) = token.split("=")
          self.add_result('info', "Cache-Control: token '{}' has value '{}'.".format(ccv, str(seconds)))
          if int(seconds) <= 0:
            self.add_result('warning', "Cache-Control has {} value to 0 or lower".format(ccv))
          else:
            self.add_result('ok', "Cache-Control has {} value to 0 or higher".format(ccv), score = ccv_modifier)

  def analyze_headers(self):

    """
    Age
    """
    self.add_section("Header Age")
    if 'Age' in self.usefull_headers:
      self.add_result('ok', "Age is present, current value: '{}'".format(str(self.usefull_headers['Age'])), score = score.age)
    else:
      self.add_result('info', "Age is absent.")

    """
    Cache-Control
    """
    self.add_section("Header Cache-Control")
    if 'Cache-Control' in self.usefull_headers:
      self.add_result('ok', "Cache-Control ok, current value: '{}'".format(self.usefull_headers['Cache-Control']))
      self.analyze_header_cachecontrol(self.usefull_headers['Cache-Control'])
      #if 'Age' not in self.usefull_headers:
      #  self.add_result('warning', "But wait, age is not present ?")
    else:
      self.add_result('warning', "Cache-Control is absent. Default value is '{}', which deactivate all cache mecanismes".format('no-store, no-cache'))

    """
    ETag
    """
    self.add_section("Header ETag")
    if 'ETag' in self.usefull_headers:
      etag = self.usefull_headers['ETag'].strip('"\'')
      self.add_result('ok', "ETag is present, current value: {}.".format(etag), score = score.etag)
      if 'Cache-Control' not in self.usefull_headers:
        self.add_result('info', 'Cache-Control is not used, but Etag is.')

    else:
      etag_strs = ["ETag is absent."]
      if 'Cache-Control' in self.usefull_headers:
        etag_strs.append("But it's ok, Cache-Control can be used too.")
        self.add_result('ok', " ".join(etag_strs))
      else:
        etag_strs.append("Cache-Control is absent too. No cache can be made.")
        self.add_result('warning', " ".join(etag_strs))

    """
    Expires
    """
    self.add_section("Header Expires")
    if 'Expires' in self.usefull_headers:
      if 'Cache-Control' in self.usefull_headers:
        self.add_result('ok', "Expires is present, but it's value '{}' is ignored since Cache-Control is present".format(self.usefull_headers['Expires']))
      else:
        self.add_result('ok', "Expires ok, '{}'".format(self.usefull_headers['Expires']), score = score.expires)
    else:
      if 'Cache-Control' in self.usefull_headers:
        self.add_result('ok', "Expires is absent, but Cache-Control is present, which is good.")
      else:
        self.add_result('info', "Expires is absent. It's ok")

    """
    Last-Modified
    """
    self.add_section("Header Last-Modified")
    if 'Last-Modified' in self.usefull_headers:
      self.add_result('ok', "Last-Modified is present, current value: '{}'".format(self.usefull_headers['Last-Modified']), score = score.last_modified)
    else:
      self.add_result('info', "Last-Modified is absent, it's okay")

    """
    Pragma
    """
    self.add_section("Header Pragma")
    if 'Pragma' in self.usefull_headers and self.usefull_headers['Pragma'] != "":
      self.add_result('ok', "Pragma: Pragma is useless since HTTP/1.1. Current value: '{}'".format(self.usefull_headers['Pragma']), score = score.pragma)
    else:
      self.add_result('ok', "Pragma is absent or empty. It's good. Pragma is useless since HTTP/1.1. ")

    """
    cookies
    """
    self.add_section("Cookie")
    if 'Set-Cookie' in self.headers:
      self.add_result('warning', "Cookies are being defined. This may deactivates caching capabilities: '{}'".format(self.headers['Set-Cookie']))
    else:
      self.add_result('ok', "No cookie defined.", score = score.no_cookies)

