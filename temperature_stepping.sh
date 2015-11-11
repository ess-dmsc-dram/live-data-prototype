#!/bin/sh

python control.py -p 10005 -c BackendMantidReducer bin_parameters '0.4,0.0001,5'

for i in $(seq 0.001 0.001 0.01)
do
  python control.py -p 10002 -c BraggPeakEventGenerator relative_peak_width $i
  python control.py -p 10005 -c BackendMantidReducer next True
  sleep 10
done
