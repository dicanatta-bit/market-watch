import unittest
from datetime import date

from app.scrapers.commodity import parse_page


def page(period="23-30 Sep 2026", count=6):
    rows = [
        ("Udang Vaname", "Rp 79.948"), ("Cumi-cumi", "Rp 70.845"),
        ("Bandeng", "Rp 36.121"), ("Nila", "Rp 30.386"),
        ("Tuna", "Rp 40.473"), ("Lele", "Rp 23.934"),
    ][:count]
    body = "".join(f"<tr><td>{name}</td><td>{price}</td></tr>" for name, price in rows)
    return f'<div id="tableHead"><h5>{period}</h5></div><table id="tabel-harga"><tbody>{body}</tbody></table>'


class CommodityParserTest(unittest.TestCase):
    def test_parses_verified_table(self):
        start, end, prices = parse_page(page(), date(2026, 9, 24))
        self.assertEqual((start, end), (date(2026, 9, 23), date(2026, 9, 30)))
        self.assertEqual(prices["Bandeng"], 36121)
        self.assertEqual(len(prices), 6)

    def test_rejects_stale_period(self):
        with self.assertRaisesRegex(ValueError, "tidak mencakup"):
            parse_page(page(), date(2026, 10, 5))

    def test_rejects_partial_table(self):
        with self.assertRaisesRegex(ValueError, "impor dibatalkan"):
            parse_page(page(count=2), date(2026, 9, 24))

    def test_cross_month_period(self):
        start, end, _ = parse_page(page("30 Sep - 7 Okt 2026"), date(2026, 10, 2))
        self.assertEqual((start, end), (date(2026, 9, 30), date(2026, 10, 7)))


if __name__ == "__main__":
    unittest.main()
