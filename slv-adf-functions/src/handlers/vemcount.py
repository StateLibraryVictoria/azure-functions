import logging

import azure.functions as func

from ..shared_code import op_vemcount


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handler for triggering the Vemcount operations

    Args:
        req (func.HttpRequest): matches the trigger configured in serverless.yaml
    """

    logging.info("Beginning Libcal operation")

    upload_complete = op_vemcount.upload_vemcount_to_azure()

    if not upload_complete:
        msg = "Upload could not be completed"
        logging.warning(msg)
    else:
        msg = "Upload complete"
        logging.info(msg)

    response = {"data": upload_complete, "message": msg}
    return str(response)
