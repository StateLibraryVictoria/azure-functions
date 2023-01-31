# Azure Functions

## LibCal

LibCal is used by SLV to manage booking of its meeting rooms and other public spaces. This repo contains scripts to connect to the API and retrieve data to be stored in a database. This database can then be queried by Power BI to present the data in a useful way.

## Set-up

### LibCal API

The LibCal API is authenticated through the use of client credentials. This script uses the existing 'SLV API' app, credentials for which can be found here [https://slv-vic.libcal.com/admin/api/authentication](https://slv-vic.libcal.com/admin/api/authentication). **N.B.** You will need a LibCal admin logon to access this page.

#### .env file

In order to prevent sensitive information (keys, secrets, etc.) being published to GitHub environmental variables have been used. A template `.env` file has been created, simply add the relevant values and rename to `.env` to enable this code to be run locally.

<!-- Todo: In production the values are stored ? -->
