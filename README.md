Running
-------
The live data prototype consists of several python scripts that run independently (and communicate via ZeroMQ). Certain aspects (typically parameters) of these components can be controlled via a ZeroMQ interface.

There are 4 main components that need to be started:

- Streamer (generates fake event data)
- Backend-live-listener (reads event stream, distributes it to all MPI ranks, and buffers event data)
- Backend-reducer (reads data from live-listener and runs Mantid-based data reduction)
- Visualizer (lightweight visualization of reduciton result)

The respective commands are:

**Streamer:**
```sh
python run_streamer.py
```

**Backend-live-listener:**
```sh
mpirun -n <N> python run_backend_event_listener.py
```
where `<N>` is the desired number of MPI ranks. `mpirun -n <N>` can be omitted to run only with a single process.

**Backend-reducer:**
```sh
mpirun -n <N> python run_backend_reducer.py
```
where `<N>` is the desired number of MPI ranks. It *must* match the number of ranks used for the backend-live-listener.

**Visualizer:**
```sh
python run_visualizer.py
```

In all four cases the run script supports the option `-h` to print help, and further options, as described in the respective help. In particular, in several cases you can set the log level with `-l` and the host with `-H` (which defaults to localhost).

**Control while running:**

...is possible with the script `control.py`. The components described above listen for commands via ZeroMQ on various ports (streamer on 10002, backend-reducer on 10004 and 10005).

Usage example:
```sh
# Query server for available controllees and commands
python control.py -p <PORT>
# Example usage for setting the bin size for the backend-reducer
python control.py -p 10005 -c BackendMantidReducer bin_parameters '0.4,0.001,5'
```


Running the unit tests
----------------------
```sh
python -m unittest discover tests
```
or for individual modules
```sh
python -m unittest discover tests.test_backend
```
