import logging
import os
from datetime import datetime

import pyodbc
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

from . import shared_constants


def get_key_vault_secret(secret_to_retrieve, vault_url):
    """Retrieves a secret from Azure Key Vault

    Args:
        secret_to_retrieve (str): Name of the key to retrieve (must match exactly the name in hte Azure key vault)
        vault_url (str): URL for the vault

    Returns:
        bool: False flag returned to indicate that the function failed
        str: The key vault secret value
    """
    azure_client_id = os.environ.get("AZURE_CLIENT_ID")
    azure_client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    azure_tenant_id = os.environ.get("AZURE_TENANT_ID")

    credentials = ClientSecretCredential(
        client_id=azure_client_id,
        client_secret=azure_client_secret,
        tenant_id=azure_tenant_id,
    )
    client = SecretClient(credential=credentials, vault_url=vault_url)
    key_vault_secret = client.get_secret(secret_to_retrieve)

    if not key_vault_secret.value:
        logging.warning("Unable to retrieve key vault secret")
        return False

    return key_vault_secret.value


def check_if_table_exists(environment, prefix=False):
    """Checks if a database table exists

    Args:
        environment (str): Staging environment (Valid values dev, test or prod)
        prefix (bool, optional): Prefix for the database table name to check. Default is false

    Returns:
        bool: Flag to indicate success of the function
    """
    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f"{prefix}_{table_name}"

    logging.info(
        f"Checking if table: {table_name} already exists in {environment} database"
    )

    sql = f"""
        SELECT *
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo'
        AND TABLE_NAME = '{table_name}';
    """
    res = query_azure_database(sql, environment, return_data=True)

    if len(res) == 0:
        logging.info(f"{table_name} does not exist")
        return False

    logging.info(f"{table_name} does exist")
    return True


def query_azure_database(sql_statement, environment, return_data=False):
    """Queries Azure SQL database

    Args:
        sql_statement (str): SQL query to run against the databse
        environment (str): Staging environment (Valid values dev, test or prod).
        return_data (bool, optional): Flag to indicate whether to return the result of the successful SQL query. Defaults to False.

    Returns:
        bool: Flag to indicate success of the function
        list: Data returned by the SQL query
    """
    username = os.environ.get("SQL_ADMIN_USER")
    password = os.environ.get("SQL_ADMIN_PASSWORD")

    connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:slv-{environment}-sqldw.database.windows.net,1433;Database={environment}-edw;Uid={username};Pwd={{{password}}};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

    try:
        data_to_return = True
        con = pyodbc.connect(connection_string)
        cursor = con.cursor()
        cursor.execute(sql_statement)
        if return_data:
            data_to_return = cursor.fetchall()
        con.commit()
        con.close()

        return data_to_return
    except Exception as e:
        logging.error(
            f"Could not complete sql query. Here is the exception returned: {e}"
        )

        return False


def create_azure_sql_table(environment, prefix=False):

    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f"{prefix}_{table_name}"
    logging.info(f'Created table "{table_name}" in {environment} database')

    db_columns = [
        f"[{field}] [nvarchar](200) NULL" for field in shared_constants.API_FIELDS
    ]
    columns_string = ",".join(db_columns)

    sql = f"""
        CREATE TABLE [dbo].[{table_name}] (
            {columns_string}
        )
    """
    return query_azure_database(sql, environment)


def get_most_recent_date_in_db(environment, prefix=False):
    """Retrieves the most recent date recorded in the database

    Args:
        environment (str): Staging environment (Valid values dev, test or prod)
        prefix (bool, optional): Prefix for the database table name to check. Default is false

    Returns:
        bool: False flag to indicate an error occurred
        date: Most recent date in the database
    """
    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f"{prefix}_{shared_constants.DB_TABLE_NAME}"

    sql_statement = f"""
        SELECT TOP (1) [fromDate]
        FROM [dbo].[{table_name}]
        ORDER BY [fromDate] DESC
    """
    top_date_in_db = query_azure_database(
        sql_statement, environment=environment, return_data=True
    )

    if not top_date_in_db:
        logging.error(f"Could not retrieve the most recent date from {table_name}")
        logging.info(f"Reverting to default date {shared_constants.EARLIEST_DATE}")
        return datetime.strptime(shared_constants.EARLIEST_DATE, "%Y-%m-%d").date()

    return datetime.strptime(top_date_in_db[0][0], "%Y-%m-%dT%H:%M:%S%z").date()


def bulk_upload_azure_database(data_for_upload, environment, prefix=False):
    """Upload list of lists to Azure SQL database

    Args:
        data_for_upload (list): formatted list of data for upload to Azure
        environment (str): Staging environment (Valid values dev, test or prod)
        prefix (bool, optional): Prefix for the database table name to check. Default is false

    Returns:
        bool: Flag to indicate success of the function
    """
    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f"{prefix}_{table_name}"

    logging.info(
        f"{len(data_for_upload)} rows to be added to {table_name} in {environment} database"
    )

    columns = ", ".join(shared_constants.API_FIELDS)
    placeholders = "?, " * len(shared_constants.API_FIELDS)
    placeholders = placeholders[:-2]

    sql = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
    username = os.environ.get("SQL_ADMIN_USER")
    password = os.environ.get("SQL_ADMIN_PASSWORD")
    connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:slv-{environment}-sqldw.database.windows.net,1433;Database={environment}-edw;Uid={username};Pwd={{{password}}};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    try:
        con = pyodbc.connect(connection_string)
        cursor = con.cursor()
        cursor.executemany(sql, data_for_upload)
        con.commit()
        con.close()
        logging.info(f"Success: {len(data_for_upload)} rows added to {table_name}")
        return True
    except Exception as e:
        logging.error(
            f"Could not complete sql query. Here is the exception returned: {e}"
        )
        return False
