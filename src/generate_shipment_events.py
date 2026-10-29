
import sys
import random
from pathlib import Path
from datetime import timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db_connection import get_connection


RANDOM_SEED = 20261029


def generate_shipment_events():
    rng = random.Random(RANDOM_SEED)
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Prevent accidental duplicate generation.
        for table in (
            "custodyevent",
            "routestop",
            "shipmentstatusevent",
        ):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]

            if count > 0:
                print(
                    f"{table} already contains {count} records. "
                    "No data was inserted. Check before rerunning."
                )
                return

        cursor.execute("""
            SELECT
                shipment_id,
                origin,
                destination,
                planned_departure,
                planned_arrival,
                actual_departure,
                actual_arrival,
                shipment_status
            FROM shipment
            ORDER BY shipment_id
        """)

        shipments = cursor.fetchall()

        if not shipments:
            print("No shipments found.")
            return

        custody_rows = []
        route_rows = []
        status_rows = []

        for shipment in shipments:
            (
                shipment_id,
                origin,
                destination,
                planned_departure,
                planned_arrival,
                actual_departure,
                actual_arrival,
                shipment_status,
            ) = shipment

            departure = actual_departure or planned_departure
            arrival = actual_arrival or planned_arrival

            if not departure or not arrival or arrival <= departure:
                print(f"Skipping invalid timeline: {shipment_id}")
                continue

            duration = arrival - departure

            # Generate one intermediate stop during transit.
            dwell_minutes = rng.randint(15, 90)
            midpoint = departure + duration / 2
            stop_departure = midpoint + timedelta(
                minutes=dwell_minutes
            )

            if stop_departure >= arrival:
                stop_departure = arrival - timedelta(minutes=1)
                dwell_minutes = max(
                    0,
                    int((stop_departure - midpoint).total_seconds() / 60)
                )

            # 1. Chain-of-custody history.
            custody_rows.extend([
                (
                    f"CUS-{shipment_id}-PICK",
                    shipment_id,
                    departure,
                    "Origin Warehouse",
                    "Carrier",
                    origin,
                    "PICKUP",
                ),
                (
                    f"CUS-{shipment_id}-HAND",
                    shipment_id,
                    midpoint,
                    "Carrier",
                    "Transit Hub",
                    "Intermediate Transit Hub",
                    "HANDOFF",
                ),
                (
                    f"CUS-{shipment_id}-DELV",
                    shipment_id,
                    arrival,
                    "Carrier",
                    "Destination Warehouse",
                    destination,
                    "DELIVERY",
                ),
            ])

            # 2. Route history: origin, intermediate stop, destination.
            route_rows.extend([
                (
                    f"RT-{shipment_id}-01",
                    shipment_id,
                    1,
                    origin,
                    departure,
                    departure,
                    0,
                ),
                (
                    f"RT-{shipment_id}-02",
                    shipment_id,
                    2,
                    "Intermediate Transit Hub",
                    midpoint,
                    stop_departure,
                    dwell_minutes,
                ),
                (
                    f"RT-{shipment_id}-03",
                    shipment_id,
                    3,
                    destination,
                    arrival,
                    arrival,
                    0,
                ),
            ])

            # 3. Status history matching the shipment timeline.
            planned_event_time = departure - timedelta(hours=1)

            status_rows.extend([
                (
                    shipment_id,
                    None,
                    "PLANNED",
                    planned_event_time,
                    "Shipment System",
                    "Shipment scheduled",
                ),
                (
                    shipment_id,
                    "PLANNED",
                    "IN_TRANSIT",
                    departure,
                    "Carrier",
                    "Shipment departed origin",
                ),
                (
                    shipment_id,
                    "IN_TRANSIT",
                    shipment_status,
                    arrival,
                    "Shipment System",
                    "Recorded shipment arrival and final status",
                ),
            ])

        # Insert all event records in one transaction.
        cursor.executemany("""
            INSERT INTO custodyevent
            (
                custody_event_id, shipment_id, event_time,
                from_party, to_party, location, event_type
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, custody_rows)

        cursor.executemany("""
            INSERT INTO routestop
            (
                route_stop_id, shipment_id, stop_sequence,
                location, arrival_time, departure_time, dwell_minutes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, route_rows)

        cursor.executemany("""
            INSERT INTO shipmentstatusevent
            (
                shipment_id, previous_status, new_status,
                changed_at, changed_by, reason
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, status_rows)

        connection.commit()

        print("\nShipment event generation completed.")
        print(f"Shipments processed: {len(shipments):,}")
        print(f"Custody events inserted: {len(custody_rows):,}")
        print(f"Route stops inserted: {len(route_rows):,}")
        print(f"Status events inserted: {len(status_rows):,}")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    generate_shipment_events()
