from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 7, 10),
}

with DAG(
    dag_id='validation_workflow',
    default_args=default_args,
    schedule_interval=None,       # manual trigger only
    catchup=True,
    tags=['cdc', 'validation']
) as dag:

    # 1) Clean up source DB
    cleanup_source = PostgresOperator(
        task_id='cleanup_source',
        postgres_conn_id='source_db',
        sql="""
            DROP TABLE IF EXISTS employee_a, emp_cdc;
        """
    )

    # 2) Create employee_a + emp_cdc
    create_source_tables = PostgresOperator(
        task_id='create_source_tables',
        postgres_conn_id='source_db',
        sql="""
            CREATE TABLE employee_a(
                emp_id        INTEGER     NOT NULL PRIMARY KEY,
                first_name    VARCHAR(100),
                last_name     VARCHAR(100),
                date_of_birth DATE,
                city          VARCHAR(100)
            );

            CREATE TABLE emp_cdc(
                action_id     SERIAL      PRIMARY KEY,
                emp_id        INTEGER     NOT NULL,
                first_name    VARCHAR(100),
                last_name     VARCHAR(100),
                date_of_birth DATE,
                city          VARCHAR(100),
                action        VARCHAR(100)
            );
        """
    )

    # 3) Clean up existing trigger & function
    cleanup_trigger = PostgresOperator(
        task_id='cleanup_trigger',
        postgres_conn_id='source_db',
        sql="""
            DROP TRIGGER IF EXISTS emp_trigger ON employee_a;
            DROP FUNCTION IF EXISTS trigger_emp_cdc();
        """
    )

    # 4) Create trigger function + BEFORE trigger
    create_trigger = PostgresOperator(
        task_id='create_trigger',
        postgres_conn_id='source_db',
        sql="""
        CREATE OR REPLACE FUNCTION trigger_emp_cdc()
          RETURNS TRIGGER
          LANGUAGE plpgsql
        AS $$
        DECLARE
          birth_year INT := EXTRACT(YEAR FROM NEW.date_of_birth);
        BEGIN
          -- Extract year, if present
          birth_year := EXTRACT(YEAR FROM COALESCE(NEW.date_of_birth, OLD.date_of_birth));

          IF TG_OP = 'INSERT' THEN
            -- Rule 1: emp_id must be positive
            IF NEW.emp_id < 0 THEN
              INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
              VALUES (NEW.emp_id, NEW.first_name, NEW.last_name, NEW.date_of_birth, NEW.city, 'INSERT');
              RETURN NULL;  -- skip inserting into employee_a

            -- Rule 2: must be at least 18 years old
            ELSIF birth_year >= 2007 THEN
              INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
              VALUES (NEW.emp_id, NEW.first_name, NEW.last_name, NEW.date_of_birth, NEW.city, 'INSERT');
              RETURN NULL;  -- skip inserting into employee_a

            -- Otherwise: valid insert
            ELSE
              INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
              VALUES (NEW.emp_id, NEW.first_name, NEW.last_name, NEW.date_of_birth, NEW.city, 'INSERT');
              RETURN NEW;   -- proceed with inserting into employee_a
            
            END IF;

        ELSIF TG_OP = 'UPDATE' THEN
            -- Rule 1: emp_id must be positive
            IF NEW.emp_id < 0 THEN
              INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
              VALUES (NEW.emp_id, NEW.first_name, NEW.last_name, NEW.date_of_birth, NEW.city, 'UPDATE');
              RETURN NULL;

            -- Rule 2: must be at least 18 years old
            ELSIF birth_year >= 2007 THEN
              INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
              VALUES (NEW.emp_id, NEW.first_name, NEW.last_name, NEW.date_of_birth, NEW.city, 'UPDATE');
              RETURN NULL;  -- skip inserting into employee_a

            -- Otherwise: valid insert
            ELSE
              INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
              VALUES (NEW.emp_id, NEW.first_name, NEW.last_name, NEW.date_of_birth, NEW.city, 'UPDATE');
              RETURN NEW;   -- proceed with inserting into employee_a
            
            END IF;

        ELSIF TG_OP = 'DELETE' THEN
            INSERT INTO emp_cdc (emp_id, first_name, last_name, date_of_birth, city, action)
            VALUES (OLD.emp_id, OLD.first_name, OLD.last_name, OLD.date_of_birth, OLD.city, 'DELETE');
            RETURN OLD;
        
        END IF;

        RETURN NULL;
        END;
        $$;

        CREATE TRIGGER emp_trigger
          BEFORE INSERT OR UPDATE OR DELETE
          ON employee_a
          FOR EACH ROW
          EXECUTE FUNCTION trigger_emp_cdc();
        """
    )

    # 5) Clean up destination DB
    cleanup_dest = PostgresOperator(
        task_id='cleanup_dest',
        postgres_conn_id='dest_db',
        sql="DROP TABLE IF EXISTS employee_b;"
    )

    # 6) Create employee_b
    create_dest = PostgresOperator(
        task_id='create_dest',
        postgres_conn_id='dest_db',
        sql="""
            CREATE TABLE employee_b(
                emp_id        INTEGER     NOT NULL PRIMARY KEY,
                first_name    VARCHAR(100),
                last_name     VARCHAR(100),
                date_of_birth DATE,
                city          VARCHAR(100)
            );
        """
    )

    # 8) Fire off all your DML in one shot
    execute_dml = PostgresOperator(
        task_id='execute_dml',
        postgres_conn_id='source_db',
        sql="""
            INSERT INTO employee_a(emp_id, first_name, last_name, date_of_birth, city)
            VALUES
              (1, 'Max', 'Smith',   '2002-02-03', 'Sydney'),
              (2, 'Karl', 'Summers','2004-04-10', 'Brisbane'),
              (3, 'Sam', 'Wilde',   '2005-02-06', 'Perth'),
              (-2,'Mr.','Impossible','2000-01-03','Reykjavík'),
              (4, 'Wayne','Bruce',  '1997-03-12', 'Barcelona');

            UPDATE employee_a
               SET first_name='Bruce', last_name='Wayne'
             WHERE emp_id=4;

            UPDATE employee_a
               SET date_of_birth='2010-02-07', city='Paris'
             WHERE emp_id=3;

            UPDATE employee_a
               SET date_of_birth='1997-02-07'
             WHERE emp_id=3;

            DELETE FROM employee_a WHERE emp_id IN (1,2);
        """
    )

    # ─── define task ordering ───
    cleanup_source \
      >> create_source_tables \
      >> cleanup_trigger \
      >> create_trigger \
      >> cleanup_dest \
      >> create_dest \
      >> execute_dml
