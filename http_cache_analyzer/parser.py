
from .analyzer import analyzer
import bs4

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
    #self.soup = bs4.BeautifulSoup(response.text, "html.parser")
    self.soup = bs4.BeautifulSoup(parent_hca.response.text, self.bs_parser)

  def parse(self):
    self.find_css()
    self.find_js()
    self.find_images()
    """
    fonts are mainly loaded by css
    todo: parse css, extract images + fonts, add the to corresponding lists
    """
    #self.find_fonts()

    for elemtype in self.elem_types:
      if elemtype not in self.hcas:
        self.hcas[elemtype] = []

      if elemtype in self.assets:
        for elem in self.assets[elemtype]:
          if elem[0:2] == '//' or elem[:4] == 'http':
            #print("Skipping {}".format(elem))
            continue
          elem_analyzer = analyzer()
          url = "{}{}".format(self.parent_hca_url, elem.lstrip('/'))
          elem_analyzer.request(url, options = self.parent_hca_options)
          elem_analyzer.analyze()
          elem_analyzer.finalize_results()
          self.hcas[elemtype].append(elem_analyzer)

  def show_results(self):
    for elemtype in self.hcas:
      averages_for_type = []
      for elem in self.hcas[elemtype]:
        averages_for_type.append(elem.score)
      avg_type = (sum(averages_for_type) / len(averages_for_type))
      min_type = min(averages_for_type)
      max_type = max(averages_for_type)

      print("Average score for {}: {}, min: {}, max: {}".format(elemtype, avg_type, min_type, max_type))
      if min_type != avg_type:
        print("worse {} stats:".format(elemtype))
        for elem in self.hcas[elemtype]:
          if elem.score != min_type:
            continue
          elem.show_results()

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
        #r[elemtype] = [{hca.response.url: hca.get_results()} for hca in self.hcas[elemtype]]
    return r

  #def find_fonts(self):
  #  pass