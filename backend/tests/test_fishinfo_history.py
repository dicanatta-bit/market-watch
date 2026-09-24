import unittest
from datetime import date

from app.scrapers.fishinfo_history import parse_archive_page, week_starts


def page(period="20 May 2026 - 26 May 2026", fish="Bandeng"):
    return f'''<div id="tab-tabel"><center>
    Perbandingan Harga Rata-rata Eceran Ikan {fish} Jawa Timur (Semua Pasar)
    ( {period} )</center><table id="tb_harga"><tbody>
    <tr><td>1</td><td>{fish}</td><td>Pasar A</td><td>Rp. 30.000,00</td></tr>
    <tr><td>2</td><td>{fish}</td><td>Pasar B</td><td>Rp. 36.000,00</td></tr>
    </tbody></table></div>'''


class FishInfoHistoryTest(unittest.TestCase):
    def test_weekly_average_and_count(self):
        result = parse_archive_page(page(), "Bandeng", date(2026, 5, 20), date(2026, 5, 26))
        self.assertEqual(result, (33000, 2))

    def test_rejects_wrong_period_or_fish(self):
        with self.assertRaisesRegex(ValueError, "Periode historis salah"):
            parse_archive_page(page(), "Bandeng", date(2026, 5, 27), date(2026, 6, 2))
        with self.assertRaisesRegex(ValueError, "Filter komoditas tidak cocok"):
            parse_archive_page(page(), "Tuna", date(2026, 5, 20), date(2026, 5, 26))

    def test_week_buckets_cover_partial_current_week(self):
        periods = list(week_starts(date(2026, 9, 16), date(2026, 9, 24)))
        self.assertEqual(periods, [(date(2026, 9, 16), date(2026, 9, 22)),
                                   (date(2026, 9, 23), date(2026, 9, 24))])


if __name__ == "__main__":
    unittest.main()
