
import random
import sys
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection

BATCH_SIZE = 5000
INTERVAL_MINUTES = 10
RANDOM_SEED = 20261022


def generate_temperature_readings():
    rng = random.Random(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT
                s.shipment_id,
                sl.logger_id,
                COALESCE(s.actual_departure, s.planned_departure),
                COALESCE(s.actual_arrival, s.planned_arrival),
                p.min_temp_c,
                p.max_temp_c
            FROM shipment s
            JOIN lot l
                ON s.lot_id = l.lot_id
            JOIN product p
                ON l.product_id = p.product_id
            JOIN shipmentlogger sl
                ON s.shipment_id = sl.shipment_id
            WHERE sl.assignment_status IN ('ASSIGNED', 'UNASSIGNED')
            ORDER BY s.shipment_id
        """)

        shipments = cursor.fetchall()

        if not shipments:
            print("No shipments found. Check shipment and logger assignments.")
            return

        batch = []
        generated = 0

        insert_sql = """
            INSERT IGNORE INTO temperaturereading
            (
                reading_id,
                logger_id,
                shipment_id,
                reading_time,
                temperature_c,
                quality_status,
                source
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        print(f"Processing {len(shipments)} shipments...")

        for shipment in shipments:
            (
                shipment_id,
                logger_id,
                departure,
                arrival,
                min_temp,
                max_temp,
            ) = shipment

            if not departure or not arrival or arrival < departure:
                print(f"Skipping invalid dates: {shipment_id}")
                continue

            min_temp = float(min_temp)
            max_temp = float(max_temp)

            # Keep baseline readings safely inside the product range.
            margin = min((max_temp - min_temp) * 0.10, 0.5)
            safe_min = min_temp + margin
            safe_max = max_temp - margin

            reading_time = departure

            while reading_time <= arrival:
                temperature = round(
                    rng.uniform(safe_min, safe_max), 2
                )

                reading_id = (
                    f"RDG-{shipment_id}-"
                    f"{reading_time.strftime('%Y%m%d%H%M%S')}"
                )

                batch.append((
                    reading_id,
                    logger_id,
                    shipment_id,
                    reading_time,
                    temperature,
                    "VALID",
                    "SYNTHETIC",
                ))

                if len(batch) >= BATCH_SIZE:
                    cursor.executemany(insert_sql, batch)
                    connection.commit()
                    generated += len(batch)
                    batch.clear()

                    if generated % 50000 == 0:
                        print(f"Processed {generated:,} reading records...")

                reading_time += timedelta(minutes=INTERVAL_MINUTES)

        if batch:
            cursor.executemany(insert_sql, batch)
            connection.commit()
            generated += len(batch)

        cursor.execute("SELECT COUNT(*) FROM temperaturereading")
        total = cursor.fetchone()[0]

        print("\nTemperature reading generation finished.")
        print(f"Records processed for insertion: {generated:,}")
        print(f"Total records now in database: {total:,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_temperature_readings()
