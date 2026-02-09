import os
import json
import time
import subprocess
from datetime import datetime

# ==============================================================================
# MONSTA BOT 3: THE MANAGER (V52.5 - PATH FINDER EDITION)
# ------------------------------------------------------------------------------
# PRINSIP: NO CHEAP SOLUTIONS - FULL CODE EXECUTION
# TARGET: Fix WinError 2 & Auto-Push to GitHub
# ==============================================================================

# --- KONFIGURASI PATH ABSOLUT ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_REPO = os.path.abspath(os.path.join(BASE_DIR, "..")) 
DB_FOLDER = os.path.join(ROOT_REPO, "monstacomics", "database")

# Interval Sinkronisasi
CHECK_INTERVAL = 60 

class MonstaManager:
    def __init__(self):
        print(f"--- [SYSTEM START] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
        print(f"[PATH] Root Repository : {ROOT_REPO}")
        print(f"[PATH] Database Target : {DB_FOLDER}")
        
        # 1. Validasi Folder Database
        if not os.path.exists(DB_FOLDER):
            print(f"[CRITICAL ERROR] Folder database tidak ditemukan!")
            exit(1)

        # 2. Validasi Keberadaan Git
        if not self.check_git():
            print("\n" + "!"*50)
            print("[CRITICAL ERROR] GIT MASIH TIDAK DITEMUKAN!")
            print("Windows tetap tidak mengenal perintah 'git'.")
            print("-"*50)
            print("SOLUSI:")
            print("1. Pastikan Git sudah diinstal dari git-scm.com")
            print("2. RESTART PC jika terminal masih tidak mengenali git.")
            print("!"*50 + "\n")
            exit(1)

    def check_git(self):
        """Mengecek apakah perintah git bisa dipanggil."""
        try:
            subprocess.run(["git", "--version"], capture_output=True, shell=True, check=True)
            return True
        except:
            return False

    def run_git(self, args):
        """Eksekutor perintah Git dengan mode shell=True untuk Windows."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=ROOT_REPO,
                capture_output=True,
                text=True,
                encoding='utf-8',
                shell=True 
            )
            
            if result.returncode != 0:
                print(f"      [GIT ERROR] Perintah: git {' '.join(args)}")
                print(f"      [DETAIL] {result.stderr.strip()}")
                return False
            return result.stdout.strip()
        except Exception as e:
            print(f"      [SYSTEM ERROR] {e}")
            return False

    def create_index(self):
        print("   [STEP 1/3] Memperbarui Katalog (Indexing)...")
        catalog = []
        try:
            files = [f for f in os.listdir(DB_FOLDER) if f.endswith(".json") and f != "index.json"]
            for filename in files:
                filepath = os.path.join(DB_FOLDER, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    catalog.append({
                        "title": data.get("title", "Unknown"),
                        "slug": data.get("slug", filename.replace(".json", "")),
                        "cover": data.get("cover", ""),
                        "last_updated": data.get("last_updated", "N/A"),
                        "total_chapters": len(data.get("chapters", []))
                    })
            catalog.sort(key=lambda x: x["last_updated"], reverse=True)
            with open(os.path.join(DB_FOLDER, "index.json"), 'w', encoding='utf-8') as f:
                json.dump(catalog, f, indent=2)
            print(f"      -> Berhasil merangkum {len(catalog)} komik.")
            return True
        except Exception as e:
            print(f"      [ERROR INDEXING] {e}")
            return False

    def sync_github(self):
        print("   [STEP 2/3] Memeriksa Perubahan Lokal...")
        status = self.run_git(["status", "--porcelain"])
        
        if status is False: return
        if not status:
            print("      -> Status: Clean. Tidak ada perubahan.")
            return

        print("   [STEP 3/3] Sinkronisasi ke GitHub...")
        self.run_git(["add", "."])
        
        t_stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        if self.run_git(["commit", "-m", f"Monsta Auto-Sync: {t_stamp}"]):
            print(f"      -> Committed.")
        
        print("      -> Pushing to origin main...")
        if self.run_git(["push", "origin", "main"]) is not False:
            print("      -> SINKRONISASI SELESAI: Data aman di GitHub.")
        else:
            print("      -> GAGAL PUSH. Periksa koneksi/kredensial.")

if __name__ == "__main__":
    bot = MonstaManager()
    print("\n" + "="*50)
    print("   MONSTA MANAGER V52.5 - FINAL PATH FIX")
    print("="*50)
    print(f"Status: ONLINE | Interval: {CHECK_INTERVAL}s\n")

    while True:
        try:
            bot.create_index()
            bot.sync_github()
            print(f"\n[REST] Menunggu siklus berikutnya... ({datetime.now().strftime('%H:%M:%S')})")
        except KeyboardInterrupt:
            print("\n[OFFLINE] Sistem dimatikan.")
            break
        except Exception as e:
            print(f"\n[CRASH] {e}")
        time.sleep(CHECK_INTERVAL)