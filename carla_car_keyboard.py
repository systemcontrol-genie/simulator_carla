import glob
import os
import sys
import time
import random

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' %(
        sys.version_info.major, 
        sys.version_info.minor,
        "win-amd64" if os.name == 'nt' else 'linux-x86_64'))[0])
except:
    pass

import carla
import weakref

try:
    import pygame
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_SPACE
    from pygame.locals import K_a
    from pygame.locals import K_d
    from pygame.locals import K_s
    from pygame.locals import K_w

except ImportError:
    raise RuntimeError("cannot import pygame, make sure pygame package is installed")

try:
    import numpy as np
except ImportError:
    raise RuntimeError("cannot import numpy, make sure numpy package is installed")


view_width = 640
view_height = 460
view_fov = 90

class BaisicClient(object):

    def __init__(self):
        self.client = None
        self.world = None
        self.camera = None
        self.car = None
        self.display = None
        self.image = None
        self.capture = True
    
    def camera_blueprint(self):
        camera_bp = self.world.get_blueprint_library().find("sensor.camera.rgb")
        camera_bp.set_attribute('image_size_x', str(view_width))
        camera_bp.set_attribute('image_size_y', str(view_height))
        camera_bp.set_attribute('fov', str(view_fov))
        return camera_bp
    
    def set_synchronous_mode(self, synchronous_mode):
        settings = self.world.get_settings()
        settings.synchronous_mode = synchronous_mode
        self.world.apply_settings(settings)
    
    def setup_car(self):
        car_bp = self.world.get_blueprint_library().filter('vehicle.*')[0]
        location = random.choice(self.world.get_map().get_spawn_points())
        self.car = self.world.spawn_actor(car_bp, location)
    
    def setup_camera(self):
        camera_transform = carla.Transform(carla.Location(x=-5.5, z=2.8), carla.Rotation(pitch=-15))
        self.camera = self.world.spawn_actor(self.camera_blueprint(), camera_transform, attach_to=self.car)
        weak_self = weakref.ref(self)
        self.camera.listen(lambda image: weak_self().set_image(weak_self, image))
        calibration = np.identity(3)
        calibration[0,2] = view_width/2.0
        calibration[1,2] = view_height/2.0
        calibration[0,0] = calibration[1,1] = view_width /(2.0 * np.tan(view_fov * np.pi /360.0))
        self.camera.calibration = calibration

    def control(self, car):
        keys = pygame.key.get_pressed()

        if keys [K_ESCAPE]:
            return True
        
        control = car.get_control()
        control.throttle = 0

        if keys[K_w]:
            control.throttle = 1
            control.reverse = False
        elif keys[K_s]:
            control.throttle = 1
            control.reverse = True
        
        if keys[K_a]:
            control.steer = max(-1, min(control.steer - 0.05, 0))
        elif keys[K_d]:
            control.steer = min(1. , max(control.steer + 0.05, 0))
        else:
            control.steer = 0
        control.hand_brake = keys[K_SPACE]

        car.apply_control(control)
        return False
    @staticmethod

    def set_image(weak_self, img):
        self = weak_self()
        if self.capture:
            self.image = img
            self.capture = False
    
    def render(self, display):
        if self.image is not None:
            array = np.frombuffer(self.image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (self.image.height, self.image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
            display.blit(surface, (0, 0))

    def game_loop(self):
        try:
            pygame.init()

            self.client = carla.Client('127.0.0.1', 2000)
            self.client.set_timeout(2.0)
            self.world = self.client.get_world()

            self.setup_car()
            self.setup_camera()

            self.display = pygame.display.set_mode((view_width, view_height), pygame.HWSURFACE | pygame.DOUBLEBUF)
            pygame_clock = pygame.time.Clock()

            self.set_synchronous_mode(True)
            vehicles = self.world.get_actors().filter('vehicle.*')
            while True:
                self.world.tick()
                self.capture = True
                pygame_clock.tick_busy_loop(25)

                self.render(self.display)
                pygame.display.flip()
                pygame.event.pump()

                if self.control(self.car):
                    return
        finally:
            self.set_synchronous_mode(False)
            self.camera.destroy()
            self.car.destroy()
            pygame.quit()

def main():
    try:
        client = BaisicClient()
        client.game_loop()
    finally:
        print("exit")

if __name__ == "__main__":
    main()




