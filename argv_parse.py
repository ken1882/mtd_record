from argparse import ArgumentParser
import _G

parser = ArgumentParser()
parser.add_argument("job",nargs='?')
parser.add_argument("-n", '--repeats', help='Repeat times')
parser.add_argument("-s", '--stage', help='Stage name to fight')
parser.add_argument("-i", '--index', default=0, type=int, help='Index, job-specific argument (Starting party index reverted)')
parser.add_argument("-j", '--jndex', default=0, type=int, help='Secondary index, job-specific argument (Target event index)')
parser.add_argument("-k", '--kndex', default=2, type=int, help='Third index, job-specific argument (fight difficulty)')
parser.add_argument("-w", '--wait', default=300, type=int, help='Wait duration between fights in seconds')
parser.add_argument("-b", '--battle-duration', default=0, type=int, help='Auto rematch duration in seconds, default=0 means until exhausted')

def load():
  args = parser.parse_args()
  _G.ARGV = args
  return args