# HyperOS Leica Camera for Xiaomi 12 Pro (zeus)

**[English](#english) · [Türkçe](#türkçe)**

HyperOS Camera 6.2 with Leica looks, patched to work on **AOSP-based Android 17 ROMs** for the **Xiaomi 12 Pro (zeus)**, packaged as a root module.

by **Ahmet033**

---

## English

### Features

| Feature | Status |
|---|---|
| Leica Authentic look and Leica filters (VIV / NAT / BW) | ✅ |
| Photo and video (picture + sound) | ✅ |
| 0.6x ultra-wide (photo and video) | ✅ |
| 2x / 5x telephoto switching | ✅ |
| Up to 60x zoom | ✅ |
| 1080p 60 FPS video | ✅ |
| Portrait (bokeh), front and rear | ✅ |
| Beautify (Smooth / Slender / Big eyes) | ✅ * |
| Pro mode | ✅ |

\* The beautify effect is subtle in the live preview but is fully applied to the captured photo.

### Tested on

- Xiaomi 12 Pro (zeus)
- Evolution X 12.4, Android 17 (vendor OS3.0.4.0.VLBMIXM)
- BakaSU (KernelSU based) root, SELinux enforcing

Magisk and APatch were **not** tested. Other AOSP-based Android 17 ROMs with the same zeus vendor should work but were not tested.

### Install

1. If you have the Xiaomi 12 (cupid) Leica module (`cupid-miuicamera`) installed, **remove it first** and reboot.
2. Download `zeus-hyperos-leica-camera-aosp-v1.0.zip` from [Releases](../../releases).
3. Install it from your root manager (KernelSU / BakaSU).
4. Reboot.

The installer clears Android's package cache automatically, which is needed for the system to pick up the new camera. The first launch resets the camera app's own settings once (the app signature changes). Photos and videos are not affected.

### Uninstall

Remove the module from your root manager and reboot. The package cache is cleared automatically, and the ROM's own camera comes back.

### Known limitations

- The beautify effect is subtle in the live preview but is fully applied to the captured photo.
- Made for HyperOS Camera `1+6.2.000360.1` only; the patches use fixed offsets.

### What was wrong and how it was fixed

The HyperOS camera expects a HyperOS ROM. On AOSP it ran with several features silently disabled:

1. **Missing HyperOS framework classes** (`AudioParaManger`, `MiuiSettings`, `HapticFeedbackUtil`, ...): video mode froze. Small stub classes were added (`patcher/stubs`).
2. **Vendor tags were never discovered.** On non-HyperOS ROMs the camera only reads `getAvailableCaptureRequestKeys()` instead of all vendor keys, so bokeh, 1080p 60 FPS, beautify ratios, smooth lens transition, MFNR and more were never sent to the camera HAL. The camera now always uses `getAllVendorKeys()`.
3. **Zoom used crop regions instead of `zoomRatio`.** With crop regions you cannot go below 1x (the crop becomes negative and the framework turns it into 1.0), so 0.6x stayed on the main lens. The camera now sends `CONTROL_ZOOM_RATIO` directly, and the zeus zoom list starts at 0.65x, the HAL's minimum.
4. **Wrong beautify type.** The old "3D beauty" tab type is not supported by this camera version on zeus; type `11` (Smooth / Slender / Big eyes) is used instead, and the beautify ratios are sent without the vendor tag check.
5. **Portrait capture hung.** The portrait still-capture path asked for an output stream that the portrait session on zeus does not have, so the capture failed and timed out after 10 seconds. It now uses the existing stream.

**Up to 60x zoom:** the camera HAL limits digital zoom with `maxDigitalZoom` / `extendedMaxZoomRatio` in `/vendor/etc/camera/camxoverridesettings.txt`. On every boot the module copies the ROM's own file, changes only these two values to 60 and bind-mounts it over the original. Nothing on the vendor partition is changed, and the other camera files stay as they are.

All patches are listed with offsets, original bytes and reasons in [`patcher/patch.py`](patcher/patch.py).

### Build it yourself

You need the original APK `Camera 1+6.2.000360.1 com.android.camera.apk` (sha256 `662c76d61f2fbe5fb9c66454ffa7a0b42fcb1b05849657ba3f1f50649415bed3`), Python 3, Java, `zipalign`, `apksigner`, `zip` and smali / baksmali 2.3.x.

```
python3 patcher/patch.py --apk "Camera 1+6.2.000360.1 com.android.camera.apk" \
    --smali smali.jar --baksmali baksmali.jar
```

The module zip is written to `out/`. Without `--key` / `--cert` a throwaway signing key is generated.

### Credits

Thanks to everyone whose work made this possible:

- **Joshabys & joaovti**: the Xiaomi 12 (cupid) MIUI / Leica camera module ([xiaomi-12-MIUI-Leica-Camera-Module](https://github.com/joaovti/xiaomi-12-MIUI-Leica-Camera-Module)). This module's skeleton, install and mount scripts and camera libraries are based on it.
- **backslashxx**: [mountify](https://github.com/backslashxx/mountify), the base of the OverlayFS mount logic.
- **EnOt15P (4pda: EnOt.P)**: TurboOS for Xiaomi 12 Pro, used to study the HyperOS camera on zeus.
- **KyoKusanaghi**: the zeus MIUI camera device / vendor repositories, used as the working reference for comparison.
- **Zeus Lover ⚡ (@Uzumakii_naarutoo)**: for sharing the HyperOS Camera 6.2 APK in KyoKusanaghi's Telegram group.
- **TonyC**: the "Mi 12 Pro 60x zoom enable" module, which showed the camx settings behind 60x zoom.
- **JesusFreke**: smali / baksmali.
- **Xiaomi**: HyperOS Camera.

### Disclaimer

HyperOS Camera and the included camera libraries are the property of Xiaomi. This project is not affiliated with Xiaomi. Use at your own risk.

---

## Türkçe

### Özellikler

| Özellik | Durum |
|---|---|
| Leica Authentic görünümü ve Leica filtreleri (VIV / NAT / BW) | ✅ |
| Fotoğraf ve video (görüntü + ses) | ✅ |
| 0.6x geniş açı (fotoğraf ve video) | ✅ |
| 2x / 5x tele geçişleri | ✅ |
| 60x'e kadar yakınlaştırma | ✅ |
| 1080p 60 FPS video | ✅ |
| Portre (bokeh), ön ve arka kamera | ✅ |
| Güzelleştirme (Smooth / Slender / Big eyes) | ✅ * |
| Pro mod | ✅ |

\* Güzelleştirme etkisi önizlemede hafif görünür, çekilen fotoğrafa ise tam olarak uygulanır.

### Test edildiği ortam

- Xiaomi 12 Pro (zeus)
- Evolution X 12.4, Android 17 (vendor OS3.0.4.0.VLBMIXM)
- BakaSU (KernelSU tabanlı) root, SELinux Enforcing

Magisk ve APatch ile **denenmedi**. Aynı zeus vendor'ını kullanan diğer AOSP tabanlı Android 17 ROM'larda çalışması beklenir ama denenmedi.

### Kurulum

1. Xiaomi 12 (cupid) Leica modülü (`cupid-miuicamera`) kuruluysa **önce onu kaldırıp** yeniden başlat.
2. [Releases](../../releases) bölümünden `zeus-hyperos-leica-camera-aosp-v1.0.zip` dosyasını indir.
3. Root yöneticinden (KernelSU / BakaSU) kur.
4. Telefonu yeniden başlat.

Kurulum, sistemin yeni kamerayı görebilmesi için gereken Android paket önbelleği temizliğini kendisi yapar. İlk açılışta kamera uygulamasının kendi ayarları bir kez sıfırlanır (uygulama imzası değiştiği için). Fotoğraf ve videolarına dokunulmaz.

### Kaldırma

Modülü root yöneticisinden kaldır ve yeniden başlat. Paket önbelleği kendiliğinden temizlenir, ROM'un kendi kamerası geri gelir.

### Bilinen sınırlar

- Güzelleştirme etkisi önizlemede hafif görünür, çekilen fotoğrafa ise tam olarak uygulanır.
- Sadece HyperOS Kamera `1+6.2.000360.1` için yapıldı; yamalar sabit konumlara uygulanır.

### Sorun neydi, nasıl düzeldi

HyperOS kamerası bir HyperOS ROM'u bekliyor. AOSP'de birçok özelliği sessizce kapalı çalışıyordu:

1. **Eksik HyperOS çerçeve sınıfları** (`AudioParaManger`, `MiuiSettings`, `HapticFeedbackUtil`…): video modu donuyordu. Küçük taklit sınıflar eklendi (`patcher/stubs`).
2. **Xiaomi etiketleri hiç sorgulanmıyordu.** HyperOS olmayan ROM'larda kamera bütün vendor etiketleri yerine sadece `getAvailableCaptureRequestKeys()` listesine bakıyor. Bu yüzden bokeh, 1080p 60 FPS, güzelleştirme oranları, yumuşak lens geçişi, MFNR ve daha fazlası kamera katmanına hiç gönderilmiyordu. Kamera artık her zaman `getAllVendorKeys()` kullanıyor.
3. **Yakınlaştırma `zoomRatio` yerine kırpma alanıyla yapılıyordu.** Kırpmayla 1x'in altına inilemiyor: kırpma alanı negatif oluyor, Android de bunu 1.0'a çeviriyor. 0.6x bu yüzden ana lenste kalıyordu. Kamera artık doğrudan `CONTROL_ZOOM_RATIO` gönderiyor, zeus yakınlaştırma listesi de kamera katmanının alt sınırı olan 0.65x'ten başlıyor.
4. **Yanlış güzelleştirme türü.** Eski "3D güzelleştirme" türü bu kamera sürümünde zeus için desteklenmiyor. Yerine tür `11` (Smooth / Slender / Big eyes) kullanılıyor, güzelleştirme oranları da etiket kontrolü olmadan gönderiliyor.
5. **Portre çekimi donuyordu.** Portre fotoğraf çekimi, zeus'taki portre oturumunda bulunmayan bir akışı istiyordu. Çekim başarısız olup 10 saniye sonra zaman aşımına uğruyordu. Artık var olan akışı kullanıyor.

**60x'e kadar yakınlaştırma:** Kamera katmanı dijital yakınlaştırmayı `/vendor/etc/camera/camxoverridesettings.txt` içindeki `maxDigitalZoom` / `extendedMaxZoomRatio` ile sınırlıyor. Modül her açılışta ROM'un kendi dosyasını kopyalıyor, sadece bu iki değeri 60 yapıyor ve orijinalin üstüne bağlıyor. Vendor bölümünde hiçbir şey değişmiyor, diğer kamera dosyaları olduğu gibi kalıyor.

Bütün yamalar konumları, orijinal baytları ve gerekçeleriyle [`patcher/patch.py`](patcher/patch.py) içinde.

### Kendin derle

Orijinal APK `Camera 1+6.2.000360.1 com.android.camera.apk` (sha256 `662c76d61f2fbe5fb9c66454ffa7a0b42fcb1b05849657ba3f1f50649415bed3`), Python 3, Java, `zipalign`, `apksigner`, `zip` ve smali / baksmali 2.3.x gerekir.

```
python3 patcher/patch.py --apk "Camera 1+6.2.000360.1 com.android.camera.apk" \
    --smali smali.jar --baksmali baksmali.jar
```

Modül zip'i `out/` klasörüne yazılır. `--key` / `--cert` verilmezse geçici bir imza anahtarı üretilir.

### Teşekkürler

Bu çalışmayı mümkün kılan herkese teşekkürler:

- **Joshabys & joaovti**: Xiaomi 12 (cupid) MIUI / Leica kamera modülü ([xiaomi-12-MIUI-Leica-Camera-Module](https://github.com/joaovti/xiaomi-12-MIUI-Leica-Camera-Module)). Bu modülün iskeleti, kurulum ve bağlama betikleri ve kamera kütüphaneleri ona dayanıyor.
- **backslashxx**: [mountify](https://github.com/backslashxx/mountify), OverlayFS bağlama mantığının temeli.
- **EnOt15P (4pda: EnOt.P)**: Xiaomi 12 Pro için TurboOS; zeus'ta HyperOS kamerasını incelemek için kullanıldı.
- **KyoKusanaghi**: zeus MIUI kamera device / vendor depoları; karşılaştırma için çalışan referans olarak kullanıldı.
- **Zeus Lover ⚡ (@Uzumakii_naarutoo)**: HyperOS Kamera 6.2 APK'sını KyoKusanaghi'nin Telegram grubunda paylaştığı için.
- **TonyC**: 60x yakınlaştırmanın arkasındaki camx ayarlarını gösteren "Mi 12 Pro 60x zoom enable" modülü.
- **JesusFreke**: smali / baksmali.
- **Xiaomi**: HyperOS Kamera.

### Uyarı

HyperOS Kamera ve modüldeki kamera kütüphaneleri Xiaomi'nin malıdır. Bu proje Xiaomi ile bağlantılı değildir. Kullanım sorumluluğu kullanıcıya aittir.
