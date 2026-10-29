
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection


def generate_exception_events():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM exceptionevent")
        existing = cursor.fetchone()[0]

        if existing > 0:
            print(
                f"exceptionevent already contains {existing} records. "
                "Stopping to prevent duplicate exceptions."
            )
            return

        cursor.execute("""
            SELECT
                e.shipment_id,
                e.start_time,
                e.end_time,
                e.duration_minutes,
                e.decision,
                p.max_excursion_minutes
            FROM excursionreport e
            JOIN thresholdpolicy p
                ON p.policy_id = e.policy_id
            ORDER BY e.shipment_id, e.start_time
        """)

        excursions = cursor.fetchall()
        exception_rows = []

        for row in excursions:
            (
                shipment_id,
                start_time,
                end_time,
                duration,
                decision,
                max_allowed,
            ) = row

            if decision != "NON_COMPLIANT":
                continue

            duration = float(duration)
            max_allowed = int(max_allowed)

            if duration >= max_allowed * 2:
                severity = "CRITICAL"
            elif duration >= max_allowed * 1.5:
                severity = "HIGH"
            else:
                severity = "MEDIUM"

            description = (
                f"Temperature excursion detected from "
                f"{start_time} to {end_time}. "
                f"Estimated duration: {duration:.2f} minutes. "
                f"Maximum permitted excursion duration: "
                f"{max_allowed} minutes. "
                f"Compliance decision: {decision}. "
                f"Investigation required."
            )

            exception_rows.append((
                shipment_id,
                "TEMPERATURE_EXCURSION",
                severity,
                end_time,
                description,
                "OPEN",
                None,
            ))

        if exception_rows:
            cursor.executemany("""
                INSERT INTO exceptionevent
                (
                    shipment_id,
                    issue_type,
                    severity,
                    detected_at,
                    description,
                    resolution_status,
                    resolved_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, exception_rows)

        connection.commit()

        print("\nException event generation completed.")
        print(f"Excursions reviewed: {len(excursions):,}")
        print(f"Exception events inserted: {len(exception_rows):,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_exception_events()
