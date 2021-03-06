from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
from glob import glob

import cv2
import matplotlib.pyplot as plt
import numpy as np

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import backend as K
from utils import non_max_suppression, get_all_bboxes
from dataset import YoloV1Generator
from model import yolov1

######################################
# Set GPU
######################################
os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = '1'


######################################
# Set GPU Memory
######################################
gpus = tf.config.experimental.list_physical_devices('GPU')
print(gpus)
# if gpus:
#   try:
#     tf.config.experimental.set_virtual_device_configuration(
#         gpus[0],
#         [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=10240)])
#   except RuntimeError as e:
#     print(e)


##################################
# Variables
##################################
"""
S is split size of image (in paper 7),
B is number of boxes (in paper 2),
C is number of classes (in paper and VOC dataset is 20),
"""
S = 7
B = 2
C = 20

input_shape = (448, 448, 3)
output_shape = (S, S, C + (B * 5))

batch_size = 1
model_name = 'yolo_v1'

# path variables
cur_dir = os.getcwd()
save_model_dir = os.path.join(cur_dir, "saved_models/2021-05-26 20:13:02")
data_dir = "/home/fssv2/myungsang/Datasets/voc_2012/yolo_format/train_val"
# data_dir = "/home/fssv2/myungsang/deep_learning/yolo_implementation/sample_data/data"
obj_name_path = "/home/fssv2/myungsang/Datasets/voc_2012/yolo_format/voc.names"

##################################
# Get Dataset Generator
##################################
jpg_data_list = glob(data_dir + "/*.jpg")

test_generator = YoloV1Generator(data_dir,
                                 input_shape=input_shape,
                                 batch_size=batch_size,
                                 augment=False,
                                 shuffle=False)

with open(obj_name_path, 'r') as f:
    obj_name_list = f.readlines()
obj_name_list = [data.strip() for data in obj_name_list]
print(obj_name_list)


##################################
# Get model
##################################
# Get trained model
# model_dir_list = glob(save_model_dir + "/*")
# model_dir = model_dir_list[0]
model_list = glob(save_model_dir + "/*")
model_list = sorted(model_list)
best_model = model_list[-1]
print("Best Model Name: {}".format(best_model))
# model = keras.models.load_model(best_model, compile=False)
model = yolov1((448, 448, 3), (7, 7, 30))
model.load_weights("./saved_models/2021-06-11 18:34:25/yolo_v1_00411.h5")



##################################
# Get bbox img function
##################################
import cv2
def get_bbox_img(img_path, bboxes, class_name_list):
    img = cv2.imread(img_path)
    width = img.shape[1]
    height = img.shape[0]
    for bbox in bboxes:
        class_name = class_name_list[int(bbox[0])]
        confidence_score = bbox[1]
        x = bbox[2]
        y = bbox[3]
        w = bbox[4]
        h = bbox[5]
        xmin = int((x - (w / 2)) * width)
        ymin = int((y - (h / 2)) * height)
        xmax = int((x + (w / 2)) * width)
        ymax = int((y + (h / 2)) * height)

        img = cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color=(0, 0, 255))
        img = cv2.putText(img, "{}, {}".format(class_name, confidence_score), (xmin, ymin - 10),
                          fontFace=cv2.FONT_ITALIC,
                          fontScale=1,
                          color=(0, 0, 0))
    return img


##################################
# Inference
##################################
import time
cv2.namedWindow("Test")
cv2.resizeWindow("Test", 1080, 720)
for idx in range(test_generator.__len__()):

    # Get Sample Dataset
    sample_x_true, sample_y_true = test_generator.__getitem__(idx)
    sample_y_true = K.cast(sample_y_true, dtype=tf.float32)

    # inference
    start_time = time.time()
    predictions = model(sample_x_true, training=False)
    print("Inference FPS: {:.1f}".format(1 / (time.time() - start_time)))

    # get bboxes
    second_time = time.time()
    pred_bboxes = get_all_bboxes(predictions)
    pred_bboxes = non_max_suppression(pred_bboxes[0], threshold=0.4, iou_threshold=0.5)
    print("NMS FPS: {:.1f}".format(1 / (time.time() - second_time)))

    # Get bbox img
    # true_bboxes = get_all_bboxes(sample_y_true)
    # true_bboxes = [bbox for bbox in true_bboxes[0] if bbox[1] > 0.5]
    x_true_img = get_bbox_img(jpg_data_list[idx], pred_bboxes, obj_name_list)
    # x_true_img = get_bbox_img(jpg_data_list[idx], true_bboxes, obj_name_list)

    print("FPS: {:.1f}".format(1/(time.time() - start_time)))

    # Show
    cv2.imshow("dd", sample_x_true[0])
    cv2.imshow("Test", x_true_img)
    key = cv2.waitKey(0)
    if key == 27:
        break