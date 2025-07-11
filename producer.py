"""
Copyright (C) 2024 BeaconFire Staffing Solutions
Author: Ray Wang

This file is part of Oct DE Batch Kafka Project 1 Assignment.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import os
from confluent_kafka import Producer
import confluent_kafka
from confluent_kafka.serialization import StringSerializer
import psycopg2
import json
import time

KAFKA_HOST    = os.getenv('KAFKA_HOST', 'localhost')
KAFKA_PORT    = os.getenv('KAFKA_PORT', '29092')
DB_HOST       = os.getenv('DB_HOST',    'localhost')
DB_PORT       = os.getenv('DB_PORT',    '5432')
DB_NAME       = os.getenv('DB_NAME',    'source')
DB_USER       = os.getenv('DB_USER',    'source')
DB_PASSWORD   = os.getenv('DB_PASSWORD','source')

employee_topic_name = "bf_employee_cdc"

class cdcProducer(Producer):
    def __init__(self):
        super().__init__({
            'bootstrap.servers': f'{KAFKA_HOST}:{KAFKA_PORT}',
            'acks': 'all',
        })
        self.running = True
        self.last_offset = 0 # track the last action_id seen
    
    def fetch_cdc(self,):
        conn = psycopg2.connect(
            host     = DB_HOST,
            database = DB_NAME,
            user     = DB_USER,
            port     = DB_PORT,
            password = DB_PASSWORD,
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            """
            SELECT action_id,
                emp_id,
                first_name,
                last_name,
                date_of_birth,
                city,
                action
            FROM emp_cdc
            WHERE action_id > %s
            ORDER BY action_id
            """,
            (self.last_offset,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

if __name__ == '__main__':
    # Serializer for key and value
    encoder = StringSerializer('utf-8')
    producer = cdcProducer()
    
    while producer.running:
        # 1) Fetch new CDC records
        events = producer.fetch_cdc()

        # 2) print out current status
        if not events:
            print("[Producer] idle — no new CDC rows")
        else:
            print(f"[Producer] found {len(events)} new event(s), producing…")

        # 3) For each change event, serialize & produce to Kafka
        for action_id, emp_id, first_name, last_name, dob, city, action in events:
            # Build JSON payload
            payload = json.dumps({
                'action_id': action_id,
                'emp_id': emp_id,
                'first_name': first_name,
                'last_name': last_name,
                'date_of_birth': dob.isoformat() if dob else None,
                'city': city,
                'action': action
            })
            try:
                producer.produce(
                    employee_topic_name,
                    key=encoder(str(emp_id), None),
                    value=encoder(payload, None)
                )
                # Wait for delivery
                producer.flush()
                # Advance offset tracker
                producer.last_offset = action_id
            except Exception as e:
                print(f"[Producer] Error sending record {action_id}: {e}")

        # Sleep briefly before polling again
        time.sleep(1)
    
