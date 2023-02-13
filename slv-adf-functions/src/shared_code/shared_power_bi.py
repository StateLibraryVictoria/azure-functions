import json
import logging

import requests

from . import shared_azure


def get_data_from_power_bi(endpoint, access_token):

    base_url = "https://api.powerbi.com/v1.0/myorg/"
    header = {"Authorization": f"Bearer {access_token}"}

    request = requests.get(f"{base_url}{endpoint}", headers=header)
    content = json.loads(request.content)

    return content


def get_refresh_history():
    logging.info("Getting Power BI refresh information")
    access_token = shared_azure.authenticate_by_client_token()
    refresh_history = {}

    groups = get_data_from_power_bi("groups", access_token)
    groups = groups.get("value")
    if not groups:
        logging.error("No groups returned")
        return False

    for group in groups:

        group_id = group["id"]
        group_name = group["name"]

        refresh_history[group_name] = {}

        datasets = get_data_from_power_bi(
            f"admin/groups/{group_id}/datasets", access_token
        )
        datasets = datasets.get("value")

        if not datasets:
            logging.info(f"No datasets retrieved for {group_name}")

        for dataset in datasets:

            dataset_id = dataset["id"]
            dataset_name = dataset["name"]
            dataset_refresh_history = get_data_from_power_bi(
                f"groups/{group_id}/datasets/{dataset_id}/refreshes", access_token
            )

            dataset_refresh_history = dataset_refresh_history.get("value")

            refresh_history[group_name][dataset_name] = dataset_refresh_history

    return refresh_history
