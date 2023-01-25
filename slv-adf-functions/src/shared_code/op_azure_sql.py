import logging
import os

from . import op_libcal
from . import shared_azure

def upload_libcal_data_to_azure():

    environment = os.environ.get('ENVIRONMENT')
    prefix = 'stg'

    table_exists = shared_azure.check_if_table_exists(environment,prefix)

    if not table_exists:
        shared_azure.create_azure_sql_table(environment,prefix)

    libcal_data_for_upload = op_libcal.get_booking_data_to_upload(environment, table_exists)
    if len(libcal_data_for_upload) == 0:
        logging.error('No new data to extract from LibCal')
        return False

    logging.info(f'{len(libcal_data_for_upload)} rows extracted from LibCal')

    upload_complete = shared_azure.bulk_upload_azure_database(libcal_data_for_upload,environment,prefix)

    return upload_complete

    

