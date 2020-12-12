
class section():
  name = ""
  results = []

  def __init__(self, name, results):
    self.name = name
    self.results = results

  def show_results(self):
    print("")
    print("{} {} {}".format('-' * 8, self.name, '-' * (80 - 2 - len(self.name))))
    #show_title(self.name)
    [item.show_entry() for item in self.results]
