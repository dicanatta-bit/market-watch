import unittest
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.models import PipelineRun
from app.scrapers import pipeline


class PipelineAuditTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    @patch("app.scrapers.pipeline.subprocess.run")
    def test_manual_run_records_success_and_all_steps(self, mocked_run):
        mocked_run.return_value = Mock(returncode=0, stdout="ok", stderr="")
        with patch("app.scrapers.pipeline.SessionLocal", return_value=self.db):
            pipeline.run("manual")
        recorded = self.db.query(PipelineRun).one()
        self.assertEqual(recorded.trigger, "manual")
        self.assertEqual(recorded.status, "success")
        self.assertIsNotNone(recorded.finished_at)
        self.assertEqual(mocked_run.call_count, len(pipeline.STEPS))


if __name__ == "__main__":
    unittest.main()
