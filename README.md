# SLV ADF Azure Functions

This repo uses the [serverless framework](https://www.serverless.com/) to help manage Azure Functions for use in the State Library's Azure Data Factory.

## Pre-requisites

- Python 3.8
- Node package manager (npm)

## Installation and set-up

- install serverless CLI using `npm install -g serverless`
- move into the `/slv-adf-functions` directory and launch a virtual environment usings the `Pipfile` or `requirements.txt`
  - e.g. if you're using pipenv, use the command `pipenv install`
- if you are using VS Code as your IDE the [Azure App Service](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureappservice) extension is very helpful

## Azure Functions

### Environmental Variables

In order to prevent sensitive information (keys, secrets, etc.) being published to GitHub environmental variables have been used. A template `example.env` file has been created, simply add the relevant values and rename to `.env` to enable this code to be run locally.

These values are made available to Azure Functions via [Application Settings](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-use-azure-function-app-settings?tabs=portal#settings). Most of the local environmental variables are deployed to the Application Settings via the [serverless.yml](/slv-adf-functions/serverless.yml) configuration, specifically under the `environment` key e.g. `AZURE_TENANT_ID: ${env:AZURE_TENANT_ID}`. The exceptions to this are the `SQL_ADMIN_USER` and `SQL_ADMIN_PASSWORD` which are tied to the stage (dev, test or prod). These are set via Azure and utilises Azure's key vault. This [blog](https://servian.dev/accessing-azure-key-vault-from-python-functions-44d548b49b37) gives a useful overview of how it's set-up.

### LibCal

LibCal is used by SLV to manage booking of its meeting rooms and other public spaces. This repo contains scripts to connect to the API and retrieve data to be stored in a database. This database can then be queried by Power BI to present the data in a useful way.

### LibCal API

The LibCal API is authenticated through the use of client credentials. This script uses the existing 'SLV API' app, credentials for which can be found here [https://slv-vic.libcal.com/admin/api/authentication](https://slv-vic.libcal.com/admin/api/authentication). **N.B.** You will need a LibCal admin logon to access this page.
