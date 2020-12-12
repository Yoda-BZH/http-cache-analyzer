

class result():
  rtype = None
  text = ""
  recommendation = None

  def __init__(self, rtype, text, recommendation = None):
    self.rtype = rtype
    self.text = text
    self.recommendation = recommendation

  def show_entry(self):
    prefix = "[??] "
    if self.rtype == "ok":
      prefix = "[OK] "
    elif self.rtype == "info":
      prefix = "[--] "
    elif self.rtype == "warning":
      prefix = "[!!] "
    elif self.rtype == "result":
      prefix = ""
    print("{}{}".format(prefix, self.text))
