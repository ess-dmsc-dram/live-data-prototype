from subprocess import call
import random
import time

control='control.py'

reducer_control = ['python', control, '-p', '10005', '-c', 'BackendMantidReducer']
generator_control = ['python', control, '-p', '10002', '-c', 'BraggPeakEventGenerator']

call(reducer_control + ['bin_parameters', '0.3,0.0001,5'])
a0 = 5.431
call(generator_control + ['unit_cell', '{} {} {}'.format(a0, a0, a0)])

a = a0
while True:
    a -= 0.0001*a
    call(generator_control + ['unit_cell', '{} {} {}'.format(a, a, a)])
    time.sleep(1)
