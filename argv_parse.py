from argparse import ArgumentParser
import _G

parser = ArgumentParser()
parser.add_argument("job",nargs='?')
parser.add_argument("-a", '--all', action='store_true', default=False, help='Record all scenes')

def load():
  args = parser.parse_args()
  _G.ARGV = args
  return args