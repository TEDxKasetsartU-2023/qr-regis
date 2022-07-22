# read QR Code and transform to specific format
# | IMPORT SECTION
import base64
import cv2
import datetime
import numpy as np
import os
import sys

from google.oauth2 import service_account
from multiprocessing import Process, Queue
from pyzbar.pyzbar import decode
from queue import Empty

from ConfigFile import Config
from googleModule.GG import sheet_management

# | GLOBAL VARIABLE
c = Config()
c.fromFile("sheet.cfg")


# | FUNCTION SECTION
def sheet_proc(q: Queue, status_q: Queue) -> None:
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
    res = base64.b64decode(data.decode("utf-8"))
    return res.decode("utf-8").split("|")


# | MAIN SECTION
if __name__ == "__main__":
    cam_no = input("Cam #: ")
    cap = cv2.VideoCapture(0 if cam_no == "" else cam_no)

    ret, frame = cap.read()

    SHEET_SCOPES = [c["Google Api"]["SHEET_SCOPE"]]
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.path.split(sys.argv[0])[0], c["Google Api"]["SHEET_SERVICE_ACC_FILE"]
    )

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )

    sheet_id = c["Global"]["SHEET_ID"]

    s = sheet_management(sheet_id, SHEET_CREDS)
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

                    dec_data = decode_code(barcode.data)
                    sheet_code_col = s.read_sheet_by_range(
                        f"{c['Global']['SHEET_NAME']}!{chr(ord('A') + len(c['Global']['CRITERIA_COL'])+1)}:{chr(ord('A') + len(c['Global']['CRITERIA_COL'])+1)}"
                    )
                    sheet_regis_col = s.read_sheet_by_range(
                        f"{c['Global']['SHEET_NAME']}!{chr(ord('A') + len(c['Global']['CRITERIA_COL'])+2)}:{chr(ord('A') + len(c['Global']['CRITERIA_COL'])+2)}"
                    )
                    not_found = True
                    for row_index, row in enumerate(sheet_code_col["values"]):
                        if row[0] == dec_data[-1]:
                            if len(sheet_regis_col["values"]) != 1 and sheet_regis_col["values"][row_index][0] == "TRUE":
                                not_found = False
                                print("already regis")
                                break

                            s.write_sheet_by_range(
                                f"{c['Global']['SHEET_NAME']}!{chr(ord('A') + len(c['Global']['CRITERIA_COL'])+2)}{row_index+1}",
                                [["=TRUE"]],
                                "USER_ENTERED",
                            )
                            s.write_sheet_by_range(
                                f"{c['Global']['SHEET_NAME']}!{chr(ord('A') + len(c['Global']['CRITERIA_COL'])+3)}{row_index+1}",
                                [
                                    [
                                        f"{datetime.datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}",
                                    ]
                                ],
                                "USER_ENTERED",
                            )
                            print(f"{' '.join(dec_data)} status updated")
                            not_found = False
                            break
                    if not_found:
                        print("do not found\nplease check the google sheet")

            # * output
            res = np.vstack((frame, gray))
            cv2.imshow("Main", res)
            key = cv2.waitKey(1)

            if key == ord("q"):
                break
        else:
            print("do not receive the frame")

    print("main exit")
