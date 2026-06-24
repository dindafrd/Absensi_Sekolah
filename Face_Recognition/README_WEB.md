# 🎓 Sistem Absensi Sekolah Berbasis Web
## Face Recognition dengan Python Flask

Sistem absensi otomatis menggunakan teknologi pengenalan wajah (Face Recognition) yang dapat diakses melalui browser web. Sistem ini dibangun dengan Flask, OpenCV, dan Deep Learning.

---

## 📋 Fitur Utama

### ✨ **Dashboard Interaktif**
- Statistik real-time kehadiran siswa
- Grafik dan visualisasi data
- Quick actions untuk akses cepat

### 👤 **Manajemen Siswa**
- Tambah siswa baru dengan upload foto
- Drag & drop upload foto
- Database siswa lengkap dengan foto profil
- Pencarian dan filter siswa

### 📷 **Absensi Real-time**
- Deteksi wajah menggunakan webcam
- Pengenalan wajah otomatis
- Live preview dengan bounding box
- One-click attendance marking

### 📊 **Laporan & Analytics**
- Filter berdasarkan tanggal dan kelas
- Export ke Excel
- Statistik kehadiran
- Riwayat absensi lengkap

---

## 🛠️ Teknologi yang Digunakan

### Backend
- **Flask 3.0** - Python web framework
- **OpenCV** - Computer vision
- **face_recognition** - Deep learning face recognition
- **dlib** - Machine learning toolkit
- **pandas** - Data analysis
- **openpyxl** - Excel export

### Frontend
- **HTML5 & CSS3** - Modern responsive design
- **JavaScript (Vanilla)** - Dynamic interactions
- **Font Awesome** - Icons
- **Google Fonts** - Typography (Outfit, Space Mono)

---

## 📦 Instalasi

### Persyaratan Sistem
- Python 3.8 atau lebih baru
- Webcam (untuk face recognition)
- RAM minimal 4GB (recommended 8GB)
- Windows / Linux / macOS

### Langkah Instalasi

#### 1. Clone atau Download Project
```bash
git clone <repository-url>
cd face-recognition-attendance-web
```

#### 2. Buat Virtual Environment (Optional tapi Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

**Untuk Linux/Mac:**
```bash
pip install -r requirements_web.txt
```

**Untuk Windows:**

Ada beberapa cara instalasi untuk Windows:

**Cara 1: Menggunakan pip (mudah tapi kadang error)**
```bash
pip install cmake
pip install dlib
pip install -r requirements_web.txt
```

**Cara 2: Install dlib dari wheel file (RECOMMENDED)**

1. Download dlib wheel file dari: https://github.com/jloh02/dlib/releases
2. Pilih sesuai Python version (contoh: `dlib-19.24.99-cp311-cp311-win_amd64.whl` untuk Python 3.11)
3. Install:
```bash
pip install dlib-19.24.99-cp311-cp311-win_amd64.whl
pip install -r requirements_web.txt
```

**Cara 3: Menggunakan Anaconda (paling stabil)**
```bash
conda install -c conda-forge dlib
pip install -r requirements_web.txt
```

#### 4. Verifikasi Instalasi
```bash
python -c "import flask, cv2, face_recognition; print('Instalasi berhasil!')"
```

---

## 🚀 Cara Menjalankan

### 1. Jalankan Server
```bash
python run.py
```

Catatan: `python app.py` masih didukung sebagai compatibility launcher, tapi entrypoint utama adalah `run.py`.

Output yang akan muncul:
```
==================================================================
 WEB-BASED FACE RECOGNITION ATTENDANCE SYSTEM
==================================================================

Starting server...
Access the application at: http://localhost:5000

Press CTRL+C to stop the server
==================================================================
```

### 2. Akses di Browser
Buka browser dan kunjungi:
```
http://localhost:5000
```

atau jika dari komputer lain di jaringan yang sama:
```
http://<IP-ADDRESS>:5000
```

### 3. Workflow Penggunaan

#### **A. Tambah Siswa**
1. Klik menu **"Siswa"** > **"Tambah Siswa"**
2. Isi data siswa:
   - NIS/ID Siswa (contoh: STD001)
   - Nama Lengkap
   - Kelas
3. Upload 3-5 foto siswa:
   - Klik atau drag & drop foto
   - Foto dengan pencahayaan baik
   - Wajah terlihat jelas
   - Berbagai sudut (depan, kiri, kanan)
4. Klik **"Daftarkan Siswa"**

#### **B. Jalankan Absensi**
1. Klik menu **"Absensi"**
2. Izinkan akses kamera saat diminta browser
3. Siswa berdiri di depan kamera
4. Sistem otomatis mendeteksi wajah (box hijau = dikenali)
5. Klik **"Capture & Mark Attendance"**
6. Sistem mencatat kehadiran otomatis

#### **C. Lihat Laporan**
1. Klik menu **"Laporan"**
2. Gunakan filter:
   - Pilih rentang tanggal
   - Filter berdasarkan kelas
   - Preset: Hari Ini / Minggu Ini / Bulan Ini
3. Klik **"Export Excel"** untuk download laporan

---

## 📁 Struktur Project

```
face-recognition-attendance-web/
│
├── run.py                      # Primary Flask entrypoint
├── app.py                      # Compatibility launcher
├── requirements_web.txt        # Python dependencies
├── README_WEB.md               # Dokumentasi ini
│
├── app/
│   ├── __init__.py             # App factory + blueprint registration
│   ├── config.py               # Configuration
│   ├── models/
│   │   └── models.py           # SQLAlchemy models
│   ├── routes/                 # Route blueprints
│   │   ├── auth.py
│   │   ├── main.py
│   │   ├── students.py
│   │   ├── attendance.py
│   │   └── reports.py
│   ├── services/               # Camera/face/db/rate-limit services
│   ├── templates/              # HTML templates
│   └── static/                 # Static files
│
└── data/                       # Application data (SQLite, uploads, logs)
```

---

## ❤️ Monitoring Endpoint

- `GET /health` untuk status umum aplikasi (database, kamera, recognition flag)
- `GET /ready` untuk readiness probe (fokus kesiapan database)

Contoh:
```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/ready
```

---

## 🔐 Catatan Keamanan

- Login fallback berbasis password config **dinonaktifkan default**.
- Aktifkan hanya untuk emergency dengan env:
```bash
ENABLE_CONFIG_ADMIN_LOGIN=1
ADMIN_PASSWORD=<strong-password-or-bcrypt-hash>
```
- Disarankan login menggunakan akun admin di database (`users`).

---

## 💡 Tips & Best Practices

### Foto Siswa yang Baik

#### ✅ DO (Lakukan):
- Pencahayaan yang baik dan merata
- Wajah terlihat jelas, tidak blur
- Ambil dari berbagai sudut (depan, kiri sedikit, kanan sedikit)
- Ekspresi wajah natural
- Background yang bersih
- Minimal 3 foto per siswa (ideal 5 foto)

#### ❌ DON'T (Hindari):
- Foto dengan masker
- Kacamata hitam
- Topi yang menutupi wajah
- Pencahayaan terlalu gelap/terang
- Foto blur atau tidak fokus
- Wajah tertutup objek lain

### Penggunaan Kamera
- Posisi kamera setinggi wajah atau sedikit di atas
- Jarak ideal 50-100 cm dari kamera
- Pastikan background tidak terlalu ramai
- Pencahayaan dari depan, bukan dari belakang
- Gunakan resolusi kamera minimal 720p

### Performa Sistem
- Gunakan komputer dengan RAM minimal 4GB
- Browser modern (Chrome, Firefox, Edge terbaru)
- Koneksi kamera yang stabil
- Update foto siswa jika ada perubahan penampilan signifikan

---

## 🔧 Troubleshooting

### Error: "Could not access camera"
**Solusi:**
1. Pastikan browser memiliki izin akses kamera
2. Tutup aplikasi lain yang menggunakan kamera
3. Coba browser yang berbeda
4. Restart komputer jika perlu

### Error: "No module named 'face_recognition'"
**Solusi:**
```bash
pip install face-recognition
```

### Error: "dlib installation failed"
**Solusi untuk Windows:**
1. Download wheel file: https://github.com/jloh02/dlib/releases
2. Install manual:
```bash
pip install dlib-19.24.99-cp311-cp311-win_amd64.whl
```

**Solusi untuk Linux:**
```bash
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev
pip install dlib
```

### Wajah tidak terdeteksi
**Solusi:**
1. Perbaiki pencahayaan ruangan
2. Pastikan wajah menghadap kamera
3. Kurangi jarak dari kamera (50-100cm)
4. Bersihkan lensa kamera
5. Update foto training dengan kualitas lebih baik

### Sistem lambat / lag
**Solusi:**
1. Tutup aplikasi lain yang berat
2. Gunakan browser yang lebih ringan
3. Kurangi resolusi webcam di `app.py`:
```python
stream = await navigator.mediaDevices.getUserMedia({ 
    video: { 
        width: 640,   # Ubah dari 1280
        height: 480   # Ubah dari 720
    } 
});
```

### Port 5000 sudah digunakan
**Solusi:**
Edit `app.py` baris terakhir:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Ganti port
```

---

## 🌐 Akses dari Jaringan Lokal

Untuk mengakses dari komputer/HP lain di jaringan yang sama:

### 1. Cari IP Address komputer server
**Windows:**
```bash
ipconfig
# Cari "IPv4 Address"
```

**Linux/Mac:**
```bash
ifconfig
# atau
ip addr show
```

### 2. Akses dari device lain
```
http://192.168.1.XXX:5000
```
(Ganti XXX dengan IP address yang ditemukan)

### 3. Firewall
Pastikan firewall mengizinkan koneksi ke port 5000:

**Windows:**
```bash
netsh advfirewall firewall add rule name="Flask App" dir=in action=allow protocol=TCP localport=5000
```

---

## 📊 Format Data

### Database Siswa (students.json)
```json
{
    "STD001": {
        "name": "Ahmad Rizki Pratama",
        "class": "12 IPA 1",
        "added_date": "2025-01-14",
        "num_photos": 5,
        "photos": [
            "data/students/STD001/photo_1.jpg",
            "data/students/STD001/photo_2.jpg"
        ]
    }
}
```

### Data Absensi (attendance.csv)
```csv
StudentID,Name,Class,Date,Time,Status
STD001,Ahmad Rizki Pratama,12 IPA 1,2025-01-14,07:30:15,Present
STD002,Siti Nurhaliza,12 IPA 1,2025-01-14,07:31:22,Present
```

---

## 🔐 Security Notes

### Untuk Production:
1. **Ganti Secret Key** di `app.py`:
```python
app.secret_key = 'your-very-secret-key-here-change-this'
```

2. **Matikan Debug Mode**:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

3. **Gunakan HTTPS** (SSL/TLS)

4. **Tambahkan Authentication** untuk akses admin

5. **Backup Data** secara berkala

---

## 🎯 Fitur Mendatang (Roadmap)

- [ ] User authentication & authorization
- [ ] Multi-camera support
- [ ] SMS/Email notification
- [ ] Mobile app (Android/iOS)
- [ ] Cloud storage integration
- [ ] Advanced analytics & charts
- [ ] Automatic backup system
- [ ] API endpoints untuk integrasi
- [ ] Dark/Light theme toggle

---

## 📞 Support & Kontribusi

### Butuh Bantuan?
- Buat issue di repository
- Email: support@example.com

### Ingin Berkontribusi?
- Fork repository
- Buat branch baru
- Submit pull request

---

## 📝 Lisensi

MIT License - Bebas digunakan untuk keperluan pendidikan dan komersial

---

## ⚠️ Catatan Penting

1. **Privasi Data**: Pastikan mematuhi peraturan privasi data di wilayah Anda
2. **Informed Consent**: Dapatkan izin dari siswa/wali untuk menggunakan foto
3. **Data Security**: Simpan data siswa dengan aman
4. **Regular Backup**: Backup database secara berkala
5. **Internet Access**: Tidak memerlukan internet untuk operasi normal (hanya untuk install)

---

## 🙏 Credits

- **Flask** - Web framework
- **face_recognition** - Face recognition library by Adam Geitgey
- **OpenCV** - Computer vision library
- **dlib** - Machine learning toolkit
- **Font Awesome** - Icon library
- **Google Fonts** - Web fonts

---

**Dibuat untuk kemajuan pendidikan Indonesia**

**Version:** 1.0.0  
**Last Updated:** Januari 2025
