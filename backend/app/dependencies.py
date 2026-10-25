import sqlite3
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends

from app.database import connect_database, create_tables


def database_connection() -> Generator[sqlite3.Connection, None, None]:
    connection = connect_database()
    create_tables(connection)
    try:
        yield connection
    finally:
        connection.close()


DatabaseConnection = Annotated[sqlite3.Connection, Depends(database_connection)]
