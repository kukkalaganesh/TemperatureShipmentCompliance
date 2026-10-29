
from datetime import date, datetime, timedelta

from db_connection import get_connection


def seed_reference_data():
    connection = get_connection()
    if connection is None:
        raise RuntimeError("Could not connect to MySQL.")

    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM product")
        if cursor.fetchone()[0] == 0:
            products = [
                ("PROD-001", "Vaccine A", "Vaccine", 2.0, 8.0, 30),
                ("PROD-002", "Biologic B", "Biologic", 2.0, 8.0, 20),
                (
                    "PROD-003",
                    "Frozen Sample C",
                    "Laboratory Sample",
                    -25.0,
                    -15.0,
                    15,
                ),
            ]

            cursor.executemany(
                """
                INSERT INTO product
                (product_id, product_name, category, min_temp_c,
                 max_temp_c, max_excursion_minutes)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                products,
            )

        cursor.execute("SELECT COUNT(*) FROM packaging")
        if cursor.fetchone()[0] == 0:
            packaging = [
                ("PKG-001", "Insulated Box", 20, 0.850, 1),
                ("PKG-002", "Validated Cooler", 50, 0.950, 1),
                ("PKG-003", "Refrigerated Container", 200, 0.990, 1),
            ]

            cursor.executemany(
                """
                INSERT INTO packaging
                (packaging_id, packaging_type, capacity_units,
                 insulation_rating, active)
                VALUES (%s, %s, %s, %s, %s)
                """,
                packaging,
            )

        cursor.execute(
            """
            SELECT product_id, min_temp_c, max_temp_c,
                   max_excursion_minutes
            FROM product
            """
        )
        product_rows = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM thresholdpolicy")
        if cursor.fetchone()[0] == 0:
            now = datetime.now()

            policies = [
                (
                    f"POL-{product_id}",
                    product_id,
                    minimum,
                    maximum,
                    duration,
                    now - timedelta(days=365),
                    now + timedelta(days=365),
                    1,
                    "ACTIVE",
                )
                for product_id, minimum, maximum, duration in product_rows
            ]

            cursor.executemany(
                """
                INSERT INTO thresholdpolicy
                (policy_id, product_id, min_temp_c, max_temp_c,
                 max_excursion_minutes, effective_start, effective_end,
                 policy_version, policy_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                policies,
            )

        cursor.execute("SELECT COUNT(*) FROM lot")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "SELECT product_id FROM product ORDER BY product_id"
            )
            product_ids = [row[0] for row in cursor.fetchall()]

            today = date.today()
            lots = [
                (
                    f"LOT-{index:04d}",
                    product_id,
                    today - timedelta(days=30 + index),
                    today + timedelta(days=365),
                    "RELEASED",
                    100,
                )
                for index, product_id in enumerate(product_ids, start=1)
            ]

            cursor.executemany(
                """
                INSERT INTO lot
                (lot_id, product_id, manufacture_date, expiry_date,
                 lot_status, quantity_units)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                lots,
            )

        connection.commit()
        print("Reference data seeded successfully.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def seed_loggers():
    connection = get_connection()
    if connection is None:
        raise RuntimeError("Could not connect to MySQL.")

    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM logger")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(
                f"Logger table already contains {existing_count} records. "
                "Skipping."
            )
            return

        today = date.today()
        loggers = []

        for i in range(1, 1001):
            loggers.append(
                (
                    f"LOGGER-{i:05d}",
                    "TempTrack T100",
                    today - timedelta(days=90),
                    today + timedelta(days=275),
                    0.25,
                    "ACTIVE",
                )
            )

        cursor.executemany(
            """
            INSERT INTO logger
            (logger_id, model, calibration_date, calibration_due,
             calibration_uncertainty_c, logger_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            loggers,
        )

        connection.commit()
        print(f"Successfully created {len(loggers)} loggers.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


def seed_shipments():
    import random

    random.seed(20261022)

    connection = get_connection()
    if connection is None:
        raise RuntimeError("Could not connect to MySQL.")

    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM shipment")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(
                f"Shipment table already contains {existing_count} records. "
                "Skipping."
            )
            return

        cursor.execute(
            """
            SELECT l.lot_id, l.product_id, p.packaging_id, tp.policy_id
            FROM lot l
            JOIN product pr ON pr.product_id = l.product_id
            JOIN packaging p ON p.active = 1
            JOIN thresholdpolicy tp ON tp.product_id = l.product_id
            WHERE l.lot_status = 'RELEASED'
              AND tp.policy_status = 'ACTIVE'
              AND (tp.effective_end IS NULL OR tp.effective_end >= NOW())
            ORDER BY l.lot_id, p.packaging_id
            """
        )
        choices = cursor.fetchall()

        if not choices:
            raise RuntimeError(
                "No valid lot, packaging, and policy combinations found."
            )

        locations = [
            "Hyderabad",
            "Vijayawada",
            "Bengaluru",
            "Chennai",
            "Pune",
            "Mumbai",
            "Delhi",
            "Visakhapatnam",
            "Nagpur",
            "Kolkata",
        ]

        carriers = [f"CARRIER-{i:03d}" for i in range(1, 21)]
        base_time = datetime(2026, 1, 1, 8, 0, 0)
        shipments = []

        for i in range(1, 5001):
            lot_id, product_id, packaging_id, policy_id = random.choice(
                choices
            )

            origin = random.choice(locations)
            destination = random.choice(
                [place for place in locations if place != origin]
            )

            departure = base_time + timedelta(
                minutes=random.randint(0, 60 * 24 * 270)
            )
            travel_hours = random.randint(6, 72)
            arrival = departure + timedelta(hours=travel_hours)

            shipments.append(
                (
                    f"SHP-{i:06d}",
                    lot_id,
                    packaging_id,
                    policy_id,
                    origin,
                    destination,
                    departure,
                    arrival,
                    departure,
                    arrival,
                    "DELIVERED",
                    random.choice(carriers),
                )
            )

        cursor.executemany(
            """
            INSERT INTO shipment
            (shipment_id, lot_id, packaging_id, required_policy_id,
             origin, destination, planned_departure, planned_arrival,
             actual_departure, actual_arrival, shipment_status, carrier_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            shipments,
        )

        connection.commit()
        print(f"Successfully created {len(shipments)} shipments.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()



def seed_shipment_loggers():
    connection = get_connection()
    if connection is None:
        raise RuntimeError("Could not connect to MySQL.")

    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM temperaturereading")
        if cursor.fetchone()[0] > 0:
            raise RuntimeError(
                "Temperature readings already exist. "
                "Do not rebuild assignments."
            )

        cursor.execute(
            """
            SELECT shipment_id, planned_departure, planned_arrival
            FROM shipment
            ORDER BY planned_departure, planned_arrival, shipment_id
            """
        )
        shipments = cursor.fetchall()

        cursor.execute(
            """
            SELECT logger_id
            FROM logger
            WHERE logger_status = 'ACTIVE'
            ORDER BY logger_id
            """
        )
        loggers = [row[0] for row in cursor.fetchall()]

        if not shipments or not loggers:
            raise RuntimeError("Shipments or active loggers are missing.")

        # Greedy interval allocation: reuse a logger only after its
        # previous shipment has arrived.
        import heapq

        available = [(datetime.min, logger_id) for logger_id in loggers]
        heapq.heapify(available)

        assignments = []

        for shipment_id, departure, arrival in shipments:
            available_at, logger_id = heapq.heappop(available)

            if available_at > departure:
                raise RuntimeError(
                    "No logger available without overlapping assignments. "
                    "No assignment changes were committed."
                )

            assignment_number = len(assignments) + 1
            assignments.append(
                (
                    f"ASN-{assignment_number:06d}",
                    shipment_id,
                    logger_id,
                    departure,
                    arrival,
                    "UNASSIGNED",
                )
            )

            heapq.heappush(available, (arrival, logger_id))

        # Replace only assignment rows. The transaction can be rolled back
        # if insertion fails.
        cursor.execute("DELETE FROM shipmentlogger")

        cursor.executemany(
            """
            INSERT INTO shipmentlogger
            (assignment_id, shipment_id, logger_id, assigned_at,
             unassigned_at, assignment_status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            assignments,
        )

        connection.commit()
        print(f"Successfully rebuilt {len(assignments)} logger assignments.")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    seed_reference_data()
    seed_loggers()
