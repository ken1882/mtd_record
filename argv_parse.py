from argparse import ArgumentParser
import _G

parser = ArgumentParser()
parser.add_argument("job",nargs='?')
parser.add_argument("-i", '--index', default=0, type=int, help='Index, job-specific argument (character col index)')
parser.add_argument("-a", '--all', action='store_true', default=False, help='Record all scenes')
parser.add_argument("-n", '--number', default=0, type=int, help='Character number to record')
parser.add_argument("-s", '--skip-name', action='store_true', default=False, help='Skip character name ocr')

def load():
  args = parser.parse_args()
  _G.ARGV = args
  return args