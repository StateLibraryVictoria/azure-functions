import logging
import os
from datetime import datetime

from . import op_libcal, shared_azure, shared_constants


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
