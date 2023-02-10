import logging

import azure.functions as func

from ..shared_code import op_power_bi_reporting


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Handler for triggering the POwer BI reporting operation

    Args:
        req (func.HttpRequest): matches the trigger configured in serverless.yaml
    """

    logging.info("Beginning Power BI reporting operation")

    power_bi_reporting = op_power_bi_reporting.create_power_bi_report_email()

    if not power_bi_reporting:
        msg = "Power BI reporting not completed"
        logging.warning(msg)
    else:
        msg = "Power BI reporting complete"
        logging.info(msg)

    response = {"data": power_bi_reporting, "message": msg}
    return str(response)
