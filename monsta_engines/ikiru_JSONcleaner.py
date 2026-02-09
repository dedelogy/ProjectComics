import json
import os

# PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_FILE = os.path.join(BASE_DIR, "..", "target_list.json")

def clean_targets():
    print("=== BEN'S DATA CLEANER ===")
    
    if not os.path.exists(TARGET_FILE):
        print("[!] File target_list.json tidak ditemukan.")
        return

    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    print(f"Total Data Awal: {len(raw_data)}")
    
    clean_data = []
    seen_slugs = set()
    
    for item in raw_data:
        url = item['source_url']
        slug = item['slug']
        
        # FILTER 1: Buang jika URL mengandung 'chapter-' (Ini link chapter, bukan komik)
        if "chapter-" in url or "chapter-" in slug:
            continue
            
        # FILTER 2: Buang duplikat slug
        if slug in seen_slugs:
            continue
            
        # Re-Index ID biar rapi
        item['id'] = len(clean_data) + 1
        
        clean_data.append(item)
        seen_slugs.add(slug)

    # Simpan Ulang
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, indent=4, ensure_ascii=False)

    print(f"Total Data Bersih: {len(clean_data)}")
    print(f"Sampah Dibuang: {len(raw_data) - len(clean_data)}")
    print("=== DATABASE STERILIZED ===")

if __name__ == "__main__":
    clean_targets()