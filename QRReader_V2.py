# read QR Code and transform to specific format
# | IMPORT SECTION
import cv2
import numpy as np

from pyzbar.pyzbar import decode


# | MAIN SECTION
if __name__ == "__main__":
    cam_no = input("Cam #: ")
    cap = cv2.VideoCapture(cam_no if cam_no != "" else 0)

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
            print(barcode)
            (x, y, w, h) = barcode.rect
            (bl, )
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 5)

            print(barcode.data.decode("utf-8"))
            print(barcode.type)

        if ret:
            # * output
            res = np.vstack((frame, gray))

            cv2.imshow("Main", res)
            key = cv2.waitKey(1)

        if key == ord("q"):
            break


# image = cv2.imread(r"D:\TEDxKasetsartU 2023\qr-regis\tmp.jpg")

# cv2.imshow("Image", image)

# detectedBarcodes = decode(image)

# for barcode in detectedBarcodes:

#     (x, y, w, h) = barcode.rect
#     cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 5)

#     print(barcode.data)
#     print(barcode.type)


# cv2.imshow("Image", image)

# cv2.waitKey(0)
# cv2.destroyAllWindows()
