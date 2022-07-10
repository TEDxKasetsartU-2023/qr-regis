# read QR Code and transform to specific format
# | IMPORT SECTIONq
import cv2
import numpy as np

from pyzbar.pyzbar import decode
from threading import Thread

# from queue import Empty, Queue

# | GLOBAL VARIABLES
RUN = True

# | CLASS SECTION
class Queue:
    def __init__(self, size=float("inf")) -> None:
        self.size = size
        self.data = []
        self.Full = False
        self.Empty = True

    def put(self, val):
        if len(self.data) < self.size:
            self.data.append(val)
            if len(self.data) == self.size:
                self.Full = True
            if self.Empty:
                self.Empty = False
        else:
            raise Queue.FULL

    def get(self):
        if len(self.data) != 0:
            val = self.data.pop()
            if len(self.data) == 0:
                self.Empty = True
            if self.Full:
                self.Full = False
            return val
        else:
            raise Queue.EMPTY

    class FULL(Exception):
        pass

    class EMPTY(Exception):
        pass


# | FUNCTION SECTION
def output(q):
    global RUN
    while True:
        try:
            frame = q.get()
        except Queue.EMPTY:
            continue

        cv2.imshow("Main", frame)
        key = cv2.waitKey(1)

        if key == ord("q"):
            RUN = False
            break


# | MAIN SECTION
if __name__ == "__main__":
    q = Queue()
    out_thread = Thread(target=output, args=(q,))

    cam_no = input("Cam #: ")
    cap = cv2.VideoCapture(cam_no if cam_no != "" else 0)

    out_thread.start()
    while RUN:
        # * get image from camera
        ret, frame = cap.read()
        frame = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75)

        # * preprocessing
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # * detection
        detectedBarcodes = decode(gray)

        for barcode in detectedBarcodes:
            if barcode.type == "QRCODE":
                (x, y, w, h) = barcode.rect
                (bl, br, tr, tl) = barcode.polygon
                points = np.array([[p.x, p.y] for p in barcode.polygon], dtype=np.int32)
                cv2.polylines(frame, [points], 1, (255, 0, 0), 5)

                print(barcode.data.decode("utf-8"))

        if ret:
            # * output
            res = np.vstack((frame, gray))
            q.put(res)

out_thread.join()
cv2.destroyAllWindows()
