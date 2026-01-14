# Sanal Ayıklama Uygulaması (Factory I/O & Python)

Bu depo, TIA Portal, Factory I/O ve Python kullanılarak geliştirilen sanal ayıklama (görüntü işleme ile nesne ayrıştırma) projesinin kaynak kodlarını ve teknik dokümantasyonunu içerir. 

## Proje Tanımı

Proje, Factory I/O ortamındaki bir konveyör hattı üzerinde hareket eden mavi ve yeşil hammaddelerin simülasyon ekranından algılanarak ilgili iticiler (pusher) vasıtasıyla ayrıştırılmasını sağlar.

### Sistem Bileşenleri

-   **Kontrolcü:** Siemens S7-1200 (PLCSIM V20 üzerinde simüle edilmiştir)

-   **Saha Simülasyonu:** Factory I/O

-   **Görüntü İşleme ve Karar Mekanizması:** Python (OpenCV, MSS, Snap7)

-   **Haberleşme:** NetToPLCSim ve S7 İletişim Protokolü \## Dosya Listesi

-   `sanal_ayiklama.py`: Görüntü işleme, renk algılama ve PLC ile veri haberleşmesini sağlayan ana Python kodu.

-   `roi-belirleme.py` : Görüntünün ekrandan hangi noktadan alınacağını sağlayan ROI kordinatlarını belirleyen Python kodu.

-   `README.md`: Proje dokümantasyonu.

## Gereksinimler

Projenin çalıştırılması için aşağıdaki yazılımlar gereklidir:

1.  **TIA Portal V20** (veya uyumlu sürüm)
2.  **PLCSIM V20**
3.  **Factory I/O**
4.  **NetToPLCSim** (PLCSIM ve harici ağ arayüzü köprüsü için)
5.  **Python 3.x**

### Python Kütüphaneleri

Gerekli kütüphaneleri yüklemek için terminalde şu komutu çalıştırın:

``` bash
pip install opencv-python numpy mss python-snap7
```

## Kurulum ve Çalıştırma Adımları

### 1. TIA Portal ve PLCSIM

-   Factory I/O S7-1200 şablonunu (template) kullanarak projeyi açın.
-   PLC ayarlarında **"Permit access with PUT/GET communication"** seçeneğini aktif edin.
-   Projenizi derleyin ve PLCSIM'e yükleyin.

### 2. NetToPLCSim

-   Aracı **yönetici olarak** çalıştırın.
-   Yerel ağ IP adresiniz (PC IP) ile PLCSIM IP adresini (Genellikle 192.168.0.1) eşleştirin.
-   Server'ı başlatın.

### 3. Factory I/O

-   Sahne konfigürasyonunu yapın (Sürücü olarak **Siemens S7-PLCSIM** seçin).
-   Giriş/Çıkış adreslerini TIA Portal projesindeki etiketlerle (tag) eşleştirin.
-   Simülasyonu başlatın.

### 4. Python

-   `sanal_ayiklama.py` dosyasını açın.
-   `PLC_IP` değişkenini NetToPLCSim'de ayarladığınız (kendi bilgisayarınızın) IP adresi ile güncelleyin.
-   Betiği çalıştırın.

## Çalışma Prensibi

Python betiği (`sanal_ayiklama.py`), `mss` kütüphanesi ile ekranın belirli bölgelerinden (ROI) anlık görüntü alır. `OpenCV` kullanılarak alınan görüntü HSV formatına çevrilir ve belirlenen renk eşiklerine göre maskeleme yapılır. Maskelenen alandaki piksel yoğunluğuna göre nesne algılanırsa, `snap7` kütüphanesi aracılığıyla PLC'nin ilgili hafıza bitleri (M50.0, M51.0 vb.) tetiklenir.

------------------------------------------------------------------------

## Python Kaynak Kodu

Projenin temelini oluşturan `sanal_ayiklama.py` dosyasının içeriği aşağıdadır:

``` python
import time
import cv2
import numpy as np
import mss
import snap7
from snap7 import util

# --- YAPILANDIRMA ---
# PLC Bağlantı Ayarları (NetToPLCSim IP Adresi)
PLC_IP = "192.XXX.XXX.XXX" 
RACK = 0
SLOT = 1

# Renk Eşik Değerleri (HSV)
blue_low = np.array([75, 30, 20])
blue_high = np.array([140, 255, 255])

green_low = np.array([40, 80, 50])
green_high = np.array([80, 255, 255])

# İlgi Alanları (ROI) - Ekran çözünürlüğüne göre ayarlanmalıdır
roi_blue = {'top': 432, 'left': 692, 'width': 48, 'height': 44}
roi_green = {'top': 565, 'left': 1253, 'width': 50, 'height': 68}

px_threshold = 1200
gecen_sure = 0.10
last_log = 0 
show_debug = True

# --- PLC BAĞLANTISI ---

plc = snap7.client.Client()
plc.connect(PLC_IP, RACK, SLOT)

# --- ANA DÖNGÜ ---
with mss.mss() as scr:

    while True:

        t0 = time.perf_counter()
        img_b = np.array(scr.grab(roı_blue))[:, :, :3]
        img_g = np.array(scr.grab(roı_green))[:, :, :3]

        hsv_b = cv2.cvtColor(img_b, cv2.COLOR_BGR2HSV)
        hsv_g = cv2.cvtColor(img_g, cv2.COLOR_BGR2HSV)
        
        blue_mask  = cv2.inRange(hsv_b, blue_low, blue_hıgh)
        green_mask = cv2.inRange(hsv_g, green_low, green_hıgh)

        blue_px  = cv2.countNonZero(blue_mask)
        green_px = cv2.countNonZero(green_mask)

        blue  = blue_px  > px_threshold
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
```

## Kaynak

Orijinal Makale: [Proje Sayfası](https://ibrahimcapar.com/projects/virtual-sorting/) \| [Proje Yapım Aşamaları](https://ibrahimcapar.com/posts/sanal-ayiklama/)
