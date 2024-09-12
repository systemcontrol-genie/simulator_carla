try:
    import carla
except ModuleNotFoundError:
    print("carla not install, pip install carla")

import random

client = carla.Client('localhost', 2000)
client.load_world('Town05') #change_world
world = client.get_world()