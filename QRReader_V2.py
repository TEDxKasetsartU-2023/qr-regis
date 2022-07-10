# read QR Code and transform to specific format
# | IMPORT SECTIONq
from queue import Empty
import cv2
import numpy as np

from multiprocessing import Process, Queue
from pyzbar.pyzbar import decode


# | FUNCTION SECTION
def output(q):
    while True:
        try:
            frame = q.get_nowait()
        except Empty:
            continue

        cv2.imshow("Main", frame)
        key = cv2.waitKey(1)

        if key == ord("q"):
            break


# | MAIN SECTION
if __name__ == "__main__":
    q = Queue()
    out_proc = Process(target=output, args=(q,))

    cam_no = input("Cam #: ")
    cap = cv2.VideoCapture(cam_no if cam_no != "" else 0)

    out_proc.start()
    while True:
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
            q.put_nowait(res)
        
        if not out_proc.is_alive():
            break

    # out_proc.join()
    cv2.destroyAllWindows()
