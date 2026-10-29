
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection


def run_data_quality_checks():
    connection = get_connection()
    cursor = connection.cursor()
    failures = 0

    checks = [
        (
            "Shipments without temperature readings",
            """
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN temperaturereading r
                ON r.shipment_id = s.shipment_id
            WHERE r.reading_id IS NULL
            """,
            0,
        ),
        (
            "Shipments without logger assignments",
            """
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN shipmentlogger sl
                ON sl.shipment_id = s.shipment_id
            WHERE sl.assignment_id IS NULL
            """,
            0,
        ),
        (
            "Readings with missing logger references",
            """
            SELECT COUNT(*)
            FROM temperaturereading r
            LEFT JOIN logger l ON l.logger_id = r.logger_id
            WHERE l.logger_id IS NULL
            """,
            0,
        ),
        (
            "Readings outside product thresholds",
            """
            SELECT COUNT(*)
            FROM temperaturereading r
            JOIN shipment s ON s.shipment_id = r.shipment_id
            JOIN lot lo ON lo.lot_id = s.lot_id
            JOIN product p ON p.product_id = lo.product_id
            WHERE r.quality_status = 'VALID'
              AND (
                  r.temperature_c < p.min_temp_c
                  OR r.temperature_c > p.max_temp_c
              )
            """,
            60,
        ),
        (
            "Shipments without compliance results",
            """
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN complianceresult cr
                ON cr.shipment_id = s.shipment_id
            WHERE cr.compliance_result_id IS NULL
            """,
            0,
        ),
        (
            "Shipments without custody events",
            """
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN custodyevent ce
                ON ce.shipment_id = s.shipment_id
            WHERE ce.custody_event_id IS NULL
            """,
            0,
        ),
        (
            "Shipments without route stops",
            """
            SELECT COUNT(*)
            FROM shipment s
            LEFT JOIN routestop rs
                ON rs.shipment_id = s.shipment_id
            WHERE rs.route_stop_id IS NULL
            """,
            0,
        ),
        (
            "Non-compliant shipments without exceptions",
            """
            SELECT COUNT(*)
            FROM complianceresult cr
            LEFT JOIN exceptionevent ee
                ON ee.shipment_id = cr.shipment_id
               AND ee.issue_type = 'TEMPERATURE_EXCURSION'
            WHERE cr.compliance_status = 'NON_COMPLIANT'
              AND ee.exception_id IS NULL
            """,
            0,
        ),
    ]

    try:
        print("\nDATA QUALITY REPORT")
        print("=" * 65)

        for label, query, expected in checks:
            cursor.execute(query)
            actual = int(cursor.fetchone()[0])
            passed = actual == expected

            print(
                f"{'PASS' if passed else 'FAIL'} | {label}: "
                f"{actual} (expected {expected})"
            )

            if not passed:
                failures += 1

        cursor.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT reading_id
                FROM temperaturereading
                GROUP BY reading_id
                HAVING COUNT(*) > 1
            ) duplicates
        """)
        duplicate_ids = int(cursor.fetchone()[0])
        print(
            f"{'PASS' if duplicate_ids == 0 else 'FAIL'} | "
            f"Duplicate reading IDs: {duplicate_ids}"
        )

        if duplicate_ids:
            failures += 1

        print("\nFINAL STATUS:", "PASS" if failures == 0 else "FAIL")
        print(f"Failed checks: {failures}")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    run_data_quality_checks()
