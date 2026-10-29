
import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection


ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH = ROOT / "data" / "ground_truth" / "anomaly_ground_truth.csv"


def validate_ground_truth():
    if not GROUND_TRUTH.exists():
        print(f"Ground-truth file not found: {GROUND_TRUTH}")
        return

    with GROUND_TRUTH.open(
        "r", newline="", encoding="utf-8"
    ) as file:
        expected_rows = list(csv.DictReader(file))

    expected_ids = {
        row["shipment_id"] for row in expected_rows
        if row["expected_decision"] == "NON_COMPLIANT"
    }

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT shipment_id, compliance_status
            FROM complianceresult
        """)
        result_rows = cursor.fetchall()
        actual_noncompliant = {
            shipment_id
            for shipment_id, status in result_rows
            if status == "NON_COMPLIANT"
        }

        true_positives = expected_ids & actual_noncompliant
        false_negatives = expected_ids - actual_noncompliant
        false_positives = actual_noncompliant - expected_ids

        print("\nGROUND-TRUTH VALIDATION")
        print("-----------------------")
        print(f"Expected non-compliant shipments: {len(expected_ids)}")
        print(f"Actually detected: {len(true_positives)}")
        print(f"False negatives: {len(false_negatives)}")
        print(f"False positives: {len(false_positives)}")

        if false_negatives:
            print("Missed shipments:", sorted(false_negatives))

        if false_positives:
            print("Unexpected non-compliant shipments:",
                  sorted(false_positives))

        # Check that each expected anomaly has a matching excursion report.
        cursor.execute("""
            SELECT shipment_id, duration_minutes, decision
            FROM excursionreport
        """)
        report_rows = cursor.fetchall()

        report_by_shipment = {}
        for shipment_id, duration, decision in report_rows:
            report_by_shipment.setdefault(shipment_id, []).append(
                (float(duration), decision)
            )

        duration_errors = []

        for row in expected_rows:
            shipment_id = row["shipment_id"]
            expected_duration = float(row["duration_minutes"])

            matches = report_by_shipment.get(shipment_id, [])
            matching = [
                (duration, decision)
                for duration, decision in matches
                if decision == "NON_COMPLIANT"
                and abs(duration - expected_duration) < 0.01
            ]

            if not matching:
                duration_errors.append(shipment_id)

        print(
            "Ground-truth excursion durations matched:",
            len(expected_ids) - len(duration_errors),
            "of",
            len(expected_ids),
        )

        if duration_errors:
            print("Duration/report mismatches:", sorted(duration_errors))

        passed = (
            not false_negatives
            and not false_positives
            and not duration_errors
        )

        print("\nVALIDATION STATUS:", "PASS" if passed else "FAIL")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    validate_ground_truth()
