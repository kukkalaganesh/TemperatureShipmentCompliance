
import sys
import json
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection


READING_INTERVAL = timedelta(minutes=10)


def evaluate_compliance():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Avoid duplicate results if the script is run again.
        cursor.execute("SELECT COUNT(*) FROM complianceresult")
        if cursor.fetchone()[0] > 0:
            print(
                "Compliance results already exist. "
                "Stopping to prevent duplicate evaluations."
            )
            return

        cursor.execute("SELECT COUNT(*) FROM excursionreport")
        if cursor.fetchone()[0] > 0:
            print(
                "Excursion reports already exist. "
                "Stopping to prevent duplicate reports."
            )
            return

        cursor.execute("""
            SELECT
                s.shipment_id,
                s.required_policy_id,
                p.min_temp_c,
                p.max_temp_c,
                p.max_excursion_minutes
            FROM shipment s
            JOIN thresholdpolicy p
                ON p.policy_id = s.required_policy_id
            ORDER BY s.shipment_id
        """)
        shipments = cursor.fetchall()

        excursion_rows = []
        result_rows = []

        for (
            shipment_id,
            policy_id,
            min_temp,
            max_temp,
            max_excursion_minutes,
        ) in shipments:

            min_temp = float(min_temp)
            max_temp = float(max_temp)
            max_excursion_minutes = int(max_excursion_minutes)

            cursor.execute("""
                SELECT
                    tr.reading_id,
                    tr.logger_id,
                    tr.reading_time,
                    tr.temperature_c,
                    tr.quality_status
                FROM temperaturereading tr
                WHERE tr.shipment_id = %s
                ORDER BY tr.reading_time
            """, (shipment_id,))

            readings = cursor.fetchall()
            valid_readings = [
                row for row in readings if row[4] == "VALID"
            ]

            cursor.execute("""
                SELECT COUNT(*)
                FROM custodyevent
                WHERE shipment_id = %s
            """, (shipment_id,))
            custody_count = cursor.fetchone()[0]

            issues = []
            detected_excursions = []

            # Group consecutive valid out-of-range readings.
            current_group = []

            def save_excursion(group):
                if not group:
                    return

                start_time = group[0][2]
                end_time = group[-1][2]

                duration = (
                    end_time - start_time
                ).total_seconds() / 60.0

                low = min(float(row[3]) for row in group)
                high = max(float(row[3]) for row in group)

                if duration > max_excursion_minutes:
                    decision = "NON_COMPLIANT"
                else:
                    decision = "EXCURSION_WITHIN_DURATION"

                detected_excursions.append({
                    "shipment_id": shipment_id,
                    "logger_id": group[0][1],
                    "policy_id": policy_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "reading_count": len(group),
                    "min_observed": low,
                    "max_observed": high,
                    "decision": decision,
                })

            for reading in readings:
                reading_id, logger_id, reading_time, temperature, quality = reading

                out_of_range = (
                    quality == "VALID"
                    and (
                        float(temperature) < min_temp
                        or float(temperature) > max_temp
                    )
                )

                if out_of_range:
                    if current_group:
                        gap = reading_time - current_group[-1][2]
                        if gap > READING_INTERVAL:
                            save_excursion(current_group)
                            current_group = []

                    current_group.append(reading)
                else:
                    save_excursion(current_group)
                    current_group = []

            save_excursion(current_group)

            if not valid_readings:
                issues.append("NO_VALID_TEMPERATURE_READINGS")

            if custody_count < 3:
                issues.append("CUSTODY_GAP")

            if detected_excursions:
                issues.append("TEMPERATURE_EXCURSION")

            if any(
                excursion["decision"] == "NON_COMPLIANT"
                for excursion in detected_excursions
            ):
                status = "NON_COMPLIANT"
                reason = (
                    "One or more temperature excursions exceeded "
                    "the policy duration allowance."
                )
            elif not valid_readings or custody_count < 3:
                status = "REVIEW_REQUIRED"
                reason = (
                    "Required temperature or custody evidence "
                    "is missing or incomplete."
                )
            else:
                status = "COMPLIANT"
                reason = (
                    "Valid temperature readings remained within "
                    "policy limits, or detected excursions did not "
                    "exceed the policy duration allowance."
                )

            for excursion in detected_excursions:
                excursion_rows.append((
                    (
                        f"EXC-{shipment_id}-"
                        f"{excursion['start_time'].strftime('%Y%m%d%H%M%S')}"
                    )[:30],
                    excursion["shipment_id"],
                    excursion["logger_id"],
                    excursion["policy_id"],
                    excursion["start_time"],
                    excursion["end_time"],
                    round(excursion["duration"], 2),
                    excursion["reading_count"],
                    round(excursion["min_observed"], 2),
                    round(excursion["max_observed"], 2),
                    excursion["decision"],
                ))

            result_rows.append((
                shipment_id,
                status,
                json.dumps(issues),
                len(readings),
                custody_count,
                policy_id,
                reason,
            ))

        if excursion_rows:
            cursor.executemany("""
                INSERT INTO excursionreport
                (
                    excursion_id, shipment_id, logger_id, policy_id,
                    start_time, end_time, duration_minutes,
                    reading_count, min_observed_c, max_observed_c,
                    decision
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, excursion_rows)

        if result_rows:
            cursor.executemany("""
                INSERT INTO complianceresult
                (
                    shipment_id, compliance_status, issue_codes,
                    reading_count, custody_event_count, policy_id,
                    decision_reason
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, result_rows)

        connection.commit()

        counts = {
            "COMPLIANT": 0,
            "NON_COMPLIANT": 0,
            "REVIEW_REQUIRED": 0,
        }

        for row in result_rows:
            counts[row[1]] += 1

        print("\nCompliance evaluation completed.")
        print(f"Shipments evaluated: {len(result_rows):,}")
        print(f"Excursion reports created: {len(excursion_rows):,}")
        print(f"Compliant: {counts['COMPLIANT']:,}")
        print(f"Non-compliant: {counts['NON_COMPLIANT']:,}")
        print(f"Review required: {counts['REVIEW_REQUIRED']:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    evaluate_compliance()
