import psycopg2
from enum import Enum
import os
import json


class TaskStatus(Enum):
    PENDING = 0, 'Pending'
    SUCCESS = 1, 'Success'
    ERROR = 2, 'Error'

DB_CREDENTIALS = json.loads(os.getenv('DB_CREDENTIALS'))
DATABASE_DEFAULT = {
    'ENGINE': DB_CREDENTIALS.get('DB_ENGINE', 'django.db.backends.postgresql'),
    'NAME': DB_CREDENTIALS.get('DB_DATABASE'),
    'USER': DB_CREDENTIALS.get('DB_USER'),
    'PASSWORD': DB_CREDENTIALS.get('DB_PASSWORD'),
    'PORT': DB_CREDENTIALS.get('DB_PORT', '5432'),
    'HOST': DB_CREDENTIALS.get('DB_HOST')
}


def change_task_status(task_id, new_status=TaskStatus.SUCCESS.value[0], error_message=''):
    # Establish a connection to the database
    conn = psycopg2.connect(
        database=DATABASE_DEFAULT['NAME'],
        user=DATABASE_DEFAULT['USER'],
        password=DATABASE_DEFAULT['PASSWORD'],
        host=DATABASE_DEFAULT['HOST'],
        port=DATABASE_DEFAULT['PORT']
    )

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
