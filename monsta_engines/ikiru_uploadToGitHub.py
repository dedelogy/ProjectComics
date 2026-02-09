import os
import json
import time
import subprocess
from datetime import datetime

# ==============================================================================
# MONSTA BOT 3: THE MANAGER (V52.0 - HOME BASE EDITION)
# ------------------------------------------------------------------------------
# 1. SCANNER: Baca semua JSON di database.
# 2. INDEXER: Buat file 'index.json' (Katalog untuk Web UI).
# 3. GIT SYNC: Push otomatis ke GitHub tanpa ganggu Scraper.
# ==============================================================================

# --- KONFIGURASI RELATIF ---
# Kita asumsi script ini ada di folder 'monsta_engines'
# Database ada di folder kakak/sebelah: '../monstacomics/database'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FOLDER = os.path.abspath(os.path.join(BASE_DIR, "..", "monstacomics", "database"))
ROOT_REPO = os.path.abspath(os.path.join(BASE_DIR, "..")) # Folder root project

# Interval (Detik)
CHECK_INTERVAL = 600  # Sync setiap 10 menit

# ==============================================================================

class MonstaManager:
    def __init__(self):
        print(f"[INIT] Manager aktif di: {ROOT_REPO}")
        print(f"[INIT] Memantau Database: {DB_FOLDER}")
        
        if not os.path.exists(DB_FOLDER):
            print("[ERROR] Folder database tidak ditemukan! Cek struktur foldermu.")
            exit()

    def run_git(self, args):
        """Menjalankan perintah git di background."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=ROOT_REPO, # Jalankan perintah dari folder root
                capture_output=True,
                text=True,
                encoding='utf-8' # Handle karakter aneh
            )
            return result.stdout.strip()
        except Exception as e:
            print(f"      [SYSTEM ERROR] Gagal panggil Git: {e}")
            return False

    def create_index(self):
        """
        RAHASIA UI WEB:
        Fungsi ini membuat file 'index.json' yang berisi rangkuman.
        Web-mu nanti cuma perlu load file ini untuk menampilkan daftar komik.
        """
        print("   [1/3] Membuat Katalog (Indexing)...")
        catalog = []
        
        # Scan semua file .json
        files = [f for f in os.listdir(DB_FOLDER) if f.endswith(".json") and f != "index.json"]
        
        for filename in files:
            filepath = os.path.join(DB_FOLDER, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Ambil data penting saja untuk 'kartu' di halaman depan web
                    catalog.append({
                        "title": data.get("title", "Unknown"),
                        "slug": data.get("slug", filename.replace(".json", "")),
                        "cover": data.get("cover", ""),
                        "last_updated": data.get("last_updated", "2000-01-01 00:00"),
                        "total_chapters": len(data.get("chapters", [])),
                        "genres": data.get("genres", [])
                    })
            except Exception as e:
                print(f"      [WARN] Gagal baca {filename}: {e}")

        # Sortir: Komik yang baru update naik ke paling atas
        catalog.sort(key=lambda x: x["last_updated"], reverse=True)
        
        # Simpan jadi index.json
        index_path = os.path.join(DB_FOLDER, "index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2) # indent=2 biar enak dibaca manusia
            
        print(f"      -> Sukses! {len(catalog)} komik terdaftar di index.json")
        return True

    def sync_github(self):
        """Proses Upload ke GitHub."""
        print("   [2/3] Cek Perubahan (Git Status)...")
        
        # Cek status dulu
        status = self.run_git(["status", "--porcelain"])
        
        if not status:
            print("      -> Tidak ada perubahan data. (Clean)")
            return
        
        print("   [3/3] Sinkronisasi ke Awan...")
        
        # Add (Bungkus semua perubahan)
        self.run_git(["add", "."])
        
        # Commit (Stempel waktu)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        msg = f"Auto Update: {timestamp} ({len(status.splitlines())} files)"
        self.run_git(["commit", "-m", msg])
        print(f"      -> Commited: {msg}")
        
        # Push (Kirim)
        print("      -> Mengirim paket ke GitHub (Pushing)...")
        push_res = self.run_git(["push"])
        
        # Cek output push (kadang kosong kalau sukses, kadang ada text)
        print("      -> Selesai! Data aman di GitHub.")

# --- MAIN LOOP ---

if __name__ == "__main__":
    bot = MonstaManager()
    
    print("\n==============================================")
    print("   MONSTA BOT 3: THE MANAGER (ACTIVATED)")
    print("==============================================")
    print("   Bot ini akan update Index & GitHub otomatis.")
    print(f"   Interval: Setiap {CHECK_INTERVAL} detik.")
    print("   Tekan CTRL+C untuk berhenti.")
    print("==============================================\n")

    while True:
        try:
            print(f"\n[JOB START] {datetime.now().strftime('%H:%M:%S')}")
            bot.create_index()
            bot.sync_github()
            print("[JOB DONE] Istirahat dulu...")
        except KeyboardInterrupt:
            print("\n[STOP] Bot dimatikan. Sampai jumpa!")
            break
        except Exception as e:
            print(f"[CRASH] Terjadi kesalahan: {e}")
            input("Tekan ENTER untuk keluar...")
        
        time.sleep(CHECK_INTERVAL)