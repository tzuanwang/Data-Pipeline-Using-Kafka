# Create a Data Pipeline Using Kafka
## Capture the changing data
* Create a data tunnel to maintain a sync between tables in source and destination databases
* The stream processing would be responsible for:
    * Snapshot processing => Reading all the records from source database => send them asynchronously to destination databse
    * Stream processing => Once a snapshot has been synchronized, stream processing will keep looking for the new changes
* Insert/Delete/Update => Any changes on source table should be reflected in destination table less than 1 sec
