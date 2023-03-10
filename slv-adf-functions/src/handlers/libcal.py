import logging

import azure.functions as func

from ..shared_code import op_libcal


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handler for triggering the Libcal/Azure operations

    Args:
        req (func.HttpRequest): matches the trigger configured in serverless.yaml
    """

    logging.info("Beginning Libcal operation")

    # * Read and decode date passed as argument from the function invocation
    req_body = req.get_body()
    last_date_retrieved = req_body.decode("utf-8")

    upload_complete = op_libcal.upload_libcal_data_to_azure(last_date_retrieved)

    if not upload_complete:
        msg = "Upload could not be completed"
        logging.warning(msg)
    else:
        msg = "Upload complete"
        logging.info(msg)

    response = {"data": upload_complete, "message": msg}
    return str(response)
