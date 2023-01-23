import logging

from op_libcal import get_booking_data_to_upload
from shared_azure import bulk_upload_azure_database, check_if_table_exists, create_azure_sql_table

def upload_libcal_data_to_azure():

    environment = 'dev'
    prepend = 'stg'

    libcal_data_for_upload = get_booking_data_to_upload(environment)
    if len(libcal_data_for_upload) == 0:
        logging.error('No new data to extract from LibCal')
        return False

    logging.info(f'{len(libcal_data_for_upload)} rows extracted from LibCal')

    table_exists = check_if_table_exists(environment,prepend)

    if not table_exists:
        create_azure_sql_table(environment,prepend)

    upload_complete = bulk_upload_azure_database(libcal_data_for_upload,environment,prepend)

    return upload_complete

