import os

# Cek posisi script ini berada
current_dir = os.path.dirname(os.path.abspath(__file__))
print(f"1. Script ada di: {current_dir}")

# Cek di mana dia mencari database
target_db = os.path.abspath(os.path.join(current_dir, "..", "monstacomics", "database"))
print(f"2. Target Database: {target_db}")

# Cek apakah folder itu ada?
if os.path.exists(target_db):
    print("   -> STATUS: Folder DITEMUKAN! ✅")
    
    # Cek isi folder itu
    files = os.listdir(target_db)
    print(f"3. Isi Folder Database ({len(files)} file):")
    if "index.json" in files:
        print("   -> WOW! Ada file 'index.json' di sini! 🎉")
    else:
        print("   -> WADUH! Tidak ada 'index.json' di sini. ❌")
        print("   -> Daftar file yang ada:")
        print(files[:5]) # Tampilkan 5 file pertama aja
else:
    print("   -> STATUS: Folder TIDAK ADA! ❌ (Salah Alamat)")
    print("   -> Coba cek lagi nama foldermu. Apakah 'monstacomics' atau 'MonstaComics'?")

input("\nTekan Enter untuk keluar...")