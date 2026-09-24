import unittest
from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import CommodityPrice
from app.routers.prices_router import get_price_history, get_prices
from app.scrapers.fishinfo_history import SERIES_SIZE, SOURCE_NAME


class PriceHistoryTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        for day, source, price in (
            (date(2026, 9, 9), "FishInfo Jatim (DKP Jawa Timur)", 30000),
            (date(2026, 9, 10), "FishInfo Jatim (DKP Jawa Timur)", 31000),
            (date(2026, 9, 17), "FishInfo Jatim (DKP Jawa Timur)", 32000),
            (date(2026, 9, 20), "Estimasi", 99999),
            (date(2026, 9, 23), "FishInfo Jatim (DKP Jawa Timur)", 33000),
        ):
            self.db.add(CommodityPrice(tanggal=day, komoditas="Bandeng",
                                       size="Rata-rata konsumen", sumber=source,
                                       harga_tambak_low=price, harga_tambak_high=price,
                                       created_at=datetime(2026, 9, 23)))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_uses_fourteen_days_ending_at_latest_verified_sync(self):
        result = get_price_history("Bandeng", "Rata-rata konsumen", 14, self.db)
        self.assertEqual(result["window_start"], "2026-09-10")
        self.assertEqual(result["window_end"], "2026-09-23")
        self.assertEqual([point["date"] for point in result["data"]],
                         ["2026-09-10", "2026-09-17", "2026-09-23"])
        self.assertEqual(result["observation_count"], 3)

    def test_missing_history_is_explicit(self):
        result = get_price_history("Tuna", "Rata-rata konsumen", 14, self.db)
        self.assertEqual(result["data"], [])
        self.assertIsNone(result["window_end"])

    def test_archive_is_preferred_and_full_history_is_returned(self):
        for day, value in ((date(2026, 5, 20), 30000),
                           (date(2026, 7, 1), 32000),
                           (date(2026, 9, 23), 39000)):
            self.db.add(CommodityPrice(
                tanggal=day, komoditas="Bandeng", size=SERIES_SIZE,
                sumber=SOURCE_NAME, harga_tambak_low=value,
                harga_tambak_high=value, created_at=datetime(2026, 9, 23),
                catatan=f"Periode {day}; 18 harga pasar; https://fishinfojatim.net/dashboard/dashharga"))
        self.db.commit()
        latest = get_prices(self.db)
        self.assertEqual(latest["series"], "retail_market_mean")
        self.assertEqual(latest["data"][0]["harga_tambak_low"], 39000)
        self.assertEqual(latest["data"][0]["market_count"], 18)
        history = get_price_history("Bandeng", SERIES_SIZE, None, self.db)
        self.assertEqual(history["observation_count"], 3)
        self.assertEqual(history["window_start"], "2026-05-20")


if __name__ == "__main__":
    unittest.main()
