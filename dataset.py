import vrplib
import os


def load_cvrp_dataset(dataset_path: str) -> dict:
    cvrp_dataset = {}
    cvrp_dataset['B'] = {}

    for file in os.listdir(dataset_path):
        if file.endswith(".vrp"):
            instances = vrplib.read_instance(os.path.join(dataset_path, file))
            cvrp_dataset['B'][file[:-4]] = instances

    return cvrp_dataset
