import time
import cv2
import numpy as np
import mss
import snap7
from snap7 import util

PLC_IP = "XXX.XXX.XXX.XXX"
RACK = 0
SLOT = 1

blue_low   = np.array([75,  30, 20])
blue_hıgh  = np.array([140, 255, 255])

green_low  = np.array([40,  80, 50])
green_hıgh = np.array([80,  255, 255])

roı_blue = {'top': 432, 'left': 692, 'width': 48, 'height': 44}
roı_green = {'top': 565, 'left': 1253, 'width': 50, 'height': 68}

px_threshold = 1200
gecen_sure = 0.10
last_log = 0  

show_debug = True

plc = snap7.client.Client()
plc.connect(PLC_IP, RACK, SLOT)


with mss.mss() as scr:
    while True:
        t0 = time.perf_counter()

        img_b = np.array(scr.grab(roı_blue))[:, :, :3]
        img_g = np.array(scr.grab(roı_green))[:, :, :3]

        hsv_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2HSV)
        hsv_g = cv2.cvtColor(img_g, cv2.COLOR_BGR2HSV)

        blue_mask  = cv2.inRange(hsv_b, blue_low, blue_hıgh)
        green_mask = cv2.inRange(hsv_g, green_low, green_hıgh)

        blue_px  = cv2.countNonZero(blue_mask)
        green_px = cv2.countNonZero(green_mask)

        blue  = blue_px  > px_threshold
        green = green_px > px_threshold

        byte_blue = bytearray(plc.mb_read(50, 1))
        util.set_bool(byte_blue, 0, 0, blue)
        plc.mb_write(50, 1, byte_blue)
        
        byte_green = bytearray(plc.mb_read(51, 1))
        util.set_bool(byte_green, 0, 0, green)
        plc.mb_write(51, 1, byte_green)

        now = time.time()
        if now - last_log > 0.5:
            print(f"MAVİ px={blue_px:5d} eşik={px_threshold} -> {int(blue)} | YEŞİL px={green_px:5d} -> {int(green)}")
            last_log = now

        if show_debug:
            cv2.imshow("Mavi ROI", img_b)
            cv2.imshow("Mavi Maskleme", blue_mask)
            cv2.imshow("Yeşil ROI", img_g)
            cv2.imshow("Yeşil Maskeleme", green_mask)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        dt = time.perf_counter() - t0
        if dt < gecen_sure: time.sleep(gecen_sure - dt)

cv2.destroyAllWindows()
plc.disconnect()
