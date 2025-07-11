# Create a Data Pipeline Using Kafka
### Overview
**Project Goal**: The goal of this project is to create a data tunnel to maintain a sync between tables in source and destination databases. Any changes on the source table will be reflected in destination table less than 1 sec.

This project uses **PostgreSQL** as source and destination databases and **Apache Kafka** as the message queue to capture all the changes. Additionally, we will use **Apache Airflow** to schedule the producer, consumer, and all the validation steps.

### Content
The project contains the following:

