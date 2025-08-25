import json
import time
import requests
import io
import numpy as np
import pandas as pd
from kafka import KafkaProducer
import pyarrow.parquet as pq
import heapq
import sys

end_event_buffer = []

def json_serializable(record):
    new_record = {}
    for k, v in record.items():
        if isinstance(v, (np.int64, np.int32)):
            new_record[k] = int(v)
        elif isinstance(v, (np.float64, np.float32)):
            new_record[k] = float(v)
        elif isinstance(v, (pd.Timestamp, np.datetime64)):
            new_record[k] = v.isoformat()
        else:
            new_record[k] = v
    return new_record

def download_parquet_and_get_iterator(url):
    print(f"Pobieranie: {url}")
    r = requests.get(url)
    parquet_bytes_io = io.BytesIO(r.content)
    parquet_file = pq.ParquetFile(parquet_bytes_io)
    print(f"Pobrano: {url} (do pamięci, ale teraz iterujemy po chunkach)")
    return parquet_file 


def process_event_pair(start_event, end_event, producer):
    heapq.heappush(end_event_buffer, (end_event['timestamp'], end_event['PULocationID'], end_event['DOLocationID'], end_event))

    while end_event_buffer and start_event['timestamp'] > end_event_buffer[0][0]:
        _, _, _, e = heapq.heappop(end_event_buffer)
        producer.send('end_topic', value=e)

    producer.send('start_topic', value=start_event)

def send_trip_events_simulated(parquet_file_obj, producer, speedup):
    num_row_groups = parquet_file_obj.num_row_groups
    
    for i in range(num_row_groups):
        print(f"Processing row group {i+1}/{num_row_groups}")
        df_chunk = parquet_file_obj.read_row_group(i).to_pandas()

        # # Konwersja na datetime
        df_chunk['tpep_pickup_datetime'] = pd.to_datetime(df_chunk['tpep_pickup_datetime'])
        df_chunk['tpep_dropoff_datetime'] = pd.to_datetime(df_chunk['tpep_dropoff_datetime'])

        df_chunk = df_chunk.sort_values(by="tpep_pickup_datetime").reset_index(drop=True)

        start_time = df_chunk['tpep_pickup_datetime'].iloc[0]
        real_start = time.time()

        for idx, row in df_chunk.iterrows():
            data_offset_sec = (row['tpep_pickup_datetime'] - start_time).total_seconds()
            wait_sec = data_offset_sec / speedup - (time.time() - real_start)

            if wait_sec > 0.01:
                time.sleep(wait_sec)

            start_event = {
                'timestamp': row['tpep_pickup_datetime'],
                'PULocationID': int(row['PULocationID']),
                'DOLocationID': int(row['DOLocationID']),
            }
            end_event = {
                'timestamp': row['tpep_dropoff_datetime'],
                'PULocationID': int(row['PULocationID']),
                'DOLocationID': int(row['DOLocationID']),
            }

            process_event_pair(start_event, end_event, producer)

    while end_event_buffer:
        _, _, _, e = heapq.heappop(end_event_buffer)
        producer.send('end_topic', value=e)

    producer.flush()

def main():
    speedup = float(sys.argv[1]) if len(sys.argv) > 1 else 1200.0

    producer = KafkaProducer(
        bootstrap_servers='kafka:9092',
        value_serializer=lambda v: json.dumps(json_serializable(v)).encode('utf-8'),
    )

    urls = [
        "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-03.parquet"
    ]

    try:
        for url in urls:
            try:
                parquet_file_obj = download_parquet_and_get_iterator(url)
                send_trip_events_simulated(parquet_file_obj, producer, speedup)
            except Exception as e:
                print(f"Błąd podczas przetwarzania pliku {url}: {e}")
    finally:
        producer.close()

if __name__ == "__main__":
    main()