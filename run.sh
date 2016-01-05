#!/bin/sh

RANKS=2

python run_streamer.py &
mpirun -n $RANKS python run_backend_event_listener.py &
mpirun -n $RANKS python run_backend_reducer.py &
python run_visualizer.py &
