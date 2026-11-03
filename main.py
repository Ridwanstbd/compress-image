import os
import threading
import queue
import argparse
import shutil
import subprocess
import time
from PIL import Image

def convert_and_compress_to_webp(input_path, output_path, target_size_kb=200):
    """Fungsi inti untuk mengonversi satu gambar ke WebP dengan target ukuran."""
    try:
        with Image.open(input_path) as img:
            if img.mode in ("P", "CMYK"):
                if 'transparency' in img.info:
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

            # Tahap 1: Resize gambar jika resolusinya terlalu besar untuk memangkas ukuran dasar
            # tanpa terlalu mengurangi detail visual (max 1920px)
            max_dim = 1920
            if img.width > max_dim or img.height > max_dim:
                if hasattr(Image, 'Resampling'):
                    resample_filter = Image.Resampling.LANCZOS
                else:
                    resample_filter = getattr(Image, 'ANTIALIAS', 1)
                img.thumbnail((max_dim, max_dim), resample_filter)

            # Tahap 2: Kompresi iteratif untuk mencapai target ukuran
            quality = 90
            while quality >= 10:
                img.save(
                    output_path, 
                    format="webp", 
                    quality=quality, 
                    lossless=False,
                    method=6
                )
                new_size = os.path.getsize(output_path) / 1024
                if new_size <= target_size_kb:
                    break
                quality -= 5 # Turunkan kualitas secara bertahap
        
        original_size = os.path.getsize(input_path) / 1024
        print(f"[Sukses] {os.path.basename(input_path)} -> {new_size:.1f} KB (dari {original_size:.1f} KB) [Q={quality}]")
        
    except Exception as e:
        print(f"[Error] Gagal memproses {os.path.basename(input_path)}: {e}")

def worker(task_queue):
    """
    Fungsi worker yang akan berjalan di dalam thread. 
    Mengambil tugas dari antrean (queue) dan mengeksekusinya.
    """
    while True:
        task = task_queue.get()
        
        # Jika menerima sinyal 'None', hentikan worker
        if task is None:
            break
            
        input_path, output_path, target_size_kb = task
        convert_and_compress_to_webp(input_path, output_path, target_size_kb)
        
        # Menandai bahwa satu tugas telah selesai dikerjakan
        task_queue.task_done()

def mass_convert_with_queue(input_dir, output_dir, num_workers=4, target_size_kb=200):
    """
    Menyiapkan antrean gambar dan menjalankan worker thread untuk pemrosesan massal.
    """
    # Ekstensi file yang didukung untuk diproses
    supported_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif')
    
    if not os.path.exists(input_dir):
        print(f"Error: Folder input '{input_dir}' tidak ditemukan.")
        return
        
    # Membuat folder output jika belum ada
    os.makedirs(output_dir, exist_ok=True)

    # Membuat antrean (queue)
    task_queue = queue.Queue()
    
    # Menyiapkan list untuk menyimpan referensi thread
    threads = []

    # 1. Menjalankan worker threads
    for _ in range(num_workers):
        t = threading.Thread(target=worker, args=(task_queue,))
        t.start()
        threads.append(t)

    # 2. Memasukkan semua gambar dari folder ke dalam antrean
    file_count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_extensions):
            input_path = os.path.join(input_dir, filename)
            
            # Mengganti ekstensi lama dengan .webp untuk nama file output
            filename_without_ext = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{filename_without_ext}.webp")
            
            # Memasukkan tugas ke queue
            task_queue.put((input_path, output_path, target_size_kb))
            file_count += 1

    print(f"Memulai pemrosesan {file_count} gambar dengan {num_workers} worker threads...\n" + "-"*50)
    start_time = time.time()

    # 3. Menunggu semua tugas di antrean selesai
    task_queue.join()

    # 4. Menghentikan semua worker (mengirim sinyal None)
    for _ in range(num_workers):
        task_queue.put(None)
        
    for t in threads:
        t.join()

    end_time = time.time()
    print("-" * 50)
    print(f"Selesai! Semua gambar berhasil diproses dalam {end_time - start_time:.2f} detik.")


# ================== F A S I L I T A S  V I D E O ==================

def get_ffmpeg_path():
    """Mengembalikan path ffmpeg: pakai ffmpeg sistem jika ada, 
    jika tidak, gunakan binary yang dibundel pakage imageio-ffmpeg."""
    ffmpeg_system = shutil.which("ffmpeg")
    if ffmpeg_system:
        return ffmpeg_system

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return None


def compress_video_to_webm(input_path, output_path, crf=34):
    """Fungsi inti untuk mengonversi satu video ke .webm (codec VP9 + audio Opus)
    menggunakan ffmpeg. CRF menentukan kualitas: semakin kecil semakin bagus (18-40)."""
    try:
        ffmpeg = get_ffmpeg_path()
        if not ffmpeg:
            raise RuntimeError(
                "ffmpeg tidak ditemukan. Install imageio-ffmpeg: pip install imageio-ffmpeg"
            )

        cmd = [
            ffmpeg,
            "-y",              # Timpa file output jika sudah ada
            "-hide_banner",
            "-loglevel", "error",
            "-i", input_path,
            "-c:v", "libvpx-vp9",   # Codec video VP9 (format WebM)
            "-crf", str(crf),       # Kualitas tetap (constant rate factor)
            "-b:v", "0",            # CRF mode (tanpa bit-rate tetap)
            "-row-mt", "1",         # Multithreading baris agar encoder lebih cepat
            "-deadline", "good",
            "-cpu-used", "4",       # Keseimbangan kecepatan vs ukuran
            "-c:a", "libopus",      # Codec audio Opus (diabaikan jika video tanpa audio)
            "-b:a", "96k",
            "-pix_fmt", "yuv420p",  # Pastikan pixel format standar agar bisa dimainkan semua pemain
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip()[-500:])

        original_size = os.path.getsize(input_path) / (1024 * 1024)
        new_size = os.path.getsize(output_path) / (1024 * 1024)
        print(
            f"[Sukses] {os.path.basename(input_path)} -> "
            f"{new_size:.2f} MB (dari {original_size:.2f} MB) [CRF={crf}]"
        )

    except Exception as e:
        print(f"[Error] Gagal memproses {os.path.basename(input_path)}: {e}")


def video_worker(task_queue):
    """Fungsi worker video: mengambil tugas dari antrean dan memprosesnya
    dengan ffmpeg. Setiap ffmpeg sendiri sudah multithread, jadi jumlah
    worker video lebih sedikit dibandingkan mode gambar."""
    while True:
        task = task_queue.get()

        if task is None:
            break

        input_path, output_path, crf = task
        compress_video_to_webm(input_path, output_path, crf)

        task_queue.task_done()


def mass_convert_videos_with_queue(input_dir, output_dir, num_workers=2, crf=34):
    """
    Menyiapkan antrean video dan menjalankan worker thread untuk pemrosesan massal.
    """
    # Ekstensi video yang didukung untuk diproses
    supported_extensions = (
        '.mp4', '.mov', '.avi', '.mkv', '.webm', '.wmv', '.flv', '.m4v',
        '.ts', '.mpg', '.mpeg', '.3gp', '.hevc', '.mts', '.m2ts', '.ogv',
        '.divx', '.mxf', '.vob'
    )

    if not os.path.exists(input_dir):
        print(f"Error: Folder input '{input_dir}' tidak ditemukan.")
        return

    if get_ffmpeg_path() is None:
        print("Error: ffmpeg tidak ditemukan. Jalankan: pip install imageio-ffmpeg")
        return

    # Membuat folder output jika belum ada
    os.makedirs(output_dir, exist_ok=True)

    # Membuat antrean (queue)
    task_queue = queue.Queue()

    # Menyiapkan list untuk menyimpan referensi thread
    threads = []

    # 1. Menjalankan worker threads
    for _ in range(num_workers):
        t = threading.Thread(target=video_worker, args=(task_queue,))
        t.start()
        threads.append(t)

    # 2. Memasukkan semua video dari folder ke dalam antrean
    file_count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(supported_extensions):
            input_path = os.path.join(input_dir, filename)

            # Mengganti ekstensi lama dengan .webm untuk nama file output
            filename_without_ext = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{filename_without_ext}.webm")

            task_queue.put((input_path, output_path, crf))
            file_count += 1

    print(f"Memulai pemrosesan {file_count} video dengan {num_workers} worker threads...\n" + "-"*50)
    start_time = time.time()

    # 3. Menunggu semua tugas di antrean selesai
    task_queue.join()

    # 4. Menghentikan semua worker (mengirim sinyal None)
    for _ in range(num_workers):
        task_queue.put(None)

    for t in threads:
        t.join()

    end_time = time.time()
    print("-" * 50)
    print(f"Selesai! Semua video berhasil diproses dalam {end_time - start_time:.2f} detik.")


# --- Cara Penggunaan ---
if __name__ == "__main__":
    # Path dasar diambil dari lokasi file main.py agar tidak tergantung tempat project disimpan
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Parsing argumen terminal:
    #   python main.py          -> mode gambar (input/ -> output/ jika .webp)
    #   python main.py -video   -> mode video  (video/input/ -> video/output/ jika .webm)
    parser = argparse.ArgumentParser(description="Kompresi massal gambar (.webp) atau video (.webm)")
    parser.add_argument(
        "-video",
        action="store_true",
        help="Aktifkan mode kompresi video: video/input/ -> video/output/ (.webm)"
    )
    args = parser.parse_args()

    if args.video:
        # Tentukan folder sumber (tempat video asli berkumpul)
        FOLDER_INPUT_VIDEO = os.path.join(BASE_DIR, "video", "input")

        # Tentukan folder tujuan (tempat hasil .webm akan disimpan)
        FOLDER_OUTPUT_VIDEO = os.path.join(BASE_DIR, "video", "output")

        # Menjalankan fungsi massal video dengan queue
        # num_workers: Setiap ffmpeg sudah multithread, 2 worker paralel sudah efisien.
        # crf: Kualitas video, semakin kecil semakin bagus & besar ukurannya (18-40).
        mass_convert_videos_with_queue(
            input_dir=FOLDER_INPUT_VIDEO,
            output_dir=FOLDER_OUTPUT_VIDEO,
            num_workers=2,
            crf=34
        )
    else:
        # Tentukan folder sumber (tempat gambar asli berkumpul)
        FOLDER_INPUT = os.path.join(BASE_DIR, "input")

        # Tentukan folder tujuan (tempat hasil .webp akan disimpan)
        FOLDER_OUTPUT = os.path.join(BASE_DIR, "output")

        # Menjalankan fungsi massal dengan queue
        # num_workers: Jumlah thread yang berjalan paralel.
        # Sesuaikan dengan jumlah core CPU Anda (misal 4 atau 8) agar lebih cepat.
        mass_convert_with_queue(
            input_dir=FOLDER_INPUT,
            output_dir=FOLDER_OUTPUT,
            num_workers=4,
            target_size_kb=200
        )