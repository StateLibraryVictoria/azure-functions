AZURE_VARIABLES = {
    "test": "https://slv-test-sqldw-kv.vault.azure.net/",
    "dev": "https://slv-dev-sqldw-kv.vault.azure.net/",
    "prod": "https://slv-prod-sqldw-kv.vault.azure.net/",
}

API_FIELDS = [
    "bookId",
    "eid",
    "location_name",
    "category_name",
    "item_name",
    "status",
    "fromDate",
    "toDate",
    "created",
]

DB_TABLE_NAME = "libcal_bookings"

EARLIEST_DATE = "2020-01-01"

EZPROXY_FOLDER = "transferred2Azure"
EZPROXY_SERVER = "//slvdata/ezproxyarchive"
