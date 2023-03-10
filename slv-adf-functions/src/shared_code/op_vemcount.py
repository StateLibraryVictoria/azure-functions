import calendar
import logging
import os
from datetime import date, datetime, timedelta

import requests

from . import shared_azure, shared_constants


def get_access_token():
    """_summary_

    Returns:
        _type_: _description_
    """
    base_url = os.environ.get("VEMCOUNT_URL")
    api_key = os.environ.get("VEMCOUNT_API_KEY")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Api-Key": api_key,
    }

    r = requests.post(f"{base_url}auth/login", headers=headers)

    if r.status_code != 200:
        return False

    access_token = r.json()["access_token"]

    return access_token


def get_vemcount_information(endpoint, access_token, http_method):

    base_url = os.environ.get("VEMCOUNT_URL")

    headers = {"Accept": "application/json", "Authorization": f"Bearer {access_token}"}

    r = requests.request(http_method, f"{base_url}{endpoint}", headers=headers)

    if r.status_code != 200:

        return False

    return r.json()


def get_vemcount_zones(access_token):

    locations = get_vemcount_information("location", access_token, "GET")
    if not locations:
        logging.info("Unable to retrieve location information")
        return False

    list_of_zones = locations["data"][0]["zones"]["data"]
    zone_ids = [zone["id"] for zone in list_of_zones]

    return zone_ids


def get_last_date_in_month(from_date):

    year = from_date.year
    month = from_date.month

    eo_month = calendar.monthrange(year, month)

    return date(year, month, eo_month[1])


def call_all_zones(zone_list, access_token, date_from, date_to):

    data = {}

    for zone in zone_list:
        endpoint = f"report?source=zones&data={str(zone)}&data_output=inside&period_step=30min&form_date_from={date_from}&form_date_to={date_to}"
        zone_info = get_vemcount_information(endpoint, access_token, "post")
        dates_info = zone_info["yesterday"][str(zone)]["dates"]
        data[zone] = dates_info
        print(f"{len(dates_info)} rows retrieved for zone: {zone}")

    return data


def get_zone_info_for_upload(
    zone_list, operation, environment, prefix, last_date_retrieved, access_token
):

    form_date_to = last_date_retrieved + timedelta(days=7)
    form_date_from = last_date_retrieved

    yesterday = date.today() - timedelta(1)
    eo_month_yesterday = yesterday + timedelta(days=7)

    while form_date_to <= eo_month_yesterday:
        data = []
        print(
            f"Retrieving data for {len(zone_list)} zone(s) between {form_date_from} and {form_date_to}"
        )

        form_date_to = form_date_to + timedelta(days=7)

        query_str_date_to = min(form_date_to, yesterday).strftime("%Y-%m-%d")
        query_str_date_from = form_date_from.strftime("%Y-%m-%d")

        zone_data = call_all_zones(
            zone_list, access_token, query_str_date_from, query_str_date_to
        )

        for zone, dates_info in zone_data.items():

            date_values = [dt["data"] for dt in dates_info.values()]
            vemcount_values = [
                [
                    zone if field == "zone_id" else date_value.get(field, "")
                    for field in shared_constants.API_FIELDS[operation]
                ]
                for date_value in date_values
            ]
            data.extend(vemcount_values)
            print(
                f"{len(vemcount_values)} lines for zone {zone} from {query_str_date_from} to {query_str_date_to} ready for upload"
            )

        form_date_from = form_date_to + timedelta(days=1)
        form_date_to = form_date_from + timedelta(days=7)

        shared_azure.bulk_upload_azure_database(data, environment, operation, prefix)
        print(f"{len(data)} lines added")
    return last_date_retrieved


def upload_vemcount_to_azure():

    environment = os.environ.get("ENVIRONMENT")
    prefix = "stg"
    operation = "vemcount"

    table_exists = shared_azure.check_if_table_exists(environment, operation, prefix)

    if not table_exists:
        shared_azure.create_azure_sql_table(environment, operation, prefix)
        last_date_retrieved = datetime.strptime(
            shared_constants.EARLIEST_DATE, "%Y-%m-%d"
        ).date()
    else:
        last_date_retrieved = shared_azure.get_most_recent_date_in_db(
            environment, operation, "dt", prefix=prefix
        )
        last_date_retrieved = datetime.strptime(
            last_date_retrieved, "%Y-%m-%d %H:%M:%S"
        ).date()

    logging.info(f"Last date retrieved: {last_date_retrieved}")

    access_token = get_access_token()

    zones = get_vemcount_zones(access_token)
    if not zones:
        return False

    last_date_retrieved = get_zone_info_for_upload(
        zones, operation, environment, prefix, last_date_retrieved, access_token
    )
    print(last_date_retrieved)

    return True
