
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from db_connection import get_connection


GROUND_TRUTH = ROOT / "data" / "ground_truth" / "anomaly_ground_truth.csv"


class PipelineValidationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.connection = get_connection()
        cls.cursor = cls.connection.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.cursor.close()
        cls.connection.close()

    def count(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self.cursor.fetchone()[0]

    def test_all_shipments_have_temperature_readings(self):
        missing = self.count("""
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN temperaturereading r
                ON r.shipment_id = s.shipment_id
            WHERE r.reading_id IS NULL
        """)
        self.assertEqual(missing, 0)

    def test_all_shipments_have_compliance_results(self):
        missing = self.count("""
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN complianceresult cr
                ON cr.shipment_id = s.shipment_id
            WHERE cr.compliance_result_id IS NULL
        """)
        self.assertEqual(missing, 0)

    def test_no_duplicate_reading_ids(self):
        duplicates = self.count("""
            SELECT COUNT(*)
            FROM (
                SELECT reading_id
                FROM temperaturereading
                GROUP BY reading_id
                HAVING COUNT(*) > 1
            ) d
        """)
        self.assertEqual(duplicates, 0)

    def test_expected_compliance_counts(self):
        self.cursor.execute("""
            SELECT compliance_status, COUNT(*)
            FROM complianceresult
            GROUP BY compliance_status
        """)
        actual = dict(self.cursor.fetchall())

        self.assertEqual(actual.get("COMPLIANT", 0), 4985)
        self.assertEqual(actual.get("NON_COMPLIANT", 0), 15)
        self.assertEqual(actual.get("REVIEW_REQUIRED", 0), 0)

    def test_ground_truth_anomalies_were_detected(self):
        self.assertTrue(
            GROUND_TRUTH.exists(),
            f"Ground-truth file missing: {GROUND_TRUTH}"
        )

        with GROUND_TRUTH.open(
            "r", newline="", encoding="utf-8"
        ) as file:
            rows = list(csv.DictReader(file))

        expected = {
            row["shipment_id"]
            for row in rows
            if row["expected_decision"] == "NON_COMPLIANT"
        }

        self.cursor.execute("""
            SELECT shipment_id
            FROM complianceresult
            WHERE compliance_status = 'NON_COMPLIANT'
        """)
        actual = {row[0] for row in self.cursor.fetchall()}

        self.assertEqual(expected, actual)
        self.assertEqual(len(expected), 15)

    def test_noncompliant_shipments_have_exceptions(self):
        missing = self.count("""
            SELECT COUNT(*)
            FROM complianceresult cr
            WHERE cr.compliance_status = 'NON_COMPLIANT'
              AND NOT EXISTS (
                  SELECT 1
                  FROM exceptionevent ee
                  WHERE ee.shipment_id = cr.shipment_id
                    AND ee.issue_type = 'TEMPERATURE_EXCURSION'
              )
        """)
        self.assertEqual(missing, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
