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


import json
import os
from datetime import datetime
import psycopg2
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from confluent_kafka.serialization import StringDeserializer
from producer import employee_topic_name

# ─── Read Docker-Compose env vars ───────────────────────────
KAFKA_HOST   = os.getenv("KAFKA_HOST", "localhost")
KAFKA_PORT   = os.getenv("KAFKA_PORT", "29092")
DB_HOST      = os.getenv("DB_HOST",    "localhost")
DB_PORT      = os.getenv("DB_PORT",    "5432")
DB_NAME      = os.getenv("DB_NAME",    "destination")
DB_USER      = os.getenv("DB_USER",    "destination")
DB_PASSWORD  = os.getenv("DB_PASSWORD","destination")
GROUP_ID     = os.getenv("GROUP_ID",   "cdc_group")

dlq_topic_name = f"{employee_topic_name}_dlq"

class cdcConsumer(Consumer):
    def __init__(self, host: str, port: str, group_id: str):
        self.conf = {'bootstrap.servers': f'{host}:{port}',
                     'group.id': group_id,
                     'enable.auto.commit': False,    # manual commit after DB write
                     'auto.offset.reset': 'earliest'}
        super().__init__(self.conf)
        self.keep_runnning = True
        # For deserializing incoming messages
        self.deserializer = StringDeserializer('utf-8')
        # Producer for sending to DLQ on failure
        self.dlq_producer = Producer({'bootstrap.servers': f"{host}:{port}", 'acks': 'all'})

    def consume(self, topics, processing_func):
        try:
            self.subscribe(topics)
            while self.keep_runnning:
                msg = self.poll(timeout=1.0)
                if msg is None:
                    print("[Consumer] idle — no messages received")
                    continue
                if msg.error():
                    # Ignore partition EOF, rethrow others
                    if msg.error().code() != KafkaError._PARTITION_EOF:
                        raise KafkaException(msg.error())
                    continue
            
                try:
                    # Deserialize & parse JSON
                    raw = msg.value()
                    body = self.deserializer(raw, None)
                    event = json.loads(body)
                    print(f"[Consumer] ← received emp_id={event['emp_id']}, action={event['action']}")

                    # --- DLQ validation rules ---
                    emp_id = event.get('emp_id')
                    dob_str = event.get('date_of_birth')

                    # Rule 1: emp_id must be positive
                    if isinstance(emp_id, int) and emp_id < 0:
                        error_msg = "emp_id should be a positive number."

                    elif dob_str:
                        try:
                            year = datetime.fromisoformat(dob_str).year
                            if year >= 2007:
                                error_msg = "Any employee should at least be 18 years old."
                            else:
                                error_msg = None
                        except ValueError:
                            error_msg = None
                    else:
                        error_msg = None

                    if error_msg:
                        # Send directly to DLQ and commit offset
                        print(f"[Consumer] DLQ rule triggered for emp_id={emp_id}: {error_msg}")
                        dlq_message = {
                            'original_topic':    msg.topic(),
                            'original_partition':msg.partition(),
                            'original_offset':   msg.offset(),
                            'error':             error_msg,
                            'original_message':  body
                        }
                        self.dlq_producer.produce(
                            dlq_topic_name,
                            key=msg.key(),
                            value=json.dumps(dlq_message).encode('utf-8')
                        )
                        self.dlq_producer.flush()
                        self.commit(message=msg, asynchronous=False)
                        continue

                    # --- normal processing ---
                    processing_func(event)
                    print(f"[Consumer] ✓ applied {event['action']} for emp_id={event['emp_id']}")

                    # 3) Commit offset only after successful DB write
                    self.commit(message=msg, asynchronous=False)

                except Exception as e:
                    print(f"[Consumer] Error processing message: {e}")

                    # Create DLQ message with metadata
                    dlq_message = {
                        'original_topic': msg.topic(),
                        'original_partition': msg.partition(),
                        'original_offset': msg.offset(),
                        'error': str(e),
                        'original_message': msg.value().decode('utf-8') if msg.value() else None
                    }

                    # Send problematic record to DLQ
                    self.dlq_producer.produce(dlq_topic_name,
                                              key=msg.key(),
                                              value=json.dumps(dlq_message).encode('utf-8'))
                    self.dlq_producer.flush()
                    # Commit offset so we don't retry the bad message
                    self.commit(message=msg, asynchronous=False)
        finally:
            self.close()

def update_dst(event):
    """
    Apply a single CDC event (dict) to employee_b
    """
    try:
        conn = psycopg2.connect(
            host     = DB_HOST,
            database = DB_NAME,
            user     = DB_USER,
            port     = DB_PORT,
            password = DB_PASSWORD
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        action = event.get('action')
        emp_id = event.get('emp_id')
        first_name = event.get('first_name')
        last_name = event.get('last_name')
        dob = event.get('date_of_birth')
        city = event.get('city')

        if action == 'INSERT':
            cur.execute(
                """
                INSERT INTO employee_b (emp_id, first_name, last_name, date_of_birth, city)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (emp_id) DO NOTHING
                """,
                (emp_id, first_name, last_name, dob, city)
            )
        elif action == 'UPDATE':
            cur.execute(
                """
                UPDATE employee_b
                SET first_name = %s,
                    last_name = %s,
                    date_of_birth = %s,
                    city = %s
                WHERE emp_id = %s
                """,
                (first_name, last_name, dob, city, emp_id)
            )
        elif action == 'DELETE':
            cur.execute(
                "DELETE FROM employee_b WHERE emp_id = %s",
                (emp_id,)
            )
        else:
            print(f"[Consumer] Unknown action '{action}' for emp_id={emp_id}")

        cur.close()
        conn.close()
    except Exception as err:
        print(err)

if __name__ == '__main__':
    # Start the consumer loop
    consumer = cdcConsumer(
        host    = KAFKA_HOST,
        port    = KAFKA_PORT,
        group_id= GROUP_ID
    )
    consumer.consume([employee_topic_name], update_dst)