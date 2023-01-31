import logging

import azure.functions as func

from ..shared_code import op_azure_sql


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handler for triggering the Libcal/Azure operations

    Args:
        req (func.HttpRequest): matches the trigger configured in serverless.yaml
    """

    logging.info("Beginning Libcal operation")

    upload_complete = op_azure_sql.upload_libcal_data_to_azure()

    if not upload_complete:
        msg = "Upload could not be completed"
        logging.warning(msg)
    else:
        msg = "Upload complete"
        logging.info(msg)

    response = {"data": upload_complete, "message": msg}
    return str(response)
