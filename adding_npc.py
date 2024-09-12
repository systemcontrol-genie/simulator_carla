import carla 
import random

client = carla.Client('localhost', 2000)
world = client.get_world()
vehicle_blueprint = world.get_blueprint_library().filter('*vehicle*')
spawn_points = world.get_map().get_spawn_points()

for i in range(0, 50):
    world.try_spawn_actor(random.choice(vehicle_blueprint), random.choice(spawn_points))