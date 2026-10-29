
import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH_DIR = PROJECT_ROOT / "data" / "ground_truth"
GROUND_TRUTH_FILE = GROUND_TRUTH_DIR / "anomaly_ground_truth.csv"

# Number of consecutive out-of-range readings needed to exceed
# each product's maximum allowed excursion duration.
READINGS_PER_ANOMALY = {
    "Biologic B": 4,       # 30 minutes > 20-minute allowance
    "Vaccine A": 5,        # 40 minutes > 30-minute allowance
    "Frozen Sample C": 3,  # 20 minutes > 15-minute allowance
}


def generate_anomalies():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*)
            FROM temperaturereading
            WHERE source = 'SYNTHETIC_ANOMALY'
        """)

        if cursor.fetchone()[0] > 0 or GROUND_TRUTH_FILE.exists():
            print(
                "Anomalies or ground-truth file already exist. "
                "Stopping to prevent accidental duplicate changes."
            )
            return

        cursor.execute("""
            SELECT
                s.shipment_id,
                p.product_name,
                p.min_temp_c,
                p.max_temp_c,
                p.max_excursion_minutes,
                s.required_policy_id
            FROM shipment s
            JOIN lot l ON s.lot_id = l.lot_id
            JOIN product p ON l.product_id = p.product_id
            WHERE s.shipment_status = 'DELIVERED'
            ORDER BY s.shipment_id
        """)

        shipments = cursor.fetchall()

        selected = {
            "Biologic B": [],
            "Vaccine A": [],
            "Frozen Sample C": [],
        }

        # Select five eligible shipments per product.
        for shipment in shipments:
            shipment_id, product_name = shipment[0], shipment[1]

            if product_name not in selected:
                continue

            if len(selected[product_name]) >= 5:
                continue

            cursor.execute("""
                SELECT reading_id, reading_time
                FROM temperaturereading
                WHERE shipment_id = %s
                  AND quality_status = 'VALID'
                  AND source = 'SYNTHETIC'
                ORDER BY reading_time
            """, (shipment_id,))

            readings = cursor.fetchall()
            needed = READINGS_PER_ANOMALY[product_name]

            if len(readings) >= needed:
                selected[product_name].append(
                    (shipment, readings)
                )

        for product_name, entries in selected.items():
            if len(entries) < 5:
                raise RuntimeError(
                    f"Only {len(entries)} eligible shipments found "
                    f"for {product_name}; expected 5."
                )

        ground_truth = []
        updates = []

        for product_name, entries in selected.items():
            for shipment, readings in entries:
                (
                    shipment_id,
                    _,
                    min_temp,
                    max_temp,
                    max_excursion_minutes,
                    policy_id,
                ) = shipment

                needed = READINGS_PER_ANOMALY[product_name]

                # Choose a contiguous window near the middle of the trip.
                start_index = (len(readings) - needed) // 2
                window = readings[start_index:start_index + needed]

                # Create an above-maximum excursion.
                if product_name == "Frozen Sample C":
                    anomaly_temp = round(float(max_temp) + 5.0, 2)
                else:
                    anomaly_temp = round(float(max_temp) + 4.0, 2)

                start_time = window[0][1]
                end_time = window[-1][1]
                duration_minutes = int(
                    (end_time - start_time).total_seconds() / 60
                )

                if duration_minutes <= int(max_excursion_minutes):
                    raise RuntimeError(
                        f"Chosen window does not exceed the policy "
                        f"for {shipment_id}."
                    )

                for reading_id, reading_time in window:
                    updates.append((
                        anomaly_temp,
                        "SYNTHETIC_ANOMALY",
                        reading_id,
                    ))

                ground_truth.append({
                    "shipment_id": shipment_id,
                    "product_name": product_name,
                    "policy_id": policy_id,
                    "expected_issue": "TEMPERATURE_EXCURSION",
                    "expected_decision": "NON_COMPLIANT",
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_minutes": duration_minutes,
                    "max_excursion_minutes": int(max_excursion_minutes),
                    "anomaly_temperature_c": anomaly_temp,
                    "injected_reading_count": needed,
                })

        # Update only the selected readings, preserving all other data.
        cursor.executemany("""
            UPDATE temperaturereading
            SET temperature_c = %s,
                source = %s
            WHERE reading_id = %s
        """, updates)

        connection.commit()

        GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

        with GROUND_TRUTH_FILE.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=ground_truth[0].keys()
            )
            writer.writeheader()
            writer.writerows(ground_truth)

        print("\nControlled anomaly generation completed.")
        print(f"Shipments with injected anomalies: {len(ground_truth)}")
        print(f"Readings modified: {len(updates)}")
        print(f"Ground truth saved to: {GROUND_TRUTH_FILE}")

        for product_name, entries in selected.items():
            print(f"{product_name}: {len(entries)} shipments")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_anomalies()
