# 🌍 Dynamic Map Viewer

Aplikasi Streamlit untuk memvisualisasikan titik lokasi dari file Excel di atas peta interaktif menggunakan **Folium**.  
Kamu dapat mengupload file Excel, memfilter data berdasarkan kolom, dan menandai titik lokasi dengan warna khusus.

## 🚀 Fitur Utama

- Upload file Excel dengan kolom **Latitude** dan **Longitude** (wajib).
- Bebas memilih kolom mana pun sebagai **nama titik**.
- Pilihan otomatis untuk memfilter berdasarkan kolom dengan nilai unik ≤ 100.
- Pemberian warna khusus pada titik tertentu berdasarkan nama titik.
- Dukungan clustering marker untuk tampilan yang lebih rapi.
- Menampilkan lingkaran radius pada titik tertentu.
- Simpan dan muat ulang pengaturan lewat file JSON.
- Download kembali data yang telah difilter dan diberi warna ke Excel.

## 📦 Struktur Project

```
dynamic-map-viewer/
│
├── app.py                  # Aplikasi Streamlit utama
├── requirements.txt        # Daftar dependensi
├── README.md               # Dokumentasi ini

```

## 📁 Format File Excel

File Excel minimal harus memiliki kolom:

- `Latitude`
- `Longitude`

Kolom opsional lainnya:
- Kolom nama titik (misalnya: `KCP`, `Nama`, `Lokasi`, dll)
- `Warna` – jika ingin langsung memberi warna tanpa konfigurasi manual.

## 🛠 Cara Menjalankan

1. Clone repository ini atau download project-nya.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Jalankan aplikasi:

```bash
streamlit run app.py
```

## 🌐 Deploy Gratis (Opsional)

Kamu bisa deploy aplikasi ini secara gratis ke:
- [Streamlit Community Cloud](https://streamlit.io/cloud)

Cukup upload repo ke GitHub, lalu hubungkan dengan Streamlit Cloud.

## 📄 Simpan & Muat Konfigurasi

- Gunakan tombol **Simpan Progress (JSON)** untuk menyimpan data + pengaturan.
- Di lain waktu, upload kembali file JSON untuk melanjutkan dari sesi sebelumnya.

## 📤 Export Data

- Setelah memberi warna & filter, download hasilnya ke Excel dengan tombol:

  > ⬇️ **Download Seluruh Data (Excel)**

---
