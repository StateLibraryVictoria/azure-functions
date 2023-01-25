import datetime
import logging

import azure.functions as func

from ..shared_code import op_azure_sql

def main(myTimer: func.TimerRequest) -> None:

    logging.info('RESTART')
    logging.info(myTimer)

    # upload_complete = op_azure_sql.upload_libcal_data_to_azure()

    # if not upload_complete:
    #     logging.warning('Upload could not be completed')
    # else:
    #     logging.info('Upload complete!')

    utc_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if myTimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)