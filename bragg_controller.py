import zmq
import sys
import argparse

from parameter_control_client import ParameterControlClient
from general_parameter_controller import GeneralParameterController

HOST = 'localhost'
PORT = 10002

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--list-parameters', action='store_true',
                    help='Show a list of available parameters and their types.')
parser.add_argument('-c', '--controllee', type=str, default='BraggPeakEventGenerator', help='Specify controllee.')
parser.add_argument('parameter_name', nargs='?', help='Name of parameter to set.')
parser.add_argument('parameter_value', nargs='?', help='New parameter value.')

args = parser.parse_args()


control_client = ParameterControlClient(HOST, PORT)
controller = GeneralParameterController(control_client)

if args.list_parameters:
    controller.print_available_parameters()

if args.parameter_name:
    if args.parameter_value:
        print controller.set_parameter_value(args.controllee, args.parameter_name, args.parameter_value)
    else:
        print controller.get_parameter_value(args.controllee, args.parameter_name)

else:
    controller.print_current_values()