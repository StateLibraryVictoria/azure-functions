import logging

import azure.functions as func

from ..shared_code import op_azure_sql

def main(myTimer: func.TimerRequest) -> None:
    """Handler for triggering the Libcal/Azure operations

    Args:
        myTimer (func.TimerRequest): matches the trigger configured in serverless.yaml
    """

    logging.info('Beginning Libcal operation')

    upload_complete = op_azure_sql.upload_libcal_data_to_azure()

    if not upload_complete:
        logging.warning('Upload could not be completed')
    else:
        logging.info('Upload complete!')