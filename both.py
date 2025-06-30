import cv2
import mediapipe as mp
import numpy as np
import time
import math
import datetime

# Stream URL from ESP32-CAM
url = 'http://192.168.31.35:81/stream'

# MediaPipe setup
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

def euclidean(p1, p2):
    return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

def calculate_ear(landmarks, eye_indices, w, h):
    pts = [(int(landmarks[i].x * w), int(landmarks[i].y * h)) for i in eye_indices]
    A = euclidean(pts[1], pts[5])
    B = euclidean(pts[2], pts[4])
    C = euclidean(pts[0], pts[3])
    return (A + B) / (2.0 * C)

EYE_AR_THRESH = 0.2
SLEEP_THRESHOLD = 10
eye_closed_start = None

video_writer = None
video_start_time = time.time()
recording_fps = 15
fourcc = cv2.VideoWriter_fourcc(*'XVID')

cap = cv2.VideoCapture(url)
cv2.namedWindow("Live Feed", cv2.WINDOW_AUTOSIZE)

frame_count = 0
start_time = time.time()

with mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as face_mesh:

    while True:
        success, frame = cap.read()
        if not success:
            print("[WARN] Could not fetch frame from ESP32-CAM.")
            continue

        h, w, _ = frame.shape

        # Start new video every 60 seconds
        now = time.time()
        if video_writer is None or now - video_start_time >= 60:
            if video_writer:
                video_writer.release()
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'video_{timestamp}.avi'
            video_writer = cv2.VideoWriter(filename, fourcc, recording_fps, (w, h))
            print(f"[INFO] Started new video: {filename}")
            video_start_time = now

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        sleeping = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Draw full face mesh and contours
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style()
                )
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style()
                )

                landmarks = face_landmarks.landmark

                # Mouth open detection
                pt_top = (int(landmarks[13].x * w), int(landmarks[13].y * h))
                pt_bottom = (int(landmarks[14].x * w), int(landmarks[14].y * h))
                mouth_open = euclidean(pt_top, pt_bottom)
                if mouth_open > 35:
                    cv2.putText(frame, "Crying", (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 0, 255), 2, cv2.LINE_AA)

                # Eye aspect ratio
                left_ear = calculate_ear(landmarks, LEFT_EYE, w, h)
                right_ear = calculate_ear(landmarks, RIGHT_EYE, w, h)
                avg_ear = (left_ear + right_ear) / 2.0

                if avg_ear < EYE_AR_THRESH:
                    if eye_closed_start is None:
                        eye_closed_start = time.time()
                    elif time.time() - eye_closed_start > SLEEP_THRESHOLD:
                        sleeping = True
                else:
                    eye_closed_start = None

        if sleeping:
            cv2.putText(frame, "Sleeping", (30, 100), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (255, 0, 0), 2, cv2.LINE_AA)

        video_writer.write(frame)
        cv2.imshow("Live Feed", frame)

        frame_count += 1
        if frame_count % 30 == 0:
            elapsed = time.time() - start_time
            actual_fps = frame_count / elapsed
            print(f"[INFO] Capturing at approx {actual_fps:.2f} FPS")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
if video_writer:
    video_writer.release()
cv2.destroyAllWindows()
