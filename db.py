import psycopg2
from enum import Enum
import os


class TaskStatus(Enum):
    PENDING = 0, 'Pending'
    SUCCESS = 1, 'Success'
    ERROR = 2, 'Error'


def change_task_status(task_id, new_status=TaskStatus.SUCCESS.value[0], error_message=''):
    # Establish a connection to the database
    conn = psycopg2.connect(database=os.getenv('DB_DATABASE'), user=os.getenv('DB_USER'),
                            password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT', '5432'))

    # Open a cursor to perform database operations
    cur = conn.cursor()

    table = 'prompts_task'
    cur.execute(
        f"UPDATE {table} SET status='{new_status}', error_message='{error_message}' WHERE id='{task_id}'")

    # Commit the changes to the database
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()
