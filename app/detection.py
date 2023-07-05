import sys
from django.shortcuts import render
sys.path.append('..')
from django.shortcuts import get_object_or_404
import cv2
import os
import numpy as np
from attendance.settings import BASE_DIR1
from .models import *
import face_recognition
import dlib
import pickle
from .spoofing.test import test
from datetime import datetime


class FaceRecognition:

    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.face_encodings = []
        self.ids = []

    def faceDetect(self, entry1):
        face_id = entry1
        cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        count = 0

        while count < 30:
            ret, img = cam.read()
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            faces = self.detector(gray)
            for face in faces:
                x, y, w, h = face.left(), face.top(), face.width(), face.height()
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                count += 1

                face_img = gray[y:y + h, x:x + w]
                face_img = cv2.resize(face_img, (160, 160))

                img_path = os.path.join(BASE_DIR1, f'app/dataset/User.{face_id}.{count}.jpg')
                cv2.imwrite(img_path, face_img)
                cv2.imshow('Register Face', img)

            if cv2.waitKey(100) == 27 or count >= 30:
                break

        cam.release()
        cv2.destroyAllWindows()