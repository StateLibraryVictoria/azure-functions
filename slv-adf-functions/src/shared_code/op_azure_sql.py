import datetime
import logging
import os

from . import op_libcal
from . import shared_azure
from . import shared_constants

def upload_libcal_data_to_azure():
    """Coordinates the retrieval of data from Libcal and subsequent upload to Azure SQL database

    Returns:
        bool: Returns True/False to indicate success of the operation
    """
    environment = os.environ.get('ENVIRONMENT')
    prefix = 'stg'
    
    table_exists = shared_azure.check_if_table_exists(environment,prefix)

    if not table_exists:
        shared_azure.create_azure_sql_table(environment,prefix)
        last_date_retrieved = datetime.strptime(shared_constants.EARLIEST_DATE,'%Y-%m-%d').date()
    else:
        last_date_retrieved = shared_azure.get_most_recent_date_in_db(environment,prefix='stg')

    logging.info(f'Last date retrieved: {last_date_retrieved}')

    libcal_data_for_upload = op_libcal.get_booking_data_to_upload(environment, last_date_retrieved)
    if len(libcal_data_for_upload) == 0:
        logging.error('No new data to extract from LibCal')
        return False

    logging.info(f'{len(libcal_data_for_upload)} rows extracted from LibCal')

    upload_complete = shared_azure.bulk_upload_azure_database(libcal_data_for_upload,environment,prefix)

    return upload_complete

    

