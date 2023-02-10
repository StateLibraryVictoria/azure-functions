import os

from . import shared_azure, shared_constants


def check_ezproxy_transfer():

    # Get list of files from Azure data lake - shared_azure

    # Get list of files from on prem server
    on_prem_file_list = os.listdir(shared_constants.EZPROXY_SERVER)

    # Get list of files that match

    # Move files into transferred folder - shared_constants

    return True
