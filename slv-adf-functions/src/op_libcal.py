import os
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
import requests
from shared_azure import get_most_recent_date_in_db
from shared_constants import API_FIELDS


load_dotenv()
libcal_url = os.environ.get('LIBCAL_URL')
libcal_client_secret = os.environ.get('LIBCAL_CLIENT_SECRET')
libcal_client_id = os.environ.get('LIBCAL_CLIENT_ID')

def get_access_token():
    """Retrieves access token for the LibCal API. The client_id and client_secret values are read from environmental variables

    Returns:
        bool: if the request fails a False flag is returned
        string:  the access token
    """
    payload = {
        "client_id" : libcal_client_id,
        "client_secret" : libcal_client_secret,
        "grant_type" : "client_credentials"
    }

    r = requests.post(f'{libcal_url}oauth/token', json=payload)

    if r.status_code != 200:
        return False
    
    access_token = r.json()['access_token']

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

    headers = {
        "Authorization" : f'Bearer {access_token}'
    }
    
    r = requests.get(f'{libcal_url}{endpoint}', headers=headers)

    if r.status_code != 200:
        print(r.text)
        return False
    
    return r.json()

def get_locations():
    """Retrieves information from the LibCal 'location' API endpoint 

    Returns:
        dict: JSON containing information returned by the endpoint
    """
    locations = get_libcal_information('space/locations')

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
        date_to_retrieve = date.today().strftime('%Y-%m-%d')

    bookings = get_libcal_information(f'space/bookings?date={date_to_retrieve}&days={days}&limit={limit}&page={page}')

    return bookings


# check date of most recent booking, this is to prevent an infinite loop if there's no booking for 'today'
def get_most_recent_booking():
    """Queries the LibCal API for the last date that an entry has been added from 'today' backwards i.e. does not include any dates in the future

    Returns:
        date: First date from today backwards that return a non empty list from the LibCal API
    """
    most_recent_booking = date.today()
    most_recent_bookings = get_bookings(date_to_retrieve=most_recent_booking,limit=1,days=1)

    while len(most_recent_bookings) == 0:
        most_recent_booking = most_recent_booking - timedelta(days=1)
        most_recent_bookings = get_bookings(date=most_recent_booking,limit=1,days=1)

    return most_recent_booking

def format_booking_data(booking):

    formatted_booking_info = [booking.get(field,'') for field in API_FIELDS]

    return formatted_booking_info

def get_booking_data_to_upload(environment):
    """Polls the LibCal recursively from the last date recorded in the DB (or the default value if not present) and builds a list of lists containing the data to upload to the DB

    Returns:
        bool: False flag returned if the process doesn't complete
        list: List of nested lists containing metadata extracted from the LibCal API 
    """
    print(f'Retrieving LibCal data for {environment} environment')
    # Calculate no. of days since last update. If it's less than the APIs max days (365) add to the query param
    last_date_retrieved = get_most_recent_date_in_db(environment,prepend='stg')
    if not last_date_retrieved:
        print('Unable to retrieve most recent date from database')
        return False

    print(f'Last date retrieved: {last_date_retrieved}')

    date_to_check = get_most_recent_booking()
    returned_values_upload_list = []
    try:
        # days_since_last_update = 1
        days_since_last_update = date_to_check - last_date_retrieved
        days_since_last_update = int(days_since_last_update.days)
        while days_since_last_update > 0:
            days_since_last_update = date_to_check - last_date_retrieved
            days_since_last_update = int(days_since_last_update.days)
            days = min(days_since_last_update,365)

            # Query bookings API from most recent date added recursively using page param until len of returned values is less than limit
            #* Do not include any bookings after 'today'
            page_counter = 1
            bookings_info = get_bookings(date_to_retrieve=last_date_retrieved,days=days, page=page_counter)

            values_for_upload = [format_booking_data(booking) for booking in bookings_info]
            returned_values_upload_list.extend(values_for_upload)

            while len(bookings_info) > 0:
                page_counter += 1
                bookings_info = get_bookings(date_to_retrieve=last_date_retrieved,days=days, page=page_counter)
                values_for_upload = [format_booking_data(booking) for booking in bookings_info]
                returned_values_upload_list.extend(values_for_upload)

            #* datetime.strptime(element[5],'%Y-%m-%dT%H:%M:%S%z').date() is a complicated way of converting the string returned by the API into a date format
            last_date_retrieved = max([datetime.strptime(element[5],'%Y-%m-%dT%H:%M:%S%z').date() for element in returned_values_upload_list])
            print(f'Data retrieved up to: {last_date_retrieved}')
    
    except Exception as e:
        print(f"The following error occurred: {e}. Process aborted")
        return False
    
    print('Completed LibCal data extraction')
    return returned_values_upload_list