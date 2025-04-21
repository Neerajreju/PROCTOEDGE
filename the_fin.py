# import cv2
# import mediapipe as mp
# import time
# from ultralytics import YOLO
# import numpy as np

# # Initialize Mediapipe Face Mesh with multiple face detection
# mp_face_mesh = mp.solutions.face_mesh
# face_mesh = mp_face_mesh.FaceMesh(
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5,
#     max_num_faces=2  # Allow detection of up to 2 faces (adjust as needed)
# )

# # Load YOLOv8 model for mobile phone detection
# try:
#     mobile_model = YOLO('yolov8med_mobile_phone.pt')
# except Exception as e:
#     print(f"Error loading YOLO model: {e}")
#     exit()

# # Initialize webcam
# cap = cv2.VideoCapture(0)
# if not cap.isOpened():
#     print("Error: Could not open webcam.")
#     exit()

# # Variables for gaze tracking
# left_gaze_start_time = None
# right_gaze_start_time = None
# gaze_threshold = 5  # 5 seconds
# gaze_sensitivity = 0.1  # Adjust based on testing

# # Alert message variables
# alert_message = ""
# alert_start_time = None
# alert_duration = 3  # Duration to display alert in seconds

# while cap.isOpened():
#     ret, frame = cap.read()
#     if not ret:
#         print("Error: Failed to capture frame.")
#         break

#     # Convert frame to RGB for Mediapipe
#     rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     results_face_mesh = face_mesh.process(rgb_frame)

#     # Reset alert message if duration has passed
#     if alert_start_time and (time.time() - alert_start_time > alert_duration):
#         alert_message = ""

#     # Debug: Print number of detected faces
#     if results_face_mesh.multi_face_landmarks:
#         num_faces = len(results_face_mesh.multi_face_landmarks)
#         print(f"Number of faces detected: {num_faces}")
#     else:
#         num_faces = 0
#         print("No faces detected")

#     # Face detection logic
#     if not results_face_mesh.multi_face_landmarks:
#         alert_message = "ALERT: No face detected!"
#         alert_start_time = time.time()
#     elif len(results_face_mesh.multi_face_landmarks) > 1:
#         alert_message = "ALERT: Multiple faces detected!"
#         alert_start_time = time.time()
#     else:
#         # Single face detected, proceed with gaze tracking
#         for face_landmarks in results_face_mesh.multi_face_landmarks:
#             left_eye = face_landmarks.landmark[33]  # Left eye
#             right_eye = face_landmarks.landmark[263]  # Right eye
#             nose = face_landmarks.landmark[1]  # Nose bridge

#             # Calculate gaze offsets
#             left_gaze_offset = left_eye.x - nose.x
#             right_gaze_offset = right_eye.x - nose.x

#             # Detect looking left
#             if left_gaze_offset < -gaze_sensitivity:
#                 if left_gaze_start_time is None:
#                     left_gaze_start_time = time.time()
#                 elif time.time() - left_gaze_start_time > gaze_threshold:
#                     alert_message = "ALERT: Looking left for too long!"
#                     alert_start_time = time.time()
#             else:
#                 left_gaze_start_time = None

#             # Detect looking right
#             if right_gaze_offset > gaze_sensitivity:
#                 if right_gaze_start_time is None:
#                     right_gaze_start_time = time.time()
#                 elif time.time() - right_gaze_start_time > gaze_threshold:
#                     alert_message = "ALERT: Looking right for too long!"
#                     alert_start_time = time.time()
#             else:
#                 right_gaze_start_time = None

#     # Run YOLOv8 for mobile phone detection
#     results = mobile_model(frame)

#     # Draw bounding boxes for detected mobile phones
#     for result in results:
#         for box in result.boxes:
#             x1, y1, x2, y2 = map(int, box.xyxy[0])
#             confidence = box.conf[0].item()
#             label = f"Mobile {confidence:.2f}"
#             cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
#             cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
#             alert_message = "ALERT: Mobile phone detected!"
#             alert_start_time = time.time()

#     # Display alert message if within duration
#     if alert_message and (time.time() - alert_start_time < alert_duration):
#         cv2.putText(frame, alert_message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

#     # Show the frame
#     cv2.imshow("Proctoring System", frame)

#     # Exit on 'q' key press
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         break

# # Cleanup
# cap.release()
# face_mesh.close()
# cv2.destroyAllWindows()
import cv2
import mediapipe as mp
import time
from ultralytics import YOLO
import numpy as np
import requests
import sys

# ✅ Read token from command line
if len(sys.argv) < 2:
    print("Usage: python the_fin.py <exam_token>")
    sys.exit()

EXAM_TOKEN = sys.argv[1]

# ✅ Alert sending function
def send_alert(token, message):
    url = "http://127.0.0.1:5000/send_alert"  # Change IP if hosted elsewhere
    data = {
        "token": token,
        "alert": message
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 204:
            print("Alert sent:", message)
        else:
            print("Failed to send alert:", response.status_code)
    except Exception as e:
        print("Error sending alert:", e)

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_faces=2
)

# Load YOLOv8 model
try:
    mobile_model = YOLO('yolov8med_mobile_phone.pt')
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    exit()

# Webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Gaze tracking variables
left_gaze_start_time = None
right_gaze_start_time = None
gaze_threshold = 5
gaze_sensitivity = 0.1

# Alert message handling
alert_message = ""
alert_start_time = None
alert_duration = 3

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results_face_mesh = face_mesh.process(rgb_frame)

    if alert_start_time and (time.time() - alert_start_time > alert_duration):
        alert_message = ""

    if results_face_mesh.multi_face_landmarks:
        num_faces = len(results_face_mesh.multi_face_landmarks)
        print(f"Number of faces detected: {num_faces}")
    else:
        num_faces = 0
        print("No faces detected")

    # Face-based alerts
    if not results_face_mesh.multi_face_landmarks:
        alert_message = "ALERT: No face detected!"
        alert_start_time = time.time()
        send_alert(EXAM_TOKEN, alert_message)

    elif len(results_face_mesh.multi_face_landmarks) > 1:
        alert_message = "ALERT: Multiple faces detected!"
        alert_start_time = time.time()
        send_alert(EXAM_TOKEN, alert_message)

    else:
        for face_landmarks in results_face_mesh.multi_face_landmarks:
            left_eye = face_landmarks.landmark[33]
            right_eye = face_landmarks.landmark[263]
            nose = face_landmarks.landmark[1]

            left_gaze_offset = left_eye.x - nose.x
            right_gaze_offset = right_eye.x - nose.x

            if left_gaze_offset < -gaze_sensitivity:
                if left_gaze_start_time is None:
                    left_gaze_start_time = time.time()
                elif time.time() - left_gaze_start_time > gaze_threshold:
                    alert_message = "ALERT: Looking left for too long!"
                    alert_start_time = time.time()
                    send_alert(EXAM_TOKEN, alert_message)
            else:
                left_gaze_start_time = None

            if right_gaze_offset > gaze_sensitivity:
                if right_gaze_start_time is None:
                    right_gaze_start_time = time.time()
                elif time.time() - right_gaze_start_time > gaze_threshold:
                    alert_message = "ALERT: Looking right for too long!"
                    alert_start_time = time.time()
                    send_alert(EXAM_TOKEN, alert_message)
            else:
                right_gaze_start_time = None

    # YOLO for mobile detection
    results = mobile_model(frame)
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0].item()
            label = f"Mobile {confidence:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            alert_message = "ALERT: Mobile phone detected!"
            alert_start_time = time.time()
            send_alert(EXAM_TOKEN, alert_message)

    # Show alert message
    if alert_message and (time.time() - alert_start_time < alert_duration):
        cv2.putText(frame, alert_message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Proctoring System", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
face_mesh.close()
cv2.destroyAllWindows()
