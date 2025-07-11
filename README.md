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
![image](https://private-user-images.githubusercontent.com/88637946/465379901-dc1fd671-e69e-4d5a-975b-00ab9fe1effc.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTIyNTM1MTEsIm5iZiI6MTc1MjI1MzIxMSwicGF0aCI6Ii84ODYzNzk0Ni80NjUzNzk5MDEtZGMxZmQ2NzEtZTY5ZS00ZDVhLTk3NWItMDBhYjlmZTFlZmZjLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTElMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzExVDE3MDAxMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTUwMTQxY2JhOWRiYTZiMjcwZGY0ZDNiYjFhMmZmMzUxNjgzOGY4ZTJkYzBkYjY0NDc1YTY3MmMzZmJiZjVjNmImWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.2tdXwuQNuJKfgF6Z7qEcXp3KDMyqRHpYj2nv3AhB-DE)
![image](https://private-user-images.githubusercontent.com/88637946/465380825-5e68788c-7017-45ab-95da-660392c75528.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTIyNTM3NzEsIm5iZiI6MTc1MjI1MzQ3MSwicGF0aCI6Ii84ODYzNzk0Ni80NjUzODA4MjUtNWU2ODc4OGMtNzAxNy00NWFiLTk1ZGEtNjYwMzkyYzc1NTI4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTElMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzExVDE3MDQzMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWQ4MjFjMTVjZTQ0OTk4ODUyNDllMWQxODRiNDVkZjgxOTE2NDBmYzg3YWY4YjMxMzE1YzJlNjZlYjk1ZTFjMmMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.KzNA_dCceF4SU7cbTDYLwcd92XMYlpSn1dIbyNl1cp0)
### Examine the Result
* Check the **employee_a** table in source database:

![image](https://private-user-images.githubusercontent.com/88637946/465380899-46f21adb-77fe-4e47-a896-6f5cd81f0e93.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTIyNTM4MDQsIm5iZiI6MTc1MjI1MzUwNCwicGF0aCI6Ii84ODYzNzk0Ni80NjUzODA4OTktNDZmMjFhZGItNzdmZS00ZTQ3LWE4OTYtNmY1Y2Q4MWYwZTkzLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTElMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzExVDE3MDUwNFomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWM5Mzc1MDMyNmM1NzYzOGUwOWQyMzg2NjAyZjIyOTA3YzdhNTlmYjM3NWJiMDVkNjY0MzZiNThiY2Y5NGUxZTgmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.sEGT7o_ufbSsN5ZLgwUJrtIZ3Yi164T2BrETMidDOnU)

---
* Check the **emp_cdc** table in source database:

![image](https://private-user-images.githubusercontent.com/88637946/465380988-2ad4eb82-941a-45c9-b076-cf5ec24236a8.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTIyNTM4MjEsIm5iZiI6MTc1MjI1MzUyMSwicGF0aCI6Ii84ODYzNzk0Ni80NjUzODA5ODgtMmFkNGViODItOTQxYS00NWM5LWIwNzYtY2Y1ZWMyNDIzNmE4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTElMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzExVDE3MDUyMVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTg3NmVjOTQ4NWZkZWMzMWY3YWZmNjVkZTgxYmEyYzMxMGM2ZThkZTQ0N2NmMGJmZjNmN2QwNmIwZmZkMDAwYWMmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.-XmYh0aUc4fVcRzVIdCLooEkINhmVbojkvoVNpWJ5_4)

---
* Check the **employee_b** table in destination database:

![image](https://private-user-images.githubusercontent.com/88637946/465381062-11e9ca73-3935-494b-b71c-0bc128d8593f.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NTIyNTM4NDYsIm5iZiI6MTc1MjI1MzU0NiwicGF0aCI6Ii84ODYzNzk0Ni80NjUzODEwNjItMTFlOWNhNzMtMzkzNS00OTRiLWI3MWMtMGJjMTI4ZDg1OTNmLnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNTA3MTElMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjUwNzExVDE3MDU0NlomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPWUxM2U1OTY3MjEwOGI0N2YyMDA1NTJiMjViZDRlNDM4ZjUzYWYyN2Q4MmUyZDRmZmEzNzkxNGE1MGNkYjBjMjUmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0In0.plIXHKkTX-Nr_p1zJeeUd3fD7WLnd0H-adcrselvvjs)


