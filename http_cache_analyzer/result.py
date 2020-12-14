

class result():
  rtype = None
  text = ""
  recommendation = None

  def __init__(self, rtype, text, recommendation = None, score = 0):
    self.rtype = rtype
    self.text = text
    self.recommendation = recommendation
    self.score = score

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
    s = "{}{}.".format(prefix, self.text.rstrip('.'))

    if self.rtype in ['ok', 'warning']:
      #if self.score == 0:
      #  s += " This does not affect the final score."
      #else:
      if self.score != 0:
        s += " This affets the score by {}".format(self.score)
    print(s)

  def default(self):
    return {'type': self.rtype, 'text': self.text, 'recommendation': self.recommendation}
