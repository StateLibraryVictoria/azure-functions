AZURE_VARIABLES = {
    "test": "https://slv-test-sqldw-kv.vault.azure.net/",
    "dev": "https://slv-dev-sqldw-kv.vault.azure.net/",
    "prod": "https://slv-prod-sqldw-kv.vault.azure.net/",
}

API_FIELDS = {
    "libcal": [
        "bookId",
        "eid",
        "location_name",
        "category_name",
        "item_name",
        "status",
        "fromDate",
        "toDate",
        "created",
    ],
    "vemcount": ["zone_id", "dt", "count_in", "count_out", "inside"],
}

DB_TABLE_NAMES = {"libcal": "libcal_bookings", "vemcount": "vemcount"}

EARLIEST_DATE = "2020-01-01"
