import argparse

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-H", "--host", type=str, default='localhost', help='Host to connect to.')
args = parser.parse_args()

def get_host():
    return args.host
