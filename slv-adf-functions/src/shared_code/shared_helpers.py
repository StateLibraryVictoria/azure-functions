import asyncio
import csv
import logging
import os

import aiohttp
import psycopg2


def query_database(sql_statement, return_data=False):
    """helper function to run any valid SQL statement against the DB

    Args:
        sql_statement (string): SQL statement
        return_data (bool, optional): If set to true will return the data returned by the SQL query. Defaults to False.

    Returns:
        bool: Will return True/False flag to indicate that the SQL statement was successfully run
        list: Data returned from the database
    """
    host = os.environ.get("DB_HOST")
    dbname = os.environ.get("DB_NAME")
    user = os.environ.get("DB_USER")
    password = os.environ.get("DB_PASSWORD")
    try:
        data_to_return = True
        conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
        cur = conn.cursor()
        cur.execute(sql_statement)
        # * Not every call to the DB will require data to be returned by the function, hence the return_data flag
        if return_data:
            data_to_return = cur.fetchall()
        conn.commit()
        cur.close()
        conn.close()
        return data_to_return

    except Exception as e:
        logging.error(
            f"Could not complete sql query. Here is the exception returned: {e}"
        )
        return False


def export_to_csv(filename, data_to_write, column_names):
    """Helper function to write any list to a CSV file

    Args:
        filename (string): The filename (without .csv file extension) to export the data to
        data_to_write (list): Data to add to the csv file, each item will be added to a new line
        column_names (list): Column names to add to the first line of the csv file
    """

    f = open(f"{filename}.csv", "a+", newline="")

    with f:
        write = csv.writer(f)
        write.writerow(column_names)
        write.writerows(data_to_write)


def get_tasks(session, endpoints, access_token):
    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}
    tasks = []
    for endpoint in endpoints:
        tasks.append(asyncio.create_task(session.post(endpoint, headers=headers)))
    asyncio.sleep(2)
    return tasks


async def get_endpoints(endpoints, access_token):
    results = []
    connector = aiohttp.TCPConnector(limit_per_host=1)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = get_tasks(session, endpoints, access_token)
        responses = await asyncio.gather(*tasks)
        for response in responses:
            results.append(await response.json())
    return results


def async_call_endpoints(endpoints, access_token):

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    data = asyncio.run(get_endpoints(endpoints, access_token))

    return data
