# Create a Data Pipeline Using Kafka
## Overview
**Project Goal**: The goal of this project is to create a data tunnel to maintain a sync between tables in source and destination databases. Any changes on the source table will be reflected in destination table less than 1 sec.

This project uses **PostgreSQL** as source and destination databases and **Apache Kafka** as the message queue to capture all the changes. Additionally, we will use **Apache Airflow** to schedule the producer, consumer, and all the validation steps.

## Content
The project contains the following:
<pre> <code>
.gitignore             - this will ignore log files and other metadata files
.dockerignore          - this will ignore log files and other metadata files
consumer.py            - produce the message to Apache Kafka
producer.py            - consume the message from Apache Kafka
requirements.txt       - list all the required packages

dags/                         - DAG definitions package
│── validation_workflow.py    - entry point for data validation
</code> </pre>

## Environment Setup
### Build the Docker Image
```
docker-compose build
```
### Build the Docker Container
```
docker-compose up -d
```
You can check the status of all the services by:
```
docker ps
```
### Log in to Apache Airflow UI
Wait until **airflow** service is running. The service will start and be accessible at `http://localhost:8080/login`

### Activate the DAG and Trigger
![trigger-airflow](screenshots/trigger-airflow.png)
![airflow-done](screenshots/airflow-done.png)
### Examine the Result
* Check the **employee_a** table in source database:

![source-table](screenshots/source-table.png)

---
* Check the **emp_cdc** table in source database:

![cdc-table](screenshots/cdc-table.png)

---
* Check the **employee_b** table in destination database:

![destination-table](screenshots/destination-table.png)


