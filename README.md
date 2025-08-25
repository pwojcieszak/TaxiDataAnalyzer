# Taxi Streaming Analytics on GCP (Spark + Kafka)
## Project Overview
This project implements real-time stream processing using:

- **Apache Kafka** – to publish taxi ride start and end events,

- **Apache Spark Structured Streaming** – to analyze and query data in real time,

- **Terraform + Ansible** – to provision and configure a multi-node cluster on Google Cloud Platform (GCP).

The data source is the publicly available NYC Taxi Trip Records (Yellow Taxi):
[NYC TLC Trip Data](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
## Main Features

1. Provision a multi-machine Spark + Kafka cluster on GCP.

2. Stream taxi rides into Kafka as two separate events: start and end.

3. Perform SQL queries on live streams (e.g., number of trips between all zone pairs for each wall clock hour).

4. Use aggregated statistics to detect days with unusual traffic patterns, separated by day of the week.

## Architecture
```
Terraform + Ansible → GCP (VMs)
        │
        ├── Kafka (start_topic / end_topic)
        │
 producer.py → publishes start/end events
        │
 Spark Structured Streaming (consumer)
        │
 SQL Aggregations → HDFS / Parquet → Outlier Detection
```

## Setup & Execution
**1. Infrastructure Setup on GCP**

The entire provisioning process is automated in cloud_setup.ipynb:

- Installs required tools (Terraform, Ansible, gcloud CLI),
  
- Configures environment variables and SSH keys,
  
- Runs Terraform (terraform apply) to create VM instances,
  
- Uses Ansible to configure Kafka and Spark across the cluster.

After running the notebook, you will have a working multi-node Spark + Kafka cluster on GCP.

**2. Kafka Prducer (Event Simulation)**
The script producer.py:

- Downloads Parquet files with NYC taxi trips,

- Simulates accelerated real-time event streaming,

- Splits each trip into two events:

  - pickup → published to start_topic,

  - dropoff → published to end_topic.

Run the producer (with a configurable speedup factor, default = 1200x real-time):

```
python producer.py 1200
```
**3. Kafka Consumer (Spark Structured Streaming)**
The notebook consumer.ipynb:

- Reads from start_topic and end_topic,

- Merges both streams into a unified DataFrame,

- Groups data into hourly windows and counts trips by (PULocationID, DOLocationID),

- Writes results to HDFS (Parquet) for persistence,

- Performs statistical analysis to detect outlier days using z-scores.

## Results

SQL queries can be executed on live streaming data.

Aggregations provide trip counts by hour and by zone pair.

Daily ride totals are compared against historical weekday averages,
allowing identification of abnormal traffic days (e.g., holidays or city events).

## Technologies user
- Google Cloud Platform (GCP)

- Terraform – infrastructure provisioning

- Ansible – cluster configuration

- Apache Kafka – distributed messaging

- Apache Spark Structured Streaming – real-time analytics

- HDFS / Parquet – data storage

- Python – (pandas, pyarrow, numpy, pyspark, kafka-python)
