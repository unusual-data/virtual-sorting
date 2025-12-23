import cv2
import mss
import numpy as np

with mss.mss() as sct:
    screenshot = np.array(sct.grab(sct.monitors[1]))
    img = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

roi = cv2.selectROI("ROI Sec (Enter = Onay, Esc = Iptal)", img, False)
cv2.destroyAllWindows()

x, y, w, h = roi
print(f'monitor_area = {{"top": {y}, "left": {x}, "width": {w}, "height": {h}}}')
