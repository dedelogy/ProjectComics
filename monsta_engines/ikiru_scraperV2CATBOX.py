import os
import json
import time
import re
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ==============================================================================
# MONSTA BOT 2: DISTRIBUTED WORKER (V40.0 - CATBOX MIGRATION ULTIMATE)
# ------------------------------------------------------------------------------
# Arsitektur Transparansi & Kestabilan Baru:
# 1. CATBOX ENGINE: Hosting file permanen, tanpa limit 5MB, tanpa konversi WebP.
# 2. NO AUTH TOKEN: Upload anonim (userhash kosong) tetap menghasilkan link abadi.
# 3. HTMX & DATA-ATTRIBUTE SNIPER: Akurasi bedah pada struktur dinamis Ikiru.
# 4. ATOMIC DISK WRITE: Proteksi integritas JSON via swap .tmp (Anti-Corrupt).
# 5. FORENSIC NOISY LOG: Laporan "berisik" (Found -> Fetch -> Upload -> Success).
# ==============================================================================

# --- KONFIGURASI JALUR SISTEM ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_LIST_FILE = os.path.join(BASE_DIR, "..", "target_list.json")
DATABASE_DIR = os.path.join(BASE_DIR, "..", "monstacomics", "database")
ANOMALI_LOG = os.path.join(BASE_DIR, "..", "monstacomics", "anomali_log.json")

# Inisialisasi Infrastruktur Folder (Wajib Ada)
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)

# --- MESIN UPLOAD: CATBOX.MOE (THE NEW HEART) ---

def upload_to_catbox(img_bytes, filename="image.webp"):
    """
    Fungsi Pengunggah Utama ke Catbox.moe.
    Menggantikan Telegraph dengan logika yang jauh lebih sederhana dan kuat.
    """
    try:
        url = "https://catbox.moe/user/api.php"
        
        # Payload Standar Catbox (Anonim)
        payload = {
            'reqtype': 'fileupload',
            'userhash': '' # Biarkan kosong untuk upload anonim
        }
        
        # Kirim File Mentah (Tanpa Konversi Pillow)
        files = {
            'fileToUpload': (filename, img_bytes)
        }
        
        # LOG FORENSIK: Lapor sebelum kirim
        print(f"      [UPLOAD] Mengirim {len(img_bytes)} bytes ke Catbox...")
        
        # Eksekusi POST (Timeout 60 detik untuk file besar)
        response = requests.post(url, data=payload, files=files, timeout=60)
        
        if response.status_code == 200:
            # Catbox mengembalikan URL mentah (text/plain) di body
            result_url = response.text.strip()
            
            # Validasi URL
            if result_url.startswith("http"):
                print(f"      [SUCCESS] Link Catbox Tercipta: {result_url}")
                return result_url
            else:
                print(f"      [FAILURE] Respon Catbox Aneh: {result_url}")
                return None
        else:
            print(f"      [FAILURE] Server Error (Status {response.status_code})")
            return None

    except Exception as e:
        print(f"      [ERROR] Kendala Koneksi Catbox: {e}")
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
        # LOG FORENSIK: Lapor penulisan disk
        print(f"      [DISK] Status: Data dikunci ke {os.path.basename(filepath)} (SYNC OK).")
        return True
    except Exception as e:
        print(f"      [DISK ERROR] Gagal mengunci data ke harddisk: {e}")
        return False

# --- MESIN UTAMA (THE WORKER) ---

def run_worker_node():
    print("====================================================")
    print("   MONSTA FACTORY: BOT 2 (V40.0 - CATBOX MIGRATION)")
    print("====================================================")

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

    print(f"\n[NODE] Memulai pengerjaan {len(my_tasks)} judul komik dengan CATBOX ENGINE...\n")

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

                # --- STEP 2: COVER PROCESSING (CATBOX MODE) ---
                if not data.get('cover') or "catbox.moe" not in data['cover']:
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
                                    # Ambil ekstensi asli (WebP/JPG/PNG)
                                    ext = orig_url.split('.')[-1]
                                    t_url = upload_to_catbox(c_resp.body(), f"cover.{ext}")
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

                        # UPLOAD MASIF KE CATBOX
                        catbox_proofs = []
                        if panel_urls:
                            panel_urls = list(dict.fromkeys(panel_urls))
                            print(f"      [FOUND] {len(panel_urls)} panel gambar asli terdeteksi.")
                            
                            for p_idx, p_url in enumerate(panel_urls):
                                try:
                                    print(f"      [FETCH] Panel {p_idx+1}/{len(panel_urls)} -> {p_url[:45]}...")
                                    p_resp = page.request.get(p_url, timeout=40000)
                                    if p_resp.status == 200:
                                        # Ambil ekstensi asli tanpa konversi
                                        ext = p_url.split('.')[-1].split('?')[0]
                                        t_url = upload_to_catbox(p_resp.body(), f"panel_{p_idx}.{ext}")
                                        if t_url:
                                            catbox_proofs.append(t_url)
                                            # Link Catbox akan muncul di CMD setiap kali berhasil
                                    else:
                                        print(f"      [ERROR] Download gagal. Status: {p_resp.status}")
                                except Exception as e_p:
                                    print(f"      [ERROR] Kendala panel {p_idx+1}: {e_p}")
                        
                        # FINAL CHAPTER STORAGE
                        if catbox_proofs:
                            data['chapters'].append({
                                "ch_num": ch_task['num'],
                                "release_date": datetime.now().strftime("%Y-%m-%d"),
                                "images": list(dict.fromkeys(catbox_proofs))
                            })
                            data['chapters'].sort(key=lambda x: x['ch_num'], reverse=True)
                            
                            # PROOF OF STORAGE
                            print(f"      [PROOF] Chapter {ch_task['num']} Selesai dengan {len(catbox_proofs)} Link Catbox.")
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