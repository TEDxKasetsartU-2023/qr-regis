# read QR Code and transform to specific format
# | IMPORT SECTION
import base64
from queue import Empty
import cv2
import numpy as np

from multiprocessing import Process, Queue
from pyzbar.pyzbar import decode


# | FUNCTION SECTION
def update(q: Queue) -> None:
    RUN = True
    
    while RUN:
        try:
            RUN = status_q.get_nowait()
        except Empty:
            pass

        try:
            data = q.get_nowait()
        except Empty:
            continue

        # do something

    print("output exit")


def decode_code(data):
    res = base64.b64decode(data)
    return res.split("|")


# | MAIN SECTION
if __name__ == "__main__":
    q = Queue()
    status_q = Queue(1)
    update_proc = Process(target=update, args=(q, status_q))

    cam_no = input("Cam #: ")
    cap = cv2.VideoCapture(0 if cam_no == "" else cam_no)

    ret, frame = cap.read()

    update_proc.start()
    while True:
        # * get image from camera
        ret, frame = cap.read()
        if ret:
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
                    points = np.array(
                        [[p.x, p.y] for p in barcode.polygon], dtype=np.int32
                    )
                    cv2.polylines(frame, [points], 1, (255, 0, 0), 5)

                    print(barcode.data.decode("utf-8"))

            # * output
            res = np.vstack((frame, gray))
            cv2.imshow("Main", res)
            key = cv2.waitKey(1)

            q.put_nowait(decode_code(barcode.data.decode("utf-8")))

            if key == ord("q"):
                break
        else:
            print("do not receive the frame")

    status_q.put_nowait(False)
    update_proc.join()
    cv2.destroyAllWindows()
    cap.release()
    q.close()
    q.cancel_join_thread()
    status_q.close()
    status_q.cancel_join_thread()
    print("main exit")
