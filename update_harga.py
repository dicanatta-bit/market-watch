"""
Market Watch - AJN
Update harga komoditas perikanan ke Google Sheet "Harga Komoditas"
"""

import sys
from datetime import date
from google.oauth2.service_account import Credentials
import gspread

SERVICE_ACCOUNT_EMAIL = "knmp-ajn-service@knmp-ajn.iam.gserviceaccount.com"
SHEET_NAME = "Harga Komoditas"
CREDENTIALS_FILE = "credentials.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
HEADERS = [
    "Tanggal", "Komoditas", "Size", "Harga Tambak (Rp/kg)",
    "Harga Ekspor (USD/kg)", "Harga Internasional (USD/kg)", "Sumber", "Catatan"
]

# ---------------------------------------------------------------------------
# Data harga udang vaname — diperbarui 13 Mei 2026
# Sumber: JALA Tech, UCN Global Shrimp Index, SeafoodSource, FRED
# ---------------------------------------------------------------------------
TANGGAL = date.today().strftime("%d/%m/%Y")
DATA_UDANG_VANAME = [
    # [Tanggal, Komoditas, Size, Harga Tambak, Harga Ekspor, Harga Internasional, Sumber, Catatan]
    [
        TANGGAL,
        "Udang Vaname (Litopenaeus vannamei)",
        "Size 50",
        "60.000 - 65.000",
        "",
        "3,55 - 3,64",
        "JALA Tech; UCN Global Shrimp Index; SeafoodSource",
        "Harga tambak Jawa Tengah. Naik 1-3% vs bulan lalu."
    ],
    [
        TANGGAL,
        "Udang Vaname (Litopenaeus vannamei)",
        "Size 60",
        "55.000 - 60.000",
        "",
        "3,55",
        "JALA Tech; UCN Global Shrimp Index",
        "Harga global turun 5,6% YoY (minggu 2-8 Mar 2026). Indonesia relatif stabil."
    ],
    [
        TANGGAL,
        "Udang Vaname (Litopenaeus vannamei)",
        "Size 70",
        "50.000 - 55.000",
        "",
        "",
        "JALA Tech",
        "Produksi diperkirakan meningkat Apr-Mei, berpotensi menekan harga."
    ],
    [
        TANGGAL,
        "Udang Vaname (Litopenaeus vannamei)",
        "Size 100",
        "40.000 - 45.000",
        "",
        "",
        "JALA Tech",
        "Estimasi berdasarkan gradasi harga antar ukuran."
    ],
]


def get_or_create_sheet(spreadsheet: gspread.Spreadsheet, name: str) -> gspread.Worksheet:
    """Ambil sheet jika ada, buat baru jika belum ada."""
    try:
        sheet = spreadsheet.worksheet(name)
        print(f"Sheet '{name}' ditemukan.")
        return sheet
    except gspread.exceptions.WorksheetNotFound:
        print(f"Sheet '{name}' belum ada, membuat sheet baru...")
        sheet = spreadsheet.add_worksheet(title=name, rows=1000, cols=len(HEADERS))
        sheet.append_row(HEADERS, value_input_option="USER_ENTERED")
        # Format header: bold
        sheet.format("A1:H1", {"textFormat": {"bold": True}})
        print(f"Sheet '{name}' berhasil dibuat dengan header.")
        return sheet


def cek_duplikat(sheet: gspread.Worksheet, tanggal: str, komoditas: str, size: str) -> bool:
    """Cek apakah baris dengan tanggal+komoditas+size sudah ada."""
    records = sheet.get_all_values()
    for row in records[1:]:  # skip header
        if len(row) >= 3 and row[0] == tanggal and row[1] == komoditas and row[2] == size:
            return True
    return False


def main():
    print("=== Market Watch AJN -- Update Harga Udang Vaname ===\n")

    # Spreadsheet ID dari argumen atau input manual
    if len(sys.argv) > 1:
        spreadsheet_id = sys.argv[1]
    else:
        print("Cara penggunaan:")
        print("  1. Buat Google Spreadsheet baru di https://sheets.new")
        print(f"  2. Share ke: {SERVICE_ACCOUNT_EMAIL} (role: Editor)")
        print("  3. Salin ID dari URL spreadsheet")
        print("     Contoh URL: https://docs.google.com/spreadsheets/d/[ID_DI_SINI]/edit")
        print()
        spreadsheet_id = input("Masukkan Spreadsheet ID: ").strip()
        if not spreadsheet_id:
            print("ID tidak boleh kosong.")
            sys.exit(1)

    # Autentikasi
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    print("Autentikasi Google Sheets berhasil.")

    # Buka spreadsheet berdasarkan ID
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except gspread.exceptions.APIError as e:
        print(f"\n[ERROR] Tidak bisa membuka spreadsheet: {e}")
        print(f"Pastikan spreadsheet sudah di-share ke: {SERVICE_ACCOUNT_EMAIL}")
        sys.exit(1)
    print(f"Spreadsheet '{spreadsheet.title}' dibuka.")
    print()

    # Ambil atau buat sheet
    sheet = get_or_create_sheet(spreadsheet, SHEET_NAME)

    # Masukkan data
    baris_ditambah = 0
    baris_dilewati = 0
    for baris in DATA_UDANG_VANAME:
        tanggal, komoditas, size = baris[0], baris[1], baris[2]
        if cek_duplikat(sheet, tanggal, komoditas, size):
            print(f"  [LEWATI] {komoditas} {size} tanggal {tanggal} sudah ada.")
            baris_dilewati += 1
        else:
            sheet.append_row(baris, value_input_option="USER_ENTERED")
            print(f"  [OK] {komoditas} {size} -- ditambahkan.")
            baris_ditambah += 1

    print(f"\nSelesai: {baris_ditambah} baris ditambahkan, {baris_dilewati} baris dilewati (duplikat).")
    print(f"Lihat hasilnya: https://docs.google.com/spreadsheets/d/{spreadsheet_id}")


if __name__ == "__main__":
    main()
