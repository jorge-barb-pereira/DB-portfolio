"""Explicit configuration and transaction/connection lifetime management."""
from contextlib import contextmanager
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT/'.env')


def connection_settings():
    password = os.environ.get('DB_PASS')
    if not password:
        raise ValueError('Set DB_PASS in the environment or repository .env file')
    return {'host':os.getenv('DB_HOST','127.0.0.1'), 'port':int(os.getenv('DB_PORT','5555')),
            'dbname':os.getenv('DB_NAME','election_portfolio'), 'user':os.getenv('DB_USER','portfolio'),
            'password':password, 'connect_timeout':10}


@contextmanager
def transaction():
    connection = psycopg2.connect(**connection_settings())
    try:
        with connection:
            yield connection
    finally:
        connection.close()
