
import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#--
# Configuration
#--
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

def trigger_dataform_workflow() -> dict:
    """
    Creates a Dataform compilation result then starts a workflow invocation.
    Returns the invocatino resource dict on success
    Raises on failure
    """
    token = get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. Create a compilation result: compile SQLX from the workspace
    compile_url = f"{DATAFORM_BASE_URL}:computeRepositoryAccessTokenStatus"
    compile_url_2 = f"{DATAFORM_BASE_URL}/compilationResults"
    compile_body = {
        "workspace": (
            f"projects/{GCP_PROJECT}/locations/{DATAFORM_REGION}"
            f"/repositories/{DATAFORM_REPO}/workspaces/{DATAFORM_WORKSPACE}"
        )
    }

    logger.info("Creating Dataformcompilation result...")
    resp = http_requests.post(compile_url, headers=headers, json=compile_body)
    resp.raise_for_status()

    compilation = resp.json()
    compilation_result_name = compilation["name"]
    logger.info(f"Compilation result: {compilation_result_name}")

    #2. Create a workflow invocation against the compilation result
    invoke_url = f"{DATAFORM_BASE_URL}/workflowInvocations"
    invoke_body = {
        "compilationResult": compilation_result_name,
    }

    resp = http_requests.post(invoke_url, headers=headers, json=invoke_body)
    resp_raise_for_status()
    invocation = resp.json()
    return invocation

@functions_framework.http
def validate_and_run_dataform(request):
    """
    HTTP Cloud Function entry point.
    Cloud Scheduler POSTs to this endpoint on the cron schedule
    """
    logger.info("=== Starting Google Sheet validation ===")
    service = get_sheets_service()
    results = [validate_sheet(service, cfg) for cfg in SHEETS_TO_VALIDATE]
    
    failures = [r for r in results if not r["ok"]]

    if failures:
        error_details = [{"sheet": f["name"], "error": f["error"]} for f in failures]
        logger.error(f"Validation failed: {json.dumps(error_details, indent=2)}")
        # return HTTP 200 so Cloud Scheduler doesn't keep retrying
        # return HTTP 500 if want Cloud Scheduler to retry on validation failure.  Not good idea
        return (
            json.dumps(
                {
                    "status": "vaalidation_failed",
                    "message": "One or more sheets failed validation.  Dataform was NOT triggered",
                    "failures": error_details,
                }), (
                    200,
                    {"Content-Type": "application/json"},
                )
            )
    logger.info("=== All sheets valid - triggering Dataform ===")

    try:
        invocation = trigger_dataform_workflow()
        return (
            json.dumps( {
                "status": "success",
                "message": "All sheets validated.  Dataform workflow invocation created.",
                "invocation_name": invocation.get("name"),
                "validation_summary": [
                    {"sheet": r["name"], "rows": r.get("row_count")} for r in results
                ],
            }),
            200,
            {"Content-Type": "application/json"},
        )
    except Exception as e:
        logger.exception("Failed to trigger Dataform")
        return (
            json.dumps(
                {"status": "dataform_trigger_failed", 
                 "error": str(e)},
                 500,
                 {"Content-Type": "application/json"},
            )
        )