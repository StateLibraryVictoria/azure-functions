import logging

import azure.functions as func

from ..shared_code import op_ezproxy_transfer


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handler for triggering the EzProxy operation

    Args:
        req (func.HttpRequest): matches the trigger configured in serverless.yaml
    """

    logging.info("Beginning EzProxy operation")

    ezproxy_transfer_check = op_ezproxy_transfer.check_ezproxy_transfer()

    if not ezproxy_transfer_check:
        msg = "Transfer check not completed"
        logging.warning(msg)
    else:
        msg = "Transfer check complete"
        logging.info(msg)

    response = {"data": ezproxy_transfer_check, "message": msg}
    return str(response)
