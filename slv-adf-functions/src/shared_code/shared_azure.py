from datetime import datetime
import os
import logging

from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import pyodbc

from . import shared_constants


def get_key_vault_secret(secret_to_retrieve, vault_url):
    azure_client_id = os.environ.get('AZURE_CLIENT_ID')
    azure_client_secret = os.environ.get('AZURE_CLIENT_SECRET')
    azure_tenant_id = os.environ.get('AZURE_TENANT_ID')

    credentials = ClientSecretCredential(client_id=azure_client_id, client_secret=azure_client_secret,tenant_id=azure_tenant_id)
    client = SecretClient(credential=credentials, vault_url=vault_url)
    sql_connection_string = client.get_secret(secret_to_retrieve)


    if not sql_connection_string.value:
        logging.warning('Unable to retrieve key vault secret')
        return False

    logging.info(f'Retrieved secret: {sql_connection_string.value}')
    return sql_connection_string.value

def check_if_table_exists(environment,prefix=False):

    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f'{prefix}_{table_name}'
    
    logging.info(f'Checking if table: {table_name} already exists in {environment} database')

    sql = f"""
        SELECT *
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'dbo'
        AND TABLE_NAME = '{table_name}';
    """
    res = query_azure_database(sql, environment, return_data=True)

    if len(res) == 0:
        logging.info(f'{table_name} does not exist')
        return False

    logging.info(f'{table_name} does exist')
    return True

def query_azure_database(sql_statement,environment='dev',return_data=False):

    username = os.environ.get('SQL_ADMIN_USER')
    password = os.environ.get('SQL_ADMIN_PASSWORD')
    
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
        logging.error(f'Could not complete sql query. Here is the exception returned: {e}')
        
        return False

def create_azure_sql_table(environment, prefix=False ):
    
    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f'{prefix}_{table_name}'
    logging.info(f'Created table "{table_name}" in {environment} database')

    db_columns = [f'[{field}] [nvarchar](200) NULL' for field in shared_constants.API_FIELDS]
    columns_string = ','.join(db_columns)
    
    sql = f"""
        CREATE TABLE [dbo].[{table_name}] (
            {columns_string}
        )
    """
    return query_azure_database(sql,environment)


def get_most_recent_date_in_db(environment, prefix=False):

    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f'{prefix}_{shared_constants.DB_TABLE_NAME}'

    sql_statement = f"""
        SELECT TOP (1) [fromDate]
        FROM [dbo].[{table_name}]
        ORDER BY [fromDate] DESC
    """
    top_date_in_db = query_azure_database(sql_statement, environment=environment, return_data=True)

    if not top_date_in_db:
        return datetime.strptime(shared_constants.EARLIEST_DATE,'%Y-%m-%d').date()

    return datetime.strptime(top_date_in_db[0][0],'%Y-%m-%dT%H:%M:%S%z').date()


def bulk_upload_azure_database(libcal_data,environment='dev',prefix=False):

    table_name = shared_constants.DB_TABLE_NAME
    if prefix:
        table_name = f'{prefix}_{table_name}'
    
    logging.info(f'{len(libcal_data)} rows to be added to {table_name} in {environment} database')

    columns = ', '.join(shared_constants.API_FIELDS)
    placeholders = '?, ' * len(shared_constants.API_FIELDS)
    placeholders = placeholders[:-2]
    
    # sql = f'INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})'
    # username = os.environ.get('SQL_ADMIN_USER')
    # password = os.environ.get('SQL_ADMIN_PASSWORD')
    # connection_string = f"Driver={{ODBC Driver 17 for SQL Server}};Server=tcp:slv-{environment}-sqldw.database.windows.net,1433;Database={environment}-edw;Uid={username};Pwd={{{password}}};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    # try:
    #     con = pyodbc.connect(connection_string)
    #     cursor = con.cursor()
    #     cursor.executemany(sql,libcal_data)
    #     con.commit()
    #     con.close()
    #     logging.info(f'Success: {len(libcal_data)} rows added to {table_name}')
    #     return True
    # except Exception as e:
    #     logging.error(f'Could not complete sql query. Here is the exception returned: {e}')
    #     return False
    return True

