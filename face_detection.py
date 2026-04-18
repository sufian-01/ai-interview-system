"""Simple OpenCV face detection utilities."""

from __future__ import annotations

import time

import cv2
import streamlit as st


FACE_CASCADE = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)


def detect_face_from_webcam(max_duration_seconds: int = 15) -> bool:
    """Open webcam stream, render frames in Streamlit, and detect a face.

    Args:
        max_duration_seconds: Maximum duration to keep the camera active.

    Returns:
        True if a face is detected at least once, else False.
    """
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        st.error("Could not access webcam. Please check camera permissions.")
        return False

    frame_placeholder = st.empty()
    status_placeholder = st.empty()

    status_placeholder.info("Camera started. Looking for a face...")
    found_face = False
    start_time = time.time()

    try:
        while time.time() - start_time < max_duration_seconds:
            success, frame = camera.read()
            if not success:
                status_placeholder.warning("Unable to read frame from webcam.")
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = FACE_CASCADE.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60),
            )

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            if len(faces) > 0:
                found_face = True

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", caption="Webcam Feed")

            if found_face:
                status_placeholder.success("Face detected.")
                break

        if not found_face:
            status_placeholder.warning("No face detected.")

    finally:
        camera.release()
        frame_placeholder.empty()

    return found_face
