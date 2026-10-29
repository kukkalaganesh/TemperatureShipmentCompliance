
from db_connection import get_connection

connection = get_connection()
cursor = connection.cursor()

query = """
SELECT
    s.shipment_id,
    p.product_name,
    p.min_temp_c,
    p.max_temp_c,
    p.max_excursion_minutes,
    s.required_policy_id,
    COUNT(tr.reading_id) AS readings
FROM shipment s
JOIN lot l
    ON s.lot_id = l.lot_id
JOIN product p
    ON l.product_id = p.product_id
JOIN temperaturereading tr
    ON tr.shipment_id = s.shipment_id
GROUP BY
    s.shipment_id,
    p.product_name,
    p.min_temp_c,
    p.max_temp_c,
    p.max_excursion_minutes,
    s.required_policy_id
ORDER BY s.shipment_id
LIMIT 12
"""

try:
    cursor.execute(query)

    print("\nSample shipment temperature data:\n")

    for row in cursor.fetchall():
        print(row)

finally:
    cursor.close()
    connection.close()
