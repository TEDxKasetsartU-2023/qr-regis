# read QR Code and transform to specific format
# | IMPORT SECTION
from queue import Empty, Full
import cv2
import numpy as np

from multiprocessing import Process, Queue
from pyzbar.pyzbar import decode


# | FUNCTION SECTION
def output(q: Queue) -> None:
    while True:
        try:
            frame = q.get_nowait()
        except Empty:
            continue

        cv2.imshow("Main", frame)
        key = cv2.waitKey(1)

        if key == ord("q"):
            break

    print("output exit")


# | MAIN SECTION
if __name__ == "__main__":
    q = Queue(2)
    out_proc = Process(target=output, args=(q,))

    cam_no = input("Cam #: ")
    cap = cv2.VideoCapture(0 if cam_no == "" else cam_no)

    ret, frame = cap.read()

    out_proc.start()
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
            try:
                q.put_nowait(res)
            except Full:
                print("queue full")
                continue
        else:
            print("do not receive the frame")

        if not out_proc.is_alive():
            break

    out_proc.join()
    cv2.destroyAllWindows()
    cap.release()
    q.close()
    q.cancel_join_thread()
    print("main exit")
