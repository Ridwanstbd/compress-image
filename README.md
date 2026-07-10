# Image Compressor to WebP

Script Python untuk melakukan konversi massal (bulk convert) dan kompresi gambar (PNG, JPG, JPEG, dll) ke format `.webp`. Script ini dirancang khusus agar ukuran gambar output selalu **kurang dari 200KB** (meskipun file asli berukuran lebih dari 5MB) dengan tetap mempertahankan kualitas visual yang optimal melalui metode *resizing otomatis* (maksimal dimensi 1920px) dan *kompresi kualitas iteratif*.

## 📋 Prasyarat Sistem

Sebelum menggunakan script ini, pastikan **Python** telah terinstall di PC atau Laptop Anda. 

- Jika belum, silakan download dan install Python versi terbaru melalui situs resminya: [python.org/downloads](https://www.python.org/downloads/).
- **Penting bagi pengguna Windows:** Saat proses instalasi, pastikan untuk mencentang opsi **"Add python.exe to PATH"** agar perintah `python` dan `pip` dapat dikenali di Terminal.

## 📥 Cara Download Kode

Anda bisa mengunduh kode ini dengan salah satu cara berikut:

**Opsi 1: Menggunakan Git (Command Line)**
1. Buka Terminal (Command Prompt / PowerShell / Git Bash).
2. Jalankan perintah:
   ```bash
   git clone <URL_REPOSITORY_INI>
   ```
3. Pindah ke direktori folder yang sudah di-clone:
   ```bash
   cd compress-image
   ```

**Opsi 2: Download ZIP**
1. Klik tombol hijau bertuliskan **Code** di bagian atas halaman repositori ini.
2. Pilih **Download ZIP**.
3. Ekstrak file ZIP tersebut di PC Anda.
4. Buka Terminal (Command Prompt / PowerShell) lalu arahkan ke folder hasil ekstraksi (`cd path\ke\folder\compress-image`).

## ⚙️ Instalasi Library

Script ini memerlukan library eksternal `Pillow` untuk memproses gambar. Install library tersebut dengan menjalankan perintah berikut di Terminal:

```bash
pip install Pillow
```

## 🚀 Cara Penggunaan

1. **Siapkan Folder Gambar**
   Siapkan sebuah folder yang berisi kumpulan foto/gambar yang ingin dikompres (contoh folder: `test-big-size`).

2. **Atur Input & Output di `main.py`**
   Buka file `main.py` menggunakan Text Editor pilihan Anda (misalnya VS Code atau Notepad). Scroll ke bagian paling bawah dan sesuaikan baris berikut dengan nama folder Anda:
   ```python
   if __name__ == "__main__":
       # Tentukan folder sumber (tempat gambar asli berkumpul)
       FOLDER_INPUT = "test-big-size" 

       # Tentukan folder tujuan (tempat hasil .webp akan disimpan)
       FOLDER_OUTPUT = "test-big-size-done"
   ```

3. **Jalankan Script**
   Lewat Terminal yang sudah berada di dalam folder proyek, ketikkan perintah:
   ```bash
   python main.py
   ```

4. **Selesai!**
   Script akan memproses semua gambar menggunakan *multi-threading* (default 4 *workers*) agar proses konversi jauh lebih cepat. Anda bisa memantau kemajuan ukuran *(size)* file secara realtime di Terminal. Setelah selesai, cek hasilnya di folder tujuan (`test-big-size-done`).
