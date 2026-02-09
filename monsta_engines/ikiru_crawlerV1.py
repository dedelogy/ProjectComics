import os
import json
import time
import re
import random
from datetime import datetime
from playwright.sync_api import sync_playwright

# =======================================================
# MONSTA BOT 1: IKIRU PERFECT CRAWLER (V25.0)
# Target: https://02.ikiru.wtf/project/?the_page=X
# Perbaikan:
# 1. Filter Ketat: Wajib buang link yang mengandung "chapter-"
# 2. Pagination Fix: Menggunakan parameter ?the_page=
# 3. Dedup Logic: Memastikan 121 Judul unik, tidak kurang tidak lebih.
# =======================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, "..", "target_list.json")
DEBUG_DIR = os.path.join(BASE_DIR, "..", "monstacomics", "debug_crawler")

os.makedirs(DEBUG_DIR, exist_ok=True)

def save_data(data):
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def run_crawler_perfect():
    print("=== MONSTA FACTORY: BOT 1 (PERFECT EDITION V25.0) ===")
    
    # Reset File Target
    if not os.path.exists(TARGET_FILE):
        save_data([])

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        target_data = []
        base_url = "https://02.ikiru.wtf/project/"
        
        # Loop Halaman 1 sampai 10 (Estimasi aman, akan break jika kosong)
        for current_page in range(1, 11):
            # Pola URL sesuai temuan Partner: ?the_page=X
            url = f"{base_url}?the_page={current_page}" if current_page > 1 else base_url
            print(f"[*] Scanning Page {current_page}: {url}")

            try:
                page.goto(url, timeout=60000, wait_until="networkidle")
                
                # Scroll Trigger (Penting untuk Ikiru)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                # AMBIL SEMUA LINK MANGA
                # Strategi: Ambil semua, lalu filter di Python (Lebih aman)
                candidate_links = page.query_selector_all("a[href*='/manga/']")
                
                valid_count_on_page = 0
                seen_slugs_on_page = set()

                if not candidate_links:
                    print(f"    [!] Halaman {current_page} Kosong/Habis. Stop Crawling.")
                    break

                for link in candidate_links:
                    try:
                        href = link.get_attribute("href")
                        if not href: continue
                        
                        # --- FILTER SAMPAH (THE FLAW FIX) ---
                        # 1. Buang jika mengandung 'chapter-' (Ini link chapter, bukan komik)
                        if "chapter-" in href: continue
                        # 2. Buang jika mengandung 'comment' atau '#'
                        if "comment" in href or "#" in href: continue
                        
                        # Bersihkan URL
                        if href.endswith("/"): href = href[:-1]
                        slug = href.split("/")[-1]
                        
                        # Cek Duplikasi Global (agar id tidak loncat)
                        if any(item['slug'] == slug for item in target_data):
                            continue
                        
                        if slug in seen_slugs_on_page: continue

                        # Ambil Judul
                        title = ""
                        # Prioritas elemen judul
                        title_el = link.query_selector("span.font-bold") or \
                                   link.query_selector("div.font-bold") or \
                                   link.query_selector(".line-clamp-1") or \
                                   link.query_selector(".line-clamp-2")
                        
                        if title_el:
                            title = title_el.inner_text().strip()
                        else:
                            # Fallback Text
                            raw = link.inner_text().strip()
                            if len(raw) > 3 and "\n" not in raw: title = raw
                            else: continue

                        # Ambil Last Chapter (Optional)
                        last_chap = "N/A"
                        chap_el = link.query_selector("span.text-xs")
                        if chap_el: last_chap = chap_el.inner_text().strip()

                        # DATA BERSIH
                        item = {
                            "id": len(target_data) + 1,
                            "title": title,
                            "slug": slug,
                            "source_url": f"{href}/",
                            "last_chapter_str": last_chap,
                            "status": "pending",
                            "last_scanned": datetime.now().isoformat()
                        }
                        
                        target_data.append(item)
                        seen_slugs_on_page.add(slug)
                        valid_count_on_page += 1
                        print(f"    + {title}")

                    except Exception:
                        continue

                # Cek Hasil Halaman Ini
                if valid_count_on_page == 0:
                    print(f"    [STOP] Halaman {current_page} terbuka tapi tidak ada judul baru. Selesai.")
                    break
                
                # Simpan Progress
                save_data(target_data)
                print(f"    [SAVED] {valid_count_on_page} judul baru. Total: {len(target_data)}")
                
                # Jeda Manusiawi
                time.sleep(random.uniform(2, 3))

            except Exception as e:
                print(f"    [FATAL] Error Page {current_page}: {e}")
                break

        browser.close()
        print(f"\n=== MISSION COMPLETE: {len(target_data)} KOMIK (TARGET: 121) ===")

if __name__ == "__main__":
    run_crawler_perfect()