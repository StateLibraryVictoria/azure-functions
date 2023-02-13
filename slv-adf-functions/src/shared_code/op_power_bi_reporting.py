import logging
from datetime import date

from . import shared_power_bi


def create_power_bi_report_email():

    refresh_history = shared_power_bi.get_refresh_history()

    if not refresh_history:
        logging.error("Unable to retrieve Power BI data")
        return False

    logging.info("Power BI refresh history retrieved. Creating email body")

    failure_report = ""

    high_level_report = """
        <table>
            <tr>
                <th>Workspace</th>
                <th>Total dashboards</th>
                <th>Completed</th>
                <th>Failed</th>
                <th>Disabled</th>
                <th>Unknown</th>
            </tr>
        """

    workspace_refreshes = {}
    for workspace, datasets in refresh_history.items():

        failure_report += f"<h2>{workspace}</h2>"
        failure_report += """
            <table>
                <tr>
                    <th>Workspace</th>
                    <th>Refresh status</th>
                    <th>Attempted refreshes</th>
                    <th>Failed refreshes</th>
                </tr>
            """

        workspace_refreshes[workspace] = {}

        for dataset_name, refresh_history in datasets.items():

            if refresh_history:

                number_of_refresh_attempts = len(refresh_history)
                refresh_status = refresh_history[0]["status"]
                failures = [
                    refresh
                    for refresh in refresh_history
                    if refresh["status"] == "Failed"
                ]
                number_of_failures = len(failures)
            else:
                number_of_refresh_attempts = "0"
                number_of_failures = "n/a"
                refresh_status = "Unknown"
            failure_report += f"""
                                <tr>
                                    <td>{dataset_name}</td>
                                    <td>{refresh_status}</td>
                                    <td>{number_of_refresh_attempts}</td>
                                    <td>{number_of_failures}</td>
                                </tr>
                            """
            workspace_refreshes[workspace][dataset_name] = refresh_status

        failure_report += "</table>"

        workspace_refresh_statuses = list(workspace_refreshes[workspace].values())

        high_level_report += f"""
            <tr>
                <td>{workspace}</td>
                <td>{len(datasets)}</td>
                <td>{workspace_refresh_statuses.count('Completed')}</td>
                <td>{workspace_refresh_statuses.count('Failed')}</td>
                <td>{workspace_refresh_statuses.count('Disabled')}</td>
                <td>{workspace_refresh_statuses.count('Unknown')}</td>
            </tr>
        """

    high_level_report += "</table>"

    email_style = """
    <style>
        table, th, td  {
            border: 1px solid black;
            border-collapse: collapse;
            padding: 2px;
            }
    </style>
    """

    email_body = f"""
    {email_style}
    <h1>SLV Power BI Dataset Refresh Report: {date.today()}</h1>
    <br></br>
    <h2>Dashboard refresh statuses</h2>
    {high_level_report}
    <br></br>
    <h2>Granular report</h2>
    {failure_report}
    """
    return email_body
