import os
import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import KnmpLocation
from app.routers.export_router import export_excel, export_pdf


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.db.add(KnmpLocation(id_lokasi=1, nama_kampung="Kampung Uji",
                                 provinsi="JAWA TIMUR", kabupaten="Banyuwangi",
                                 kecamatan="Muncar", status_knmp="Hub",
                                 jumlah_nelayan=15, jumlah_kapal=4,
                                 lat=-8.4, lon=114.3, tahun=date.today().year))
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def _assert_export(self, handler, signature):
        response = handler(pulau="Jawa-Bali", provinsi=None, db=self.db, _=None)
        try:
            with open(response.path, "rb") as exported:
                self.assertEqual(exported.read(len(signature)), signature)
            self.assertIn("Jawa-Bali", response.headers["content-disposition"])
        finally:
            if os.path.exists(response.path):
                os.unlink(response.path)

    def test_excel_export_is_a_workbook(self):
        self._assert_export(export_excel, b"PK")

    def test_pdf_export_is_a_pdf(self):
        self._assert_export(export_pdf, b"%PDF")


if __name__ == "__main__":
    unittest.main()
