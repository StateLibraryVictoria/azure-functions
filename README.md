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

### Pre-commit hooks

This repo uses [https://pre-commit.com/](https://pre-commit.com/) to call 'hooks' each time changes are committed in git. Essentially these hooks are a series formatting scripts that help to create consistency and aid maintainability in the codebase.

The hooks are configured in the `.pre-commit.config.yaml` file. To install and enable the hooks ensure that `pre-commit` is installed (it is included in the repo's `Pipfile` and `requirements.txt`) and then run the command `pre-commit install`. The hooks will now run each time a commit is made.

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

- `shared_` helper functions that are designed to be used across multiple different Functions
- `op_` or operation functions that are more specific to each Function

<!-- todo should the directory structure be cleaned up a bit further? -->

### Environmental Variables

In order to prevent sensitive information (keys, secrets, etc.) being published to GitHub environmental variables have been used. A template `example.env` file has been created, simply add the relevant values and rename to `.env` to enable this code to be run locally.

These values are made available to Azure Functions via [Application Settings](https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-use-azure-function-app-settings?tabs=portal#settings). Most of the local environmental variables are deployed to the Application Settings via the [serverless.yml](/slv-adf-functions/serverless.yml) configuration, specifically under the `environment` key e.g. `AZURE_TENANT_ID: ${env:AZURE_TENANT_ID}`.

The exceptions to this are the `SQL_ADMIN_USER` and `SQL_ADMIN_PASSWORD` which are tied to the stage (dev, test or prod). These are set via Azure and utilises Azure's key vault. This [blog](https://servian.dev/accessing-azure-key-vault-from-python-functions-44d548b49b37) gives a useful overview of how it's set-up.

### Deployment

From within the [`slv-adf-functions`](/slv-adf-functions/) dir use the following command to deploy your code:

```sh
sls deploy -s <stage_name>
```

You must replace `<stage_name>` with one of the following values: `dev`, `test` or `prod`.

Before deploying the function, it may be useful to invoke it locally for testing purposes. To do so run the following command, replacing `<function_name>` with the name of the Function as given in `serverless.yaml`:

```sh
sls invoke --function <function_name>
```

Link to serverless CLI `invoke` documentation - [https://www.serverless.com/framework/docs/providers/azure/cli-reference/invoke](https://www.serverless.com/framework/docs/providers/azure/cli-reference/invoke)

## Deployed Functions

### 1. LibCal

LibCal is used by SLV to manage booking of its meeting rooms and other public spaces. This repo contains scripts to connect to the API and retrieve data to be stored in a database. This database can then be queried by Power BI to present the data in a useful way.

#### LibCal API

The LibCal API is authenticated through the use of client credentials. This script uses the existing 'SLV API' app, credentials for which can be found here [https://slv-vic.libcal.com/admin/api/authentication](https://slv-vic.libcal.com/admin/api/authentication). **N.B.** You will need a LibCal admin logon to access this page.

### 2. Power BI Refresh Report

Power BI is the Library's dashboard software of choice and is used to create visualisations from a range of different data sources. Power BI allows admin users to configure scheduled refreshes of the data. In practice at SLV this is usually on an daily basis. This function summarises the success, failure or other statuses for the SLV's Power BI dashboards/workspaces, and returns a HTML string to be emailed as a daily update.

#### Power BI Service Principal and API

Microsoft provide a variety of API endpoints to help query and manage Power BI - [https://learn.microsoft.com/en-us/rest/api/power-bi/](https://learn.microsoft.com/en-us/rest/api/power-bi/). In order to use them, an authenticated user must retrieve an access token. To avoid tying the function to a person's SLV AD account, a service principal has been set-up, which acts as an autonomous app that can be authenticated against the Power BI admin APIs. Here is a useful link to help explain how aService Principal can be used in this context [https://learn.microsoft.com/en-us/power-bi/enterprise/read-only-apis-service-principal-authentication](https://learn.microsoft.com/en-us/power-bi/enterprise/read-only-apis-service-principal-authentication).

For this function the `power-bi-monitor-app` service principal was created ([here in the azure portal](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/604459ec-de3c-4ea4-8e1e-37031c4c4c9e/isMSAApp~/false)). This app was then added to each Power BI workspace as an Admin user, instructions [here](https://learn.microsoft.com/en-us/power-bi/collaborate-share/service-give-access-new-workspaces).

## Logging

<!-- Logging related to the LibCal operation can be found at two different levels:

1. At the 'Pipeline' level, which is scheduled to run daily and includes high level logging for each component of the pipeline, including the LibCal function: [link](https://adf.azure.com/en/monitoring/triggerruns?factory=%2Fsubscriptions%2Fb4a0deaa-b166-4231-b6b8-9b9a71a7c0d2%2FresourceGroups%2Fslv-dev-datafactory-rg%2Fproviders%2FMicrosoft.DataFactory%2Ffactories%2Fslv-dev-datafactory)
2. At the Function level, which contains more detailed logging as defined in the code itself [link](https://portal.azure.com/#view/WebsitesExtension/FunctionMenuBlade/~/monitor/resourceId/%2Fsubscriptions%2Fb4a0deaa-b166-4231-b6b8-9b9a71a7c0d2%2FresourceGroups%2Fapp-ausse-dev-slv-adf-functions-rg%2Fproviders%2FMicrosoft.Web%2Fsites%2Fapp-ausse-dev-slv-adf-functions%2Ffunctions%2Flibcal) -->

Logging related to each pipeline/function happens at a variety of levels 🏴‍☠️:

1. at the 'Pipeline' level useful information is logged in the 'Monitor' tab e.g for the **dev** data factory [monitor](https://adf.azure.com/en/monitoring/pipelineruns?factory=%2Fsubscriptions%2Fb4a0deaa-b166-4231-b6b8-9b9a71a7c0d2%2FresourceGroups%2Fslv-dev-datafactory-rg%2Fproviders%2FMicrosoft.DataFactory%2Ffactories%2Fslv-dev-datafactory).
2. at the 'Function' level the logging is provided per invocation of the function, and directly reflects the logging defined in this repos code. For example, the function invocations for **dev power_bi_report** can be viewed [here](https://portal.azure.com/#view/WebsitesExtension/FunctionMenuBlade/~/monitor/resourceId/%2Fsubscriptions%2Fb4a0deaa-b166-4231-b6b8-9b9a71a7c0d2%2FresourceGroups%2Fapp-ausse-dev-slv-adf-functions-rg%2Fproviders%2FMicrosoft.Web%2Fsites%2Fapp-ausse-dev-slv-adf-functions%2Ffunctions%2Fpower_bi_report).

**N.B.** it is worth high-lighting that Function logs usually have a delay of ~5mins from when the function has been invoked.
