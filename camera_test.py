import carla
import math
import random
import time
import numpy as np
import cv2

client = carla.Client('localhost', 2000)
world = client.get_world()

bp_lib = world.get_blueprint_library()
spawn_points = world.get_map().get_spawn_points()

vehicle_bp  = bp_lib.find('vehicle.lincoln.mkz_2020')
vehicle = world.try_spawn_actor(vehicle_bp, random.choice(spawn_points))

spectator = world.get_spectator()
transform = carla.Transform(vehicle.get_transform().transform(carla.Location(x=-4, z = 2)), vehicle.get_transform().rotation)
spectator.set_transform(transform)

for i in range(10):
    vehicle_bp = random.choice(bp_lib.filter('vehicle'))
    npc = world.try_spawn_actor(vehicle_bp, random.choice(spawn_points))

#print sensor type
for bp in bp_lib.filter('sensor'):
    print(bp.id)
# npc autopilot TURE
for v in world.get_actors().filter("*vehicle*"):
    v.set_autopilot(True)

camera_init_trans = carla.Transform(carla.Location(z=2))
camera_bp = bp_lib.find("sensor.camera.rgb")
camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to = vehicle)

sem_camera_bp = bp_lib.find("sensor.camera.semantic_segmentation")
sem_camera = world.spawn_actor(sem_camera_bp, camera_init_trans, attach_to = vehicle)

inst_camera_bp = bp_lib.find("sensor.camera.instance_segmentation")
inst_camera = world.spawn_actor(inst_camera_bp, camera_init_trans, attach_to = vehicle)

depth_camera_bp = bp_lib.find("sensor.camera.depth")
depth_camera = world.spawn_actor(depth_camera_bp, camera_init_trans, attach_to = vehicle)

dvs_camera_bp = bp_lib.find("sensor.camera.dvs")
dvs_camera = world.spawn_actor(dvs_camera_bp, camera_init_trans, attach_to = vehicle)

opt_camera_bp = bp_lib.find('sensor.camera.optical_flow')
opt_camera = world.spawn_actor(opt_camera_bp, camera_init_trans, attach_to = vehicle)

def rgb_callback(image , data_dict):
    data_dict['rgb_image'] = np.reshape(np.copy(image.raw_data), (image.height, image.width , 4))

def sem_callback(image, data_dict):
    image.convert(carla.ColorConverter.CityScapesPalette)
    data_dict['sem_image'] = np.reshape(np.copy(image.raw_data), (image.height, image.width , 4))

def inst_callback(image, data_dict):
    data_dict['inst_image'] = np.reshape(np.copy(image.raw_data), (image.height, image.width , 4))


def depth_callback(image, data_dict):
    image.convert(carla.ColorConverter.LogarithmicDepth)
    data_dict['depth_image'] = np.reshape(np.copy(image.raw_data), (image.height, image.width , 4))

def opt_callback(data, data_dict):
    # 광학 흐름 데이터를 색상 코딩된 이미지로 변환
    image = data.get_color_coded_flow()

    # raw_data를 복사하고, 이미지의 (높이, 너비, 4채널)로 재구성 (4채널은 RGB + 알파)
    img = np.reshape(np.copy(image.raw_data), (image.height, image.width, 4))

    # 알파 채널(투명도)을 255로 설정하여 완전히 불투명하게 만듦
    img[:, :, 3] = 255

    # 광학 흐름 데이터를 정규화하여 0~255 범위로 맞추기 (시각적으로 잘 보이게)
    img_norm = cv2.normalize(img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8U)

    # 'opt_image'라는 키로 데이터 딕셔너리에 저장
    data_dict['opt_image'] = img_norm


def dev_callback(data, data_dict):
    dev_event= np.frombuffer(data.raw_data, dtype= np.dtype([('x', np.uint16) , ('y',np.uint16),('t', np.int64), ('pool', np.bool_)]))
    data_dict['dev_image'] = np.zeros((data.height , data.width  , 4), dtype= np.uint8)
    dvs_img = np.zeros((data.height ,data.width , 3), dtype=np.uint8)
    dvs_img[dev_event[:]['y'], dev_event[:]['x'], dev_event[:]['pool']*2]=255
    data_dict['dev_image'][:,:,0:3] = dvs_img

image_w = camera_bp.get_attribute("image_size_x").as_int()
image_h = camera_bp.get_attribute("image_size_y").as_int()

sensor_data = {'rgb_image': np.zeros((image_h, image_w , 4)),
               'sem_image': np.zeros((image_h, image_w, 4)),
               'depth_image': np.zeros((image_h, image_w, 4)),
               'opt_image' : np.zeros((image_h, image_w, 4)),
               'dev_image' : np.zeros((image_h, image_w, 4)),
               'inst_image' : np.zeros((image_h, image_w, 4))
               }
cv2.namedWindow('all_camera', cv2.WINDOW_AUTOSIZE)

top_row = np.concatenate((sensor_data['rgb_image'], sensor_data['sem_image'], sensor_data["depth_image"]),axis=1)
lower_row = np.concatenate((sensor_data['opt_image'], sensor_data['dev_image'], sensor_data['inst_image']), axis=1)
tiled = np.concatenate((top_row, lower_row),axis=0)

cv2.imshow('all_camera', tiled)
cv2.waitKey()

camera.listen(lambda image : rgb_callback(image , sensor_data))
sem_camera.listen(lambda image: sem_callback(image , sensor_data))
inst_camera.listen(lambda image : inst_callback(image, sensor_data))
depth_camera.listen(lambda image: depth_callback(image , sensor_data))
dvs_camera.listen(lambda image: dev_callback(image, sensor_data))
opt_camera.listen(lambda image: opt_callback(image, sensor_data))

while True:

    top_row = np.concatenate((sensor_data['rgb_image'], sensor_data['sem_image'], sensor_data["depth_image"]), axis=1)
    lower_row = np.concatenate((sensor_data['opt_image'], sensor_data['dev_image'], sensor_data['inst_image']), axis=1)
    tiled = np.concatenate((top_row, lower_row),axis=0)
    cv2.imshow('all_camera', tiled)

    if cv2.waitKey(1) == ord('q'):
        break

camera.stop()
sem_camera.stop()
inst_camera.stop()
depth_camera.stop()
dvs_camera.stop()
opt_camera.stop()
