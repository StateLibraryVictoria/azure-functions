import logging
import os
from datetime import date, datetime, timedelta

import requests

from . import op_libcal, shared_azure, shared_constants

libcal_url = os.environ.get("LIBCAL_URL")
libcal_client_secret = os.environ.get("LIBCAL_CLIENT_SECRET")
libcal_client_id = os.environ.get("LIBCAL_CLIENT_ID")


def get_access_token():
    """Retrieves access token for the LibCal API. The client_id and client_secret values are read from environmental variables

    Returns:
        bool: if the request fails a False flag is returned
        string:  the access token
    """
    payload = {
        "client_id": libcal_client_id,
        "client_secret": libcal_client_secret,
        "grant_type": "client_credentials",
    }

    r = requests.post(f"{libcal_url}oauth/token", json=payload)

    if r.status_code != 200:
        return False

    access_token = r.json()["access_token"]

    return access_token


def get_libcal_information(endpoint):
    """Retrieves information from one of the LibCal API endpoints, will only work for endpoints using the 'get' protocol

    Args:
        endpoint (string): the LibCal API endpoint to be requested

    Returns:
        bool: if the request fails a False flag is returned
        dict: The json returned by the API call, if the status code returned is 200
    """

    access_token = get_access_token()

    if not access_token:
        return False

    headers = {"Authorization": f"Bearer {access_token}"}

    r = requests.get(f"{libcal_url}{endpoint}", headers=headers)

    if r.status_code != 200:
        logging.error(r.text)
        return False

    return r.json()


def get_locations():
    """Retrieves information from the LibCal 'location' API endpoint

    Returns:
        dict: JSON containing information returned by the endpoint
    """
    locations = get_libcal_information("space/locations")

    return locations


def get_bookings(date_to_retrieve=False, days=365, page=1, limit=500):
    """Retrieves booking information from the LibCal API

    Args:
        date_to_retrieve (bool, optional): The date from which to retrieve bookings information. Defaults to False, which triggers a call to date.today()
        days (int, optional): How many days to include in the API request, max is 365. Defaults to 365.
        page (int, optional): Which page of results to return. Defaults to 1.
        limit (int, optional): How many results to include in the info returned (max 500). Defaults to 500.

    Returns:
        list: list of dicts containing booking information
    """
    if not date_to_retrieve:
        date_to_retrieve = date.today().strftime("%Y-%m-%d")

    bookings = get_libcal_information(
        f"space/bookings?date={date_to_retrieve}&days={days}&limit={limit}&page={page}"
    )

    return bookings


# check date of most recent booking, this is to prevent an infinite loop if there's no booking for 'today'
def get_most_recent_booking():
    """Queries the LibCal API for the last date that an entry has been added from 'today' backwards i.e. does not include any dates in the future

    Returns:
        date: First date from today backwards that return a non empty list from the LibCal API
    """
    most_recent_booking = date.today()
    most_recent_bookings = get_bookings(
        date_to_retrieve=most_recent_booking, limit=1, days=1
    )

    while len(most_recent_bookings) == 0:
        most_recent_booking = most_recent_booking - timedelta(days=1)
        most_recent_bookings = get_bookings(date=most_recent_booking, limit=1, days=1)

    return most_recent_booking


def get_users():

    users = get_libcal_information("appointments/bookings")

    return users


def format_booking_data(booking):
    """Re-formats a booking by pulling out the fields supplied in the API FIELDS list

    Args:
        booking (dict): An entry returned by the Libcal API

    Returns:
        list: List of values filtered from the booking argument supplied
    """
    formatted_booking_info = [
        booking.get(field, "") for field in shared_constants.API_FIELDS["libcal"]
    ]

    return formatted_booking_info


def get_booking_data_to_upload(environment, last_date_retrieved):
    """Polls the LibCal API recursively from the last date recorded in the DB (or the default value if not present) and builds a list of lists containing the data to upload to the DB

    Args:
        environment (str): Staging environment (Valid values dev, test or prod)
        last_date_retrieved (datetime): Last date recorded in DB, or default value if none recorded in DB

    Returns:
        bool: False flag returned if the process doesn't complete
        list: List of nested lists containing metadata extracted from the LibCal API
    """
    logging.info(f"Retrieving LibCal data for {environment} environment")
    # Calculate no. of days since last update. If it's less than the APIs max days (365) add to the query param
    date_to_check = get_most_recent_booking()
    returned_values_upload_list = []
    try:
        days_since_last_update = date_to_check - last_date_retrieved
        days_since_last_update = int(days_since_last_update.days)
        while days_since_last_update > 0:
            days_since_last_update = date_to_check - last_date_retrieved
            days_since_last_update = int(days_since_last_update.days)
            days = min(days_since_last_update, 365)

            # Query bookings API from most recent date added recursively using page param until len of returned values is less than limit
            # * Do not include any bookings after 'today'
            page_counter = 1
            bookings_info = get_bookings(
                date_to_retrieve=last_date_retrieved, days=days, page=page_counter
            )

            values_for_upload = [
                format_booking_data(booking) for booking in bookings_info
            ]
            returned_values_upload_list.extend(values_for_upload)

            while len(bookings_info) > 0:
                page_counter += 1
                bookings_info = get_bookings(
                    date_to_retrieve=last_date_retrieved, days=days, page=page_counter
                )
                values_for_upload = [
                    format_booking_data(booking) for booking in bookings_info
                ]
                returned_values_upload_list.extend(values_for_upload)

            # * datetime.strptime(element[5],'%Y-%m-%dT%H:%M:%S%z').date() is a complicated way of converting the string returned by the API into a date format
            last_date_retrieved = max(
                [
                    datetime.strptime(element[6], "%Y-%m-%dT%H:%M:%S%z").date()
                    for element in returned_values_upload_list
                ]
            )
            logging.info(f"Data retrieved up to: {last_date_retrieved}")

    except Exception as e:
        logging.error(f"The following error occurred: {e}. Process aborted")
        return False

    logging.info("Completed LibCal data extraction")
    return returned_values_upload_list


def upload_libcal_data_to_azure():
    """Coordinates the retrieval of data from Libcal and subsequent upload to Azure SQL database

    Returns:
        bool: Returns True/False to indicate success of the operation
    """
    environment = os.environ.get("ENVIRONMENT")
    prefix = "stg"
    operation = "libcal"

    table_exists = shared_azure.check_if_table_exists(environment, operation, prefix)

    if not table_exists:
        shared_azure.create_azure_sql_table(environment, operation, prefix)
        last_date_retrieved = datetime.strptime(
            shared_constants.EARLIEST_DATE, "%Y-%m-%d"
        ).date()
    else:
        last_date_retrieved = shared_azure.get_most_recent_date_in_db(
            environment, operation, "fromDate", prefix="stg"
        )
        last_date_retrieved = datetime.strptime(
            last_date_retrieved, "%Y-%m-%dT%H:%M:%S%z"
        ).date()

    logging.info(f"Last date retrieved: {last_date_retrieved}")

    libcal_data_for_upload = op_libcal.get_booking_data_to_upload(
        environment, last_date_retrieved
    )
    if libcal_data_for_upload == False:
        logging.error("There was a problem retrieving data from LibCal")
        return False

    if len(libcal_data_for_upload) == 0:
        logging.warning("No new data to extract from LibCal")
        return False

    logging.info(f"{len(libcal_data_for_upload)} rows extracted from LibCal")

    upload_complete = shared_azure.bulk_upload_azure_database(
        libcal_data_for_upload, environment, "libcal", prefix
    )

    return upload_complete


def upload_libcal_data_to_azure(last_date_retrieved):
    """Coordinates the retrieval of data from Libcal and subsequent upload to Azure SQL database

    Returns:
        bool: Returns True/False to indicate success of the operation
    """
    environment = os.environ.get("ENVIRONMENT")
    prefix = "stg"

    table_exists = shared_azure.check_if_table_exists(environment, prefix)

    if not table_exists:
        shared_azure.create_azure_sql_table(environment, prefix)

    logging.info(f"Last date retrieved: {last_date_retrieved}")

    last_date_retrieved = datetime.strptime(last_date_retrieved, "%Y-%m-%d").date()

    libcal_data_for_upload = op_libcal.get_booking_data_to_upload(
        environment, last_date_retrieved
    )
    if libcal_data_for_upload == False:
        logging.error("There was a problem retrieving data from LibCal")
        return False

    if len(libcal_data_for_upload) == 0:
        logging.warning("No new data to extract from LibCal")
        return False

    logging.info(f"{len(libcal_data_for_upload)} rows extracted from LibCal")

    upload_complete = shared_azure.bulk_upload_azure_database(
        libcal_data_for_upload, environment, prefix
    )

    return upload_complete
