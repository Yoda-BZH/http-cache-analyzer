
import json
from .section import section
from .result import result

class jsonencoder(json.JSONEncoder):
  def default(self, o):
    if isinstance(o, section):
      return o.default()
    if isinstance(o, result):
      return o.default()
    raise Exception("Unable to JSONEncode object to type {}".format(type(o)))
