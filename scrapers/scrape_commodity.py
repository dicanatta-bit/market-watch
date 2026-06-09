"""scrape_commodity.py — Scrape harga komoditas → INSERT commodity_prices + regional_prices"""
import re, time, sys
from datetime import date
from config import Config
from app import create_app
from models import db, CommodityPrice, RegionalPrice

try:
    import requests
    from bs4 import BeautifulSoup
    WEB = True
except ImportError:
    WEB = False

WILAYAH_FAKTOR = {
    "Jawa-Bali": 1.00, "Sumatera": 0.95, "Kalimantan": 0.92,
    "Sulawesi": 0.90, "NTT-NTB": 0.88, "Maluku": 0.85, "Papua": 0.85,
}

BASE_DATA = [
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 50",
     "harga_tambak_low": 60000, "harga_tambak_high": 65000,
     "harga_ekspor_low": 3.55, "harga_ekspor_high": 3.64,
     "harga_intl_low": 3.55, "harga_intl_high": 3.64,
     "sumber": "JALA Tech; KKP DJPB; UCN; ShrimpNews Asia",
     "catatan": "Harga tambak Jawa Tengah."},
    {"komoditas": "Udang Vaname (Litopenaeus vannamei)", "size": "Size 60",
     "harga_tambak_low": 55000, "harga_tambak_high": 60000,
     "harga_ekspor_low": 3.55, "harga_ekspor_high": 3.55,
     "harga_intl_low": 3.55, "harga_intl_high": 3.55,
     "sumber": "JALA Tech; KKP DJPB; FAO GLOBEFISH",
     "catatan": "Global turun 5,6% YoY. Indonesia stabil."},
    {"komoditas": "Udang Windu (Penaeus monodon)", "size": "Size 20",
     "harga_tambak_low": 100000, "harga_tambak_high": 120000,
     "harga_ekspor_low": 8.00, "harga_ekspor_high": 10.00,
     "harga_intl_low": None, "harga_intl_high": None,
     "sumber": "KKP DJPB; JALA Tech; SeafoodSource",
     "catatan": "Produksi terbatas; harga premium."},
    {"komoditas": "Nila (Oreochromis niloticus)", "size": "300-500 g",
     "harga_tambak_low": 22000, "harga_tambak_high": 28000,
     "harga_ekspor_low": 3.00, "harga_ekspor_high": 4.00,
     "harga_intl_low": None, "harga_intl_high": None,
     "sumber": "KKP DJPB; BPS ekspor; FAO GLOBEFISH",
     "catatan": "Ekspor fillet ke AS & Eropa."},
    {"komoditas": "Tuna Sirip Kuning / Yellowfin (Thunnus albacares)", "size": "Sashimi grade",
     "harga_tambak_low": 60000, "harga_tambak_high": 80000,
     "harga_ekspor_low": 5.00, "harga_ekspor_high": 8.00,
     "harga_intl_low": 6.50, "harga_intl_high": 9.00,
     "sumber": "KKP; ASTUIN; PPS Bitung; FAO GLOBEFISH",
     "catatan": "Ekspor utama ke Jepang dan Eropa."},
    {"komoditas": "Tuna Cakalang (Katsuwonus pelamis)", "size": "-",
     "harga_tambak_low": 15000, "harga_tambak_high": 25000,
     "harga_ekspor_low": 1.50, "harga_ekspor_high": 2.50,
     "harga_intl_low": 1.80, "harga_intl_high": 2.20,
     "sumber": "KKP; PPS Bitung; ASTUIN; FAO GLOBEFISH",
     "catatan": "Bahan baku utama pengalengan."},
    {"komoditas": "Rumput Laut (Eucheuma cottonii)", "size": "Kering",
     "harga_tambak_low": 6000, "harga_tambak_high": 7000,
     "harga_ekspor_low": 0.40, "harga_ekspor_high": 0.50,
     "harga_intl_low": 0.35, "harga_intl_high": 0.45,
     "sumber": "KKP DJPB; Asosiasi RL Indonesia; FAO",
     "catatan": "Dominan NTT, Sulawesi, Maluku."},
    {"komoditas": "Lobster (Panulirus ornatus) / Mutiara", "size": ">200 g",
     "harga_tambak_low": 280000, "harga_tambak_high": 380000,
     "harga_ekspor_low": 18.00, "harga_ekspor_high": 22.00,
     "harga_intl_low": None, "harga_intl_high": None,
     "sumber": "KKP; Pelabuhan Perikanan; Undercurrent News",
     "catatan": "Sensitif terhadap kuota ekspor KKP."},
    {"komoditas": "Bandeng (Chanos chanos)", "size": "250-500 g",
     "harga_tambak_low": 20000, "harga_tambak_high": 28000,
     "harga_ekspor_low": 1.80, "harga_ekspor_high": 2.50,
     "harga_intl_low": None, "harga_intl_high": None,
     "sumber": "KKP DJPB; Trobos Aqua; BPS",
     "catatan": "Premium menjelang Lebaran."},
    {"komoditas": "Cumi-cumi (Loligo spp.)", "size": "-",
     "harga_tambak_low": 35000, "harga_tambak_high": 50000,
     "harga_ekspor_low": 3.50, "harga_ekspor_high": 5.00,
     "harga_intl_low": 3.00, "harga_intl_high": 4.50,
     "sumber": "KKP; Pelabuhan Perikanan; FAO GLOBEFISH",
     "catatan": "Fluktuatif mengikuti musim tangkapan."},
]


def generate_regional_prices(today):
    """Generate regional price data from base prices × faktor wilayah."""
    for entry in BASE_DATA:
        for wilayah, faktor in WILAYAH_FAKTOR.items():
            existing = RegionalPrice.query.filter_by(
                tanggal=today, wilayah=wilayah,
                komoditas=entry["komoditas"], size=entry["size"],
            ).first()
            if existing:
                continue
            rp = RegionalPrice(
                tanggal=today,
                wilayah=wilayah,
                komoditas=entry["komoditas"],
                size=entry["size"],
                harga_tambak_low=round(entry["harga_tambak_low"] * faktor),
                harga_tambak_high=round(entry["harga_tambak_high"] * faktor),
                faktor_wilayah=faktor,
            )
            db.session.add(rp)


def main():
    app = create_app(Config)
    with app.app_context():
        today = date.today()
        print("=" * 55)
        print(f"Commodity Scraper — {today}")
        print("=" * 55)

        added = 0
        skipped = 0

        for entry in BASE_DATA:
            existing = CommodityPrice.query.filter_by(
                tanggal=today, komoditas=entry["komoditas"], size=entry["size"],
            ).first()
            if existing:
                skipped += 1
                continue

            cp = CommodityPrice(
                tanggal=today,
                komoditas=entry["komoditas"],
                size=entry["size"],
                harga_tambak_low=entry["harga_tambak_low"],
                harga_tambak_high=entry["harga_tambak_high"],
                harga_ekspor_low=entry["harga_ekspor_low"],
                harga_ekspor_high=entry["harga_ekspor_high"],
                harga_intl_low=entry["harga_intl_low"],
                harga_intl_high=entry["harga_intl_high"],
                sumber=entry["sumber"],
                catatan=entry["catatan"],
                tingkat_kepercayaan="Estimasi",
            )
            db.session.add(cp)
            added += 1

        # Generate regional prices
        generate_regional_prices(today)

        db.session.commit()
        print(f"\nCommodity prices: {added} added, {skipped} skipped")
        print(f"Regional prices generated for {len(WILAYAH_FAKTOR)} wilayah")
        print("=" * 55)


if __name__ == "__main__":
    main()
