
from .analyzer import analyzer
import bs4
import urllib
import os

class parser:
  parent_hca_url = ""
  parent_hca_content = ""
  parent_hca_options = {}
  assets = {}
  soup = None
  #bs_parser = "html.parser"
  #bs_parser = "lxml"
  bs_parser = "html5lib"
  elem_types = ['css', 'js', 'images']

  def __init__(self, parent_hca):
    self.hcas = {}
    self.parent_hca_url = parent_hca.response.url
    self.parent_hca_options = parent_hca.options
    self.soup = bs4.BeautifulSoup(parent_hca.response.text, self.bs_parser)

  def parse(self):
    self.find_css()
    self.find_js()
    self.find_images()
    """
    fonts are mainly loaded by css
    todo: parse css, extract images + fonts, add the to corresponding lists
          problem, unable to know which css rules are actually applied.
    """
    #self.find_fonts()

    url_tokens = urllib.parse.urlparse(self.parent_hca_url)
    url_tokens_path = url_tokens.path
    if url_tokens_path[-1] != '/' and url_tokens_path != '/':
      url_tokens_path = os.path.dirname(url_tokens_path)
    baseurl_main = '{}://{}'.format(url_tokens.scheme, url_tokens.netloc)
    baseurl_dir = '{}://{}{}'.format(url_tokens.scheme, url_tokens.netloc, url_tokens_path).rstrip('/')

    for elemtype in self.elem_types:
      if elemtype not in self.hcas:
        self.hcas[elemtype] = []

      if elemtype in self.assets:
        for elem in self.assets[elemtype]:
          if elem[0:2] == '//' or elem[:4] == 'http':
            continue
          elem_analyzer = analyzer()
          if elem[0] == '/':
            url = "{}/{}".format(baseurl_main, elem.lstrip('/'))
          else:
            url = "{}/{}".format(baseurl_dir, elem.lstrip('/'))
          #url = "{}{}".format(baseurl, elem.lstrip('/'))
          elem_analyzer.request(url, options = self.parent_hca_options)
          elem_analyzer.analyze()
          elem_analyzer.finalize_results()
          self.hcas[elemtype].append(elem_analyzer)

  def show_results(self):
    assets_size = 0
    for elemtype in self.hcas:
      averages_for_type = []
      if not self.hcas[elemtype]:
        print("No {} element, skipping".format(elemtype))
        continue
      for elem in self.hcas[elemtype]:
        averages_for_type.append(elem.score)
        assets_size += elem.document_size
      avg_type = (sum(averages_for_type) / len(averages_for_type))
      min_type = min(averages_for_type)
      max_type = max(averages_for_type)

      print("Average score for {}: {}, min: {}, max: {}".format(elemtype, round(avg_type, 2), round(min_type, 2), round(max_type, 2)))
      if min_type != avg_type:
        print("Worst {} stats:".format(elemtype))
        for elem in self.hcas[elemtype]:
          """
          skip all non-lowest scores results
          """
          if elem.score != min_type:
            continue
          elem.show_results()
          """
          show only the first worst assets of this type
          if several assets have the same score, all of them will be displayed
          """
          break

    assets_format = 'bytes'
    if assets_size < 1048576: # 1024 * 1024
      assets_size /= 1024
      assets_format = 'kilobytes'
    elif assets_size < 1073741824: # 1024 * 1024 * 1024
      assets_size /= 1048576
      assets_format = 'megabytes'
    else:
      assets_size /= 1073741824
      assets_format = 'gigabytes'
    print("All assets size: {} {}".format(round(assets_size, 2), assets_format))

  def find_css(self):
    css = self.soup.find_all("link", {"rel": "stylesheet"})
    self.assets['css'] = [item.get("href") for item in css]

  def find_js(self):
    js = self.soup.find_all('script', {"src": True})
    self.assets['js'] = [item.get('src') for item in js]

  def find_images(self):
    imgs = self.soup.find_all('img', {"src": True})
    self.assets['images'] = [item.get('src') for item in imgs]

  def get_results(self):
    r = {}
    for elemtype in self.elem_types:
      r[elemtype] = {}
      if elemtype in self.hcas:
        for hca in self.hcas[elemtype]:
          r[elemtype].update({hca.response.url: hca.get_results()})
    return r

  #def find_fonts(self):
  #  pass
