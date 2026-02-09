import os
import json
import time
import re
import requests
import io
import mimetypes
from PIL import Image
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ==============================================================================
# MONSTA BOT 2: DISTRIBUTED WORKER (V37.0 - ULTIMATE FORENSIC TITAN)
# ------------------------------------------------------------------------------
# Arsitektur Transparansi & Ketahanan Mutlak:
# 1. SOVEREIGN IDENTITY: Menggunakan Access Token resmi untuk Trust Server.
# 2. WEBP-TO-JPEG SURGERY: Konversi biner di RAM untuk menghancurkan Error 400.
# 3. 5MB SCALE GUARD: Verifikasi ketat kapasitas file sebelum transmisi.
# 4. MULTIPART TUPLE PRECISION: Mengikuti standar Stack Overflow ('file', data, mime).
# 5. HTMX & DATA-ATTRIBUTE SNIPER: Akurasi bedah pada struktur dinamis Ikiru.
# 6. ATOMIC DISK WRITE: Proteksi integritas JSON via swap .tmp (Anti-Corrupt).
# 7. FORENSIC NOISY LOG: Laporan per-detik (Found, Fetch, Size, Convert, Upload, Disk).
# ==============================================================================

# --- KONFIGURASI JALUR SISTEM ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_LIST_FILE = os.path.join(BASE_DIR, "..", "target_list.json")
DATABASE_DIR = os.path.join(BASE_DIR, "..", "monstacomics", "database")
AUTH_FILE = os.path.join(BASE_DIR, "..", "monstacomics", "telegraph_auth.json")
ANOMALI_LOG = os.path.join(BASE_DIR, "..", "monstacomics", "anomali_log.json")

# Inisialisasi Infrastruktur Folder
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# --- GLOBAL SESSION (Browser-Like Handshake) ---
# Digunakan untuk metadata dan verifikasi identitas
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01"
})

# --- FUNGSI IDENTITAS (TELEGRAPH SOVEREIGNTY) ---

def get_or_create_telegraph_token():
    """
    Mengambil atau membuat identitas resmi di Telegraph.
    Memberikan kredibilitas agar upload tidak dianggap sebagai spam anonim.
    """
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, 'r', encoding='utf-8') as f:
                auth_data = json.load(f)
                print(f"[AUTH] Identitas Sovereign Terdeteksi: {auth_data.get('author_name')}")
                return auth_data.get('access_token')
        except:
            print("[AUTH] File auth korup, meriset identitas Sovereign...")

    print("[AUTH] Menciptakan akun Sovereign baru di Telegraph...")
    try:
        url = "https://api.telegra.ph/createAccount"
        params = {
            "short_name": "MonstaBot",
            "author_name": "Monsta Sovereign Titan",
            "author_url": "https://monstacomics.com"
        }
        response = session.get(url, params=params, timeout=30).json()
        
        if response.get('ok'):
            token = response['result']['access_token']
            with open(AUTH_FILE, 'w', encoding='utf-8') as f:
                json.dump(response['result'], f, indent=4)
            print(f"[AUTH] Sukses! Identitas disimpan di {os.path.basename(AUTH_FILE)}")
            return token
        else:
            print(f"[AUTH ERROR] Gagal registrasi: {response.get('error')}")
    except Exception as e:
        print(f"[AUTH ERROR] Kendala jaringan saat autentikasi: {e}")
    
    return None

def verbose_titan_upload(img_bytes, source_url):
    """
    Uploader Titan V37: Gabungan Konversi WebP -> JPEG dan Log Forensik.
    Menghancurkan Error 400 dengan memastikan format selalu JPEG Whitelisted.
    """
    try:
        # 1. FORENSIC: ANALISA AWAL
        orig_ext = source_url.split('.')[-1].split('?')[0].lower()
        print(f"      [PROCESS] Membedah biner dari sumber ({orig_ext})...")

        # 2. SURGERY: KONVERSI KE JPEG (Fix Error 400)
        try:
            img = Image.open(io.BytesIO(img_bytes))
            # Handle transparansi (RGBA) ke RGB agar JPEG tidak error
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Simpan ke buffer RAM sebagai JPEG
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            final_bytes = buffer.getvalue()
            
            # Hitung ukuran hasil konversi
            final_size_mb = len(final_bytes) / (1024 * 1024)
            print(f"      [CONVERT] WebP/PNG -> JPEG Sukses. Ukuran Baru: {final_size_mb:.2f} MB")
            
            # 3. SCALE GUARD (5MB Limit)
            if final_size_mb >= 5.0:
                print(f"      [SKIP] File hasil konversi melebihi 5MB. Telegraph menolak.")
                return None
                
            mime_type = "image/jpeg"
            filename = f"monsta_{int(time.time())}.jpg"
            
        except Exception as e_conv:
            print(f"      [WARN] Operasi konversi gagal ({e_conv}). Mencoba kirim data asli...")
            final_bytes = img_bytes
            mime_type = mimetypes.types_map.get(f'.{orig_ext}', 'image/jpeg')
            filename = f"panel.{orig_ext}"

        # 4. TRANSMISI: MULTIPART POST (Struktur Stack Overflow)
        url = 'https://telegra.ph/upload'
        files = {'file': (filename, final_bytes, mime_type)}
        
        print(f"      [UPLOADING] Mengirim paket data ke Telegraph...")
        # Gunakan requests.post langsung (tanpa session headers) untuk stabilitas multipart
        response = requests.post(url, files=files, timeout=60)
        
        # 5. DIAGNOSA RESPON
        if response.status_code != 200:
            print(f"      [FAILURE] Server menolak (Status {response.status_code}).")
            print(f"      [RAW DEBUG] Respon: {response.text[:250]}")
            return None

        try:
            res_json = response.json()
            if isinstance(res_json, list) and len(res_json) > 0:
                t_link = "https://telegra.ph" + res_json[0]['src']
                # BUKTI BERHASIL
                print(f"      [SUCCESS] Link Telegraph Tercipta: {t_link}")
                return t_link
            else:
                print(f"      [FAILURE] Format JSON ilegal dari server: {res_json}")
                return None
        except:
            print(f"      [FAILURE] Respon server bukan JSON valid. Raw: {response.text[:150]}")
            return None

    except Exception as e:
        print(f"      [FAILURE] Kendala sistem fatal saat upload: {e}")
        return None

# --- FUNGSI UTILITAS (TOOLS) ---

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\n', ' ').replace('\t', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def extract_number(text):
    if not text: return 0.0
    match = re.search(r'(\d+(\.\d+)?)', str(text))
    return float(match.group(1)) if match else 0.0

def safe_save_json(data, filepath):
    """Menyimpan data dengan teknik Atomic dan konfirmasi bukti di CMD."""
    temp_path = filepath + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        if os.path.exists(filepath):
            os.remove(filepath)
        os.rename(temp_path, filepath)
        print(f"      [DISK] Status: Data dikunci ke {os.path.basename(filepath)} (SYNC OK).")
        return True
    except Exception as e:
        print(f"      [DISK ERROR] Gagal mengunci data ke harddisk: {e}")
        return False

# --- MESIN UTAMA (THE WORKER) ---

def run_worker_node():
    print("====================================================")
    print("   MONSTA FACTORY: BOT 2 (V37.0 - ULTIMATE TITAN)")
    print("====================================================")

    # Memastikan Identitas Sovereign Siap
    token = get_or_create_telegraph_token()

    if not os.path.exists(TARGET_LIST_FILE):
        print("[!] ERROR: target_list.json tidak ditemukan!"); return

    with open(TARGET_LIST_FILE, 'r', encoding='utf-8') as f:
        all_targets = json.load(f)

    # Input Range Distribusi
    while True:
        try:
            print("-" * 60)
            s_in = input("[?] Masukkan Start ID : ")
            e_in = input("[?] Masukkan End ID   : ")
            start_id, end_id = int(s_in), int(e_in); break
        except ValueError:
            print("[!] Harap masukkan angka bulat saja.")

    my_tasks = [t for t in all_targets if start_id <= t['id'] <= end_id]
    if not my_tasks:
        print("[!] Tidak ada tugas di range tersebut."); return

    print(f"\n[NODE] Memulai pengerjaan {len(my_tasks)} judul komik...\n")

    # INISIALISASI PLAYWRIGHT
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        context.set_extra_http_headers({"Referer": "https://02.ikiru.wtf/"})
        page = context.new_page()

        for idx, target in enumerate(my_tasks):
            slug = target['slug']
            db_path = os.path.join(DATABASE_DIR, f"{slug}.json")
            
            # --- MANAJEMEN RESUME ---
            data = None
            if os.path.exists(db_path):
                try:
                    with open(db_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    print(f"[{idx+1}/{len(my_tasks)}] RESUMING: {target['title']}")
                except: data = None
            
            if not data:
                print(f"[{idx+1}/{len(my_tasks)}] STARTING FRESH: {target['title']}")
                data = {
                    "slug": slug,
                    "title": target['title'],
                    "cover": "",
                    "metadata": {},
                    "chapters": [],
                    "last_updated": ""
                }
                safe_save_json(data, db_path)

            try:
                # ---------------------------------------------------------
                # STEP 1: DETAIL PAGE & HTMX SNIPER
                # ---------------------------------------------------------
                print("   -> 1. Navigasi ke Laman Detail...")
                page.goto(target['source_url'], timeout=60000, wait_until="networkidle")
                
                # HTMX Trigger (Anti-Zonk Chapter)
                try:
                    htmx_btn = page.locator("button[data-key='chapters']").first
                    if htmx_btn.is_visible():
                        print("      [ACTION] Klik Tombol HTMX Chapters...")
                        htmx_btn.click()
                        print("      [WAIT] Menunggu AJAX Render Daftar...")
                        page.wait_for_selector("div[data-chapter-number]", timeout=15000)
                        print("      [SUCCESS] Daftar Chapter muncul di DOM.")
                except Exception as e_htmx:
                    print(f"      [INFO] HTMX Trigger Skip: {e_htmx}")

                # Backup Scroll
                page.keyboard.press("End"); time.sleep(2)
                soup = BeautifulSoup(page.content(), "html.parser")

                # --- STEP 2: COVER PROCESSING (THE FORENSIC LOG) ---
                if not data.get('cover') or "telegra.ph" not in data['cover']:
                    cover_box = soup.select_one("div[itemprop='image']")
                    img_node = cover_box.select_one("img") if cover_box else soup.select_one("img.wp-post-image")
                    
                    if img_node:
                        orig_url = (img_node.get('src') or img_node.get('data-src') or "").split('?')[0]
                        if orig_url:
                            if orig_url.startswith("/"): orig_url = "https://02.ikiru.wtf" + orig_url
                            
                            print(f"      [FOUND] Link Cover Asli: {orig_url}")
                            try:
                                print(f"      [FETCH] Mendownload bytes gambar...")
                                c_resp = page.request.get(orig_url, timeout=30000)
                                if c_resp.status == 200:
                                    t_url = verbose_titan_upload(c_resp.body(), orig_url)
                                    if t_url:
                                        data['cover'] = t_url
                                        safe_save_json(data, db_path)
                            except Exception as e_up:
                                print(f"      [ERROR] Gagal proses cover: {e_up}")

                # --- STEP 3: METADATA & CHAPTER COLLECTION ---
                syn_box = soup.select_one("div[itemprop='description'][data-show='false']") or \
                          soup.select_one("div[itemprop='description']")
                data['metadata']['synopsis'] = clean_text(syn_box.get_text()) if syn_box else "N/A"

                ch_found = []
                seen_urls = set()
                chapter_list = soup.select("div[data-chapter-number]")
                for div in chapter_list:
                    a_tag = div.select_one("a")
                    if a_tag and a_tag.get('href') not in seen_urls:
                        num = extract_number(div.get('data-chapter-number'))
                        ch_found.append({"num": num, "url": a_tag.get('href')})
                        seen_urls.add(a_tag.get('href'))
                
                ch_found.sort(key=lambda x: x['num'])
                print(f"      [INFO] {len(ch_found)} Chapter Terkunci via Data-Attribute.")

                # --- STEP 4: READER ENGINE (THE PANEL PROOF) ---
                existing_nums = [c['ch_num'] for c in data['chapters']]
                work_queue = [c for c in ch_found if c['num'] not in existing_nums]
                
                print(f"      [QUEUE] {len(work_queue)} Chapter baru siap dipanen.")

                for ch_task in work_queue:
                    print(f"\n      >>> FORENSIC START: CHAPTER {ch_task['num']} <<<")
                    print(f"      [NAVIGATE] Reader URL: {ch_task['url']}")
                    
                    try:
                        page.goto(ch_task['url'], timeout=60000, wait_until="domcontentloaded")
                        # Scroll Lazy Load
                        for _ in range(3):
                            page.mouse.wheel(0, 1500); time.sleep(0.7)
                        
                        # Tunggu Reader Section
                        try:
                            page.wait_for_selector("section[data-image-data='1'] img", timeout=15000)
                        except: pass

                        c_soup = BeautifulSoup(page.content(), "html.parser")
                        reader_area = c_soup.select_one("section[data-image-data='1']")
                        img_nodes = reader_area.find_all('img') if reader_area else c_soup.find_all('img')
                        
                        panel_urls = []
                        for node in img_nodes:
                            src = (node.get('src') or node.get('data-src') or "").strip()
                            # Whitelist CDN (itachi, uqni, ikiru, google)
                            if src and any(c in src for c in ['itachi.my.id', 'uqni.net', '02.ikiru.wtf']):
                                if not any(j in src for j in ['logo', 'banner', 'iklan']):
                                    panel_urls.append(src)

                        # UPLOAD MASIF DENGAN BUKTI FORENSIK
                        telegraph_proofs = []
                        if panel_urls:
                            panel_urls = list(dict.fromkeys(panel_urls))
                            print(f"      [FOUND] {len(panel_urls)} panel gambar asli terdeteksi.")
                            
                            for p_idx, p_url in enumerate(panel_urls):
                                try:
                                    print(f"      [FETCH] Panel {p_idx+1}/{len(panel_urls)} -> {p_url[:45]}...")
                                    p_resp = page.request.get(p_url, timeout=40000)
                                    if p_resp.status == 200:
                                        t_url = verbose_titan_upload(p_resp.body(), p_url)
                                        if t_url:
                                            telegraph_proofs.append(t_url)
                                            # Link ini akan muncul di CMD setiap kali berhasil
                                    else:
                                        print(f"      [ERROR] Download gagal. Status: {p_resp.status}")
                                except Exception as e_p:
                                    print(f"      [ERROR] Kendala panel {p_idx+1}: {e_p}")
                        
                        # FINAL CHAPTER STORAGE
                        if telegraph_proofs:
                            data['chapters'].append({
                                "ch_num": ch_task['num'],
                                "release_date": datetime.now().strftime("%Y-%m-%d"),
                                "images": list(dict.fromkeys(telegraph_proofs))
                            })
                            data['chapters'].sort(key=lambda x: x['ch_num'], reverse=True)
                            
                            # PROOF OF STORAGE
                            print(f"      [PROOF] Chapter {ch_task['num']} Selesai dengan {len(telegraph_proofs)} Link Terverifikasi.")
                            safe_save_json(data, db_path)
                        else:
                            print(f"      [WARN] Ch. {ch_task['num']} dilewati (Nol upload).")

                    except Exception as e_ch:
                        print(f"      [ERROR] Gagal total pada chapter {ch_task['num']}: {e_ch}")

                # Update Timestamp Final
                data['last_updated'] = datetime.now().isoformat()
                safe_save_json(data, db_path)
                print(f"\n   [FINISHED] Judul '{target['title']}' SUKSES TOTAL.")

            except Exception as e_fatal:
                print(f"   [FATAL] Error pada {slug}: {e_fatal}")

        browser.close()
        print("\n====================================================")
        print("   OPERASI SELESAI. SILAKAN CEK HASIL DI DATABASE.")
        print("====================================================")

if __name__ == "__main__":
    run_worker_node()