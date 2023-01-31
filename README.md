# SLV ADF Azure Functions

This repo uses the [serverless framework](https://www.serverless.com/) to help manage Azure Functions for use in the State Library's Azure Data Factory.

## Pre-requisites

- Python 3.8
- Node package manager (npm)
- SLV Azure AD account with admin privileges

## Installation and set-up

- install serverless CLI using `npm install -g serverless`
- move into the `/slv-adf-functions` directory and launch a virtual environment usings the `Pipfile` or `requirements.txt`
  - e.g. if you're using pipenv, use the command `pipenv install`
- if you are using VS Code as your IDE the [Azure App Service](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureappservice) extension is very helpful
- it is also highly recommended that you have the Azure CLI installed
- authentication is done via the ['adf-app'](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/0dcd68a1-78a1-4f45-bd0b-0be230e57e45/isMSAApp~/false) Service Principal. Follow this guide to set-up your credentials locally: [https://www.serverless.com/framework/docs/providers/azure/guide/credentials](https://www.serverless.com/framework/docs/providers/azure/guide/credentials)
  - **n.b.** these credentials will need to be added to the [`.env`](#environmental-variables) file

## Azure Functions

Azure Function Apps ('Apps') are used to group together Azure Functions ('Functions'), this maps directly to each Serverless project that is set up. Therefore in this repo, the App is everything contained within the [`slv-adf-functions`](/slv-adf-functions/) directory. The App maps to three versions deployed on Azure, organised by 'stage':

- dev
- test
- prod

### Directory Structure

The Python code is all housed within the [`src`](/slv-adf-functions/src/) directory. Within which the files are split into [handlers](/slv-adf-functions/src/handlers/) and [shared_code](/slv-adf-functions/src/shared_code/).

Each Function within the App has a handler file in the `handlers` directory, this is where the function is invoked from. Azure Functions allow a variety of different Trigger types, but because these functions are being used within an Azure Data Factory setting, all of them used the HTTP trigger. Each function is configured in the `serverless.yml` file e.g.

```yaml
functions:
  libcal:
    handler: src/handlers/libcal.main
    events:
      - http: true
        methods:
          - get
          - post
        x-azure-settings:
          authLevel: anonymous
```

The `shared_code` folder contains a mix of:

- `shared_` helper functions that are designed to be used across multiple different functions
- `op_` or operation functions that are more specific to each Function.

<!-- todo should the directory structure be cleaned up a bit further? -->

### Environmental Variables

In order to prevent sensitive information (keys, secrets, etc.) being published to GitHub environmental variables have been used. A template `example.env` file has been created, simply add the relevant values and rename to `.env` to enable this code to be run locally.

These values are made available to Azure Functions via [Application Settings](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-use-azure-function-app-settings?tabs=portal#settings). Most of the local environmental variables are deployed to the Application Settings via the [serverless.yml](/slv-adf-functions/serverless.yml) configuration, specifically under the `environment` key e.g. `AZURE_TENANT_ID: ${env:AZURE_TENANT_ID}`. The exceptions to this are the `SQL_ADMIN_USER` and `SQL_ADMIN_PASSWORD` which are tied to the stage (dev, test or prod). These are set via Azure and utilises Azure's key vault. This [blog](https://servian.dev/accessing-azure-key-vault-from-python-functions-44d548b49b37) gives a useful overview of how it's set-up.

### LibCal

LibCal is used by SLV to manage booking of its meeting rooms and other public spaces. This repo contains scripts to connect to the API and retrieve data to be stored in a database. This database can then be queried by Power BI to present the data in a useful way.

### LibCal API

The LibCal API is authenticated through the use of client credentials. This script uses the existing 'SLV API' app, credentials for which can be found here [https://slv-vic.libcal.com/admin/api/authentication](https://slv-vic.libcal.com/admin/api/authentication). **N.B.** You will need a LibCal admin logon to access this page.
