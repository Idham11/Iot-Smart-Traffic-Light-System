import time
import io
import threading

try:
    from picamera2 import Picamera2
    import cv2
    HAS_CAMERA = True
except ImportError:
    print("Picamera2/OpenCV not found. Running camera in MOCK mode.")
    HAS_CAMERA = False

class CameraStream:
    def __init__(self):
        self.frame = None
        self.thread = None
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def _capture_loop(self):
        if HAS_CAMERA:
            try:
                picam2 = Picamera2()
                picam2.configure(picam2.create_video_configuration(main={"size": (640, 480), "format": "BGR888"}))
                picam2.start()
                
                while self.running:
                    # Capture frame as BGR array (OpenCV format)
                    frame_array = picam2.capture_array()
                    
                    # Encode as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame_array)
                    if ret:
                        self.frame = buffer.tobytes()
                    time.sleep(0.05) # ~20 fps
                    
                picam2.stop()
            except Exception as e:
                print(f"Camera error: {e}")
                self.running = False
        else:
            # Mock camera: Create a blank image or simple pattern
            # For simplicity, we just won't update self.frame, and the stream will return a blank or static image
            try:
                with open("static/placeholder_feed.jpg", "rb") as f:
                    self.frame = f.read()
            except FileNotFoundError:
                self.frame = b''
            
            while self.running:
                time.sleep(1)

    def get_frame(self):
        return self.frame

camera_stream = CameraStream()

def generate_frames():
    """Generator function for MJPEG streaming"""
    while True:
        frame = camera_stream.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            time.sleep(0.1)
