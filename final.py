from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import argparse
import os
import sys
import math
import pickle
from facenet.src import facenet as facenet
from facenet.src.align import detect_face

import numpy as np
import cv2
import collections
from sklearn.svm import SVC

from mtcnn.mtcnn import MTCNN
import Config as config
import time
import cv2
import numpy as np

def main():

    INPUT_IMAGE_SIZE = 160
    CLASSIFIER_PATH = 'facenet/Models/Own/Own.pkl'
    FACENET_MODEL_PATH = 'facenet/Models/facenet/20180402-114759.pb'

    # Load The  Classifier
    with open(CLASSIFIER_PATH, 'rb') as file:
        model, class_names = pickle.load(file)
    print("Custom Classifier, Successfully loaded")

    with tf.Graph().as_default():

        gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.6)
        sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, log_device_placement=False))

        with sess.as_default():

            # Load the model
            print('Loading feature extraction model')
            facenet.load_model(FACENET_MODEL_PATH)

            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
            embedding_size = embeddings.get_shape()[1]

            pnet, rnet, onet = detect_face.create_mtcnn(sess, "facenet/src/align")


            people_detected = set()
            person_detected = collections.Counter()

            webcam_info = config.webcam_info()
            webcam_info.list_webcams()

            webcam = config.webcam()
            webcam.create_filter(webcam_info.webcam_list["Microsoft® LifeCam HD-3000 - 1"])

            webcam.set_callback()
            webcam.set_callback_properties()
            webcam.grabber_cb.grab_sample()
            webcam.run()

            count = 0
            detector = MTCNN()

            while True:
                dimensions = webcam.get_resolution()
                pBuffer = webcam.queue.get(0)

                bsize = dimensions[1] * dimensions[0] * 3
                buffer_relevant_data = pBuffer[:bsize]

                frame = np.array(buffer_relevant_data)
                img = np.reshape(frame, (dimensions[1], dimensions[0], 3))
                img = img[::-1]
                img = img.astype("uint8")

                result = detector.detect_faces(img)
                try:
                    if result != []:
                        for person in result:
                            bounding_box = person['box']
                            keypoints = person['keypoints']
                            print(person['confidence'])
                            print(result)

                            x1 = bounding_box[0]
                            y1 = bounding_box[1]
                            x2 = bounding_box[0] + bounding_box[2]
                            y2 = bounding_box[1] + bounding_box[3]

                            cropped = img[y1:y2, x1:x2]
                            scaled = cv2.resize(cropped, (INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE),
                                                interpolation=cv2.INTER_CUBIC)
                            scaled = facenet.prewhiten(scaled)
                            scaled_reshape = scaled.reshape(-1, INPUT_IMAGE_SIZE, INPUT_IMAGE_SIZE, 3)
                            feed_dict = {images_placeholder: scaled_reshape, phase_train_placeholder: False}
                            emb_array = sess.run(embeddings, feed_dict=feed_dict)
                            predictions = model.predict_proba(emb_array)
                            best_class_indices = np.argmax(predictions, axis=1)
                            best_class_probabilities = predictions[
                                np.arange(len(best_class_indices)), best_class_indices]
                            best_name = class_names[best_class_indices[0]]
                            print("Name: {}, Probability: {}".format(best_name, best_class_probabilities))

                            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 155, 255), 2)
                            text_x = x1
                            text_y = y2 + 20

                            if best_class_probabilities > 0.45:
                                name = class_names[best_class_indices[0]]
                            else:
                                name = "Unknown"
                            cv2.putText(img, name, (text_x, text_y), cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                        1, (255, 255, 255), thickness=1, lineType=2)
                            cv2.putText(img, str(round(best_class_probabilities[0], 3)), (text_x, text_y + 17),
                                        cv2.FONT_HERSHEY_COMPLEX_SMALL,
                                        1, (255, 255, 255), thickness=1, lineType=2)
                            person_detected[best_name] += 1
                except:
                    pass

                cv2.imshow('Face Recognition', img)
                if cv2.waitKey(1) & 0xFF == ord('x'):
                    break


            cv2.destroyAllWindows()

main()