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



    def recognizeFace(self):
        try:
            with open("model.pickle", "rb") as file:
                data = pickle.load(file)
                self.face_encodings = data["encodings"]
                self.ids = data["labels"]

            font = cv2.FONT_HERSHEY_SIMPLEX

            cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            # address = 'http://192.168.0.102:8080/video'
            # cam.open(address)

            device_id = 0  # Specify the GPU device ID to use
            model_dir = r"C:\Users\Shahine\PycharmProjects\BestProject\attendance_V2\app\spoofing\resources\anti_spoof_models"  # Path to the anti-spoofing models

            while True:
                ret, img = cam.read()
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                faces = face_recognition.face_locations(rgb_img)
                encodings = face_recognition.face_encodings(rgb_img, faces)

                for face_encoding, face_location in zip(encodings, faces):
                    top, right, bottom, left = face_location
                    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)

                    # Perform anti-spoofing test
                    is_fake = test(img, model_dir, device_id)

                    if is_fake != 1:
                        name = "Fake"  # Set the name to indicate that the face is fake
                    else:
                        matches = face_recognition.compare_faces(self.face_encodings, face_encoding)
                        face_distances = face_recognition.face_distance(self.face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)

                        if matches[best_match_index]:
                            face_id = self.ids[best_match_index]
                            attendee = get_object_or_404(Attendee, user=face_id)
                            attendee_classrooms = attendee.classrooms.all()

                            if not attendee_classrooms:
                                name = "Unknown"
                            else:
                                classroom = Classroom.objects.get(id=1)
                                for attendee_classroom in attendee_classrooms:
                                    if attendee_classroom.id != classroom.id:
                                        name = "Unknown"
                                        continue
                                    else:
                                        name = attendee.name
                                        break
                                classroom = Classroom.objects.get(id=1)
                                attendance = Attendance.objects.filter(classroom=classroom, attendee=attendee).first()

                                if attendance:
                                    # Update existing attendance row
                                    attendance.is_present = True
                                    attendance.check_in_time = datetime.now()
                                    attendance.save()
                        else:
                            name = "Unknown"

                    cv2.putText(img, str(name), (left + 5, top - 5), font, 1, (255, 255, 255), 2)
                    cv2.putText(img, str(round(face_distances[best_match_index], 2)), (left + 5, bottom - 5), font, 1,
                                (255, 255, 0), 1)

                cv2.imshow('Detect Face', img)

                k = cv2.waitKey(10) & 0xff
                if k == 27:
                    break

            cam.release()
            cv2.destroyAllWindows()
        except:
            pass

def trainFace(request):
    path = BASE_DIR1 + '/app/dataset'
    face_encodings = []
    ids = []

    for filename in os.listdir(path):
        imagePath = os.path.join(path, filename)
        face_image = face_recognition.load_image_file(imagePath)
        face_encoding = face_recognition.face_encodings(face_image)
        if len(face_encoding) > 0:
            face_encodings.append(face_encoding[0])
            face_id = int(os.path.splitext(filename)[0].split(".")[1])
            ids.append(face_id)

    data = {"encodings": face_encodings, "labels": ids}
    with open("model.pickle", "wb") as file:
        pickle.dump(data, file)
    return render(request, 'app/home.html')
