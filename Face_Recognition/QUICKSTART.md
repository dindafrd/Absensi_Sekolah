# 🚀 PANDUAN MULAI CEPAT
## Sistem Absensi Web - Face Recognition

### ⚡ Instalasi Cepat (5 Menit)

#### 1. Install dependency
```bash
pip install -r requirements_web.txt
```

Jika error di Windows, download dlib wheel:
- https://github.com/jloh02/dlib/releases
```bash
pip install dlib-19.24.99-cp311-cp311-win_amd64.whl
pip install -r requirements_web.txt
```

#### 2. Jalankan server
```bash
python run.py
```

#### 3. Buka Browser
```
http://localhost:5000
```

---

### 📝 Penggunaan

#### **LANGKAH 1: Tambah Siswa**
1. Menu **"Siswa"** → **"Tambah Siswa"**
2. Isi form (NIS, Nama, Kelas)
3. Upload 3-5 foto siswa
4. Klik **"Daftarkan Siswa"**

#### **LANGKAH 2: Absensi**
1. Menu **"Absensi"**
2. Izinkan akses kamera
3. Siswa di depan kamera
4. Klik **"Capture & Mark Attendance"**

#### **LANGKAH 3: Lihat Laporan**
1. Menu **"Laporan"**
2. Pilih filter tanggal
3. Klik **"Export Excel"**

---

### 📁 Struktur file
```
├── app.py                 # Compatibility launcher
├── run.py                 # Primary entrypoint
├── requirements_web.txt   # Dependency list
├── app/                   # App package (routes, templates, services)
└── data/                  # Database & photos
```

---

### 🔧 Masalah Umum

**Kamera tidak bisa diakses?**
- Cek permission browser
- Tutup aplikasi lain yang pakai kamera

**Wajah tidak terdeteksi?**
- Perbaiki pencahayaan
- Jarak 50-100 cm dari kamera
- Gunakan foto training dengan kualitas baik

**Port 5000 sudah dipakai?**
Set env variable sebelum run:
```bash
# PowerShell
$env:PORT=5001
python run.py
```

---

### 💡 Tips foto siswa

**✅ GOOD:**
- Pencahayaan baik
- Wajah jelas
- 3-5 foto berbeda sudut

**❌ BAD:**
- Foto dengan masker
- Terlalu gelap/terang
- Blur/tidak fokus

---

### 🌐 Akses dari jaringan

1. Cari IP komputer:
   ```bash
   ipconfig    # Windows
   ifconfig    # Linux/Mac
   ```

2. Akses dari device lain:
   ```
   http://192.168.1.XXX:5000
   ```

---

### 📞 Butuh Bantuan?

- Baca **README_WEB.md** untuk detail lengkap
- Cek bagian troubleshooting
- Buat issue di repository

---

**Siap digunakan! 🎉**

Buka http://localhost:5000 dan mulai gunakan sistem!
