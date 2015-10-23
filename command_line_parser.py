from optparse import OptionParser

parser = OptionParser()
parser.add_option("-H", "--host", type='string', dest='host', default='localhost',
                  help='Host to connect to. Defaults to localhost.')
(options, args) = parser.parse_args()

def get_host():
    return options.host
