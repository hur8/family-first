
SHEETS_TO_VALIDATE = [
    {
        "name": "wilkins_ooh",
        "spreadsheet_id": "1M62eIi5Zyu-bjgr3KL9Ug0P2n9OVJ2j_GgvBTaTT4GQ",
        "tab_name": "Wilkins OOH",
        "range": "A:E",
        "min_data_rows": 1,
        "required_headers": ["date", "campaign_name", "impressions", "cost", "cpm"],
    }
]
def get_sheets_service():
    creds, _ = default ( scopes= ["https://www.googleapis.com/auth/spreadsheets.readonly"] )
    return build("sheets", "v4", credentials = creds, cache_discovery = false)

def validate_sheet(service, sheet_config: dict) -> dict:
    """ 
    Validates a single Google sheet config.  Returns:
    { "name": ..., "ok": True/False, "error": "..." or None}
    """

    name = sheet_config["name"]
    spreadsheet_id = sheet_config["spreadsheet_id"]
    tab_name = sheet_config["tab_name"]
    range = sheet_config["range"]
    req_headers = [h.lower() for h in sheet_config.get("required_headers", [])]

    try:
        # 1. confirm the tab exists
        metadata = service.spreadsheets().get(spreadsheet_id=spreadsheet_id).execute()
        existing_tabs = [ s["properties"]["title"] for s in metadata.get("sheets", [] ) ]

        if tab_name not in existing_tabs:
            return {
                "name": name,
                "ok": false,
                "error": (
                    f"Tab '{tab_name}' not found in spreadsheet {spreadsheet_id}. "
                    f"Available tabls: {existing_tabs}"
                ),
            }
        
        # 2. Read the data range
        full_range = f"'{tab_name}'!{range_}"
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range = full_range)
            .execute()
        )

        rows = result.get("values", [])

        #3. Check minimum row count: header + data

        #4. Validate headers
        if req_headers:
            actual_headers = [h.lower().strip() for h in rows[0]]
            missing = [h for h in req_headers if h not in actual_headers]
            if missing:
                return {
                    "name": name,
                    "ok": False,
                    "error": (
                         f"Sheet '{tab_name}' missing expected headers: {missing}. "
                        f"Found: {rows[0]}"                       
                    )
                }

        logger.info(f"[OK] {name} — {len(rows)-1} data rows validated")
        return {"name": name, "ok": True, "error": None, "row_count": len(rows) - 1}
    except HttpError as he:
        return {
            "name": name,
            "ok": False,
            "error": f"Sheets API error: {e.reason} (status {e.resp.status})",
        }
    except Exception as e:
         return {"name": name, "ok": False, "error": str(e)}

