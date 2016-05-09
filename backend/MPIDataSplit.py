

def determine_data_split(index, num_processes):
    target = index % num_processes
    return target

