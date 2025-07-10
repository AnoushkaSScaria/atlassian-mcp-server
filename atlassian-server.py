"""
MCP Server for Jira and Confluence Integration

This FastMCP server provides tools for interacting with Jira and Confluence APIs.
It supports fetching Jira tickets, creating Confluence pages, and generating
test plans from Jira issues.

Key Features:
- Fetch Jira tickets with child stories/subtasks
- Create and update Confluence pages
- Generate test plans from Jira data


Environment Variables Required:
    - JIRA_EMAIL: Your Atlassian account email
    - JIRA_API_TOKEN: Your Jira API token
    - CONFLUENCE_API_TOKEN: Your Confluence API token

"""

import sys
import io
import base64
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ==========================================================================
# SYSTEM CONFIGURATION
# ============================================================================

# Configure stdout/stderr encoding for proper Unicode handling
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Initialize FastMCP server
mcp = FastMCP("jira-confluence")

# ======================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# API Base URLs
JIRA_BASE_URL = "https://onedatascan.atlassian.net"
CONFLUENCE_BASE_URL = "https://onedatascan.atlassian.net/wiki"

# TODO: Move these to environment variables for security
# JIRA_EMAIL = "your.account@onedatascan.com"
# JIRA_API_TOKEN = "your_api_token_here"  
# CONFLUENCE_API_TOKEN = "your_api_token_here"

# Default HTTP headers for API requests
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ============================================================================
# AUTHENTICATION UTILITIES
# ============================================================================

def create_auth_headers(token: str, email: str) -> Dict[str, str]:
    """
    Create authentication headers for Atlassian API requests.
    Uses Basic Authentication with base64 encoded email:token combination.
   
    Args:
        token: API token for the service
        email: User email address
       
    Returns:
        Dictionary containing headers with Authorization
    """
    auth_string = f"{email}:{token}"
    b64_auth = base64.b64encode(auth_string.encode()).decode()
   
    return {
        **DEFAULT_HEADERS,
        "Authorization": f"Basic {b64_auth}"
    }

# ============================================================================
# DATA EXTRACTION UTILITIES
# ============================================================================

def extract_description_from_jira(description_field: Optional[Dict[str, Any]]) -> str:
    """
    Safely extract description text from Jira's complex description structure.
   
    Jira uses a complex nested JSON structure for rich text content.
    This function traverses the structure to extract plain text.
   
    Args:
        description_field: Jira description field data
       
    Returns:
        Extracted text or default message if no description available
    """
    if not description_field:
        return "No description available"
   
    try:
        content = description_field.get("content", [])
        if not content:
            return "No description available"
       
        # Extract text from nested content structure
        text_parts = []
        for item in content:
            if item.get("type") == "paragraph":
                paragraph_content = item.get("content", [])
                for text_item in paragraph_content:
                    if text_item.get("type") == "text":
                        text = text_item.get("text", "")
                        if text:
                            text_parts.append(text)
       
        return " ".join(text_parts) if text_parts else "No description available"
       
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error extracting description: {e}")
        return "No description available"

def extract_jira_field_value(field_data: Optional[Dict[str, Any]], field_name: str) -> str:
    """
    Safely extract a field value from Jira field data.
   
    Args:
        field_data: Dictionary containing field information
        field_name: Name of the field to extract
       
    Returns:
        Field value or "Unknown" if not available
    """
    if not field_data:
        return "Unknown"
   
    if isinstance(field_data, dict):
        return field_data.get(field_name, "Unknown")
   
    return str(field_data) if field_data else "Unknown"

# ============================================================================
# HTTP REQUEST UTILITIES
# ============================================================================

async def make_jira_request(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    Make an authenticated GET request to the Jira API.
   
    Args:
        endpoint: API endpoint path (starting with /)
       
    Returns:
        JSON response data or None if request failed
    """
    url = f"{JIRA_BASE_URL}{endpoint}"
    headers = create_auth_headers(JIRA_API_TOKEN, JIRA_EMAIL)
   
    async with httpx.AsyncClient() as client:
        try:
            print(f"DEBUG: Making Jira request to {url}")
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
           
            return response.json()
           
        except httpx.HTTPStatusError as e:
            print(f"HTTP error making Jira request: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Error making Jira request: {e}")
            return None

async def make_confluence_request(
    endpoint: str,
    payload: Dict[str, Any],
    method: str = "POST"
) -> Optional[Dict[str, Any]]:
    """
    Make an authenticated request to the Confluence API.
   
    Args:
        endpoint: API endpoint path (starting with /)
        payload: JSON payload for the request
        method: HTTP method (POST, PUT, GET)
       
    Returns:
        JSON response data or None if request failed
    """
    url = f"{CONFLUENCE_BASE_URL}{endpoint}"
    headers = create_auth_headers(CONFLUENCE_API_TOKEN, JIRA_EMAIL)
   
    async with httpx.AsyncClient() as client:
        try:
            print(f"DEBUG: Making Confluence {method} request to {url}")
            print(f"DEBUG: Payload: {payload}")
           
            if method.upper() == "POST":
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=payload, timeout=30.0)
            elif method.upper() == "GET":
                response = await client.get(url, headers=headers, params=payload, timeout=30.0)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
           
            print(f"DEBUG: Response status: {response.status_code}")
            response.raise_for_status()
           
            return response.json()
           
        except httpx.HTTPStatusError as e:
            print(f"HTTP error making Confluence request: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"Error making Confluence request: {e}")
            return None

# ============================================================================
# JIRA DATA PROCESSING
# ============================================================================

async def fetch_jira_issue_details(issue_key: str) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive details for a Jira issue.
   
    Args:
        issue_key: Jira issue key (e.g., PROJ-123)
       
    Returns:
        Dictionary containing issue details or None if failed
    """
    data = await make_jira_request(f"/rest/api/3/issue/{issue_key}")
    if not data:
        return None
   
    fields = data.get("fields", {})
   
    return {
        "key": issue_key,
        "summary": fields.get("summary", "No summary"),
        "status": extract_jira_field_value(fields.get("status"), "name"),
        "reporter": extract_jira_field_value(fields.get("reporter"), "displayName"),
        "assignee": extract_jira_field_value(fields.get("assignee"), "displayName"),
        "priority": extract_jira_field_value(fields.get("priority"), "name"),
        "issue_type": extract_jira_field_value(fields.get("issuetype"), "name"),
        "description": extract_description_from_jira(fields.get("description")),
        "subtasks": fields.get("subtasks", [])
    }

async def fetch_subtask_details(subtask_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Fetch details for a Jira subtask.
   
    Args:
        subtask_data: Subtask information from parent issue
       
    Returns:
        Dictionary containing subtask details
    """
    sub_key = subtask_data.get("key")
    if not sub_key:
        return {"error": "No subtask key found"}
   
    sub_data = await make_jira_request(f"/rest/api/3/issue/{sub_key}")
    if not sub_data:
        return {"key": sub_key, "error": "Unable to fetch subtask details"}
   
    sub_fields = sub_data.get("fields", {})
   
    return {
        "key": sub_key,
        "summary": sub_fields.get("summary", "No summary"),
        "status": extract_jira_field_value(sub_fields.get("status"), "name"),
        "reporter": extract_jira_field_value(sub_fields.get("reporter"), "displayName"),
        "description": extract_description_from_jira(sub_fields.get("description"))
    }

def format_jira_issue_output(issue_details: Dict[str, Any], subtask_details: list) -> str:
    """
    Format Jira issue and subtask information for output.
   
    Args:
        issue_details: Main issue details
        subtask_details: List of subtask details
       
    Returns:
        Formatted string representation
    """
    result = f"""
Jira Ticket: {issue_details['key']}
Summary: {issue_details['summary']}
Status: {issue_details['status']}
Reporter: {issue_details['reporter']}
Description: {issue_details['description']}
"""
   
    if subtask_details:
        result += "\nChild Stories/Subtasks:\n"
        for subtask in subtask_details:
            if "error" in subtask:
                result += f"\n  - {subtask.get('key', 'Unknown')}: {subtask['error']}\n"
            else:
                result += f"""
  - {subtask['key']}: {subtask['summary']}
    Status: {subtask['status']}
    Reporter: {subtask['reporter']}
    Description: {subtask['description']}
"""
    else:
        result += "\nNo child stories or subtasks found.\n"
   
    return result

# ============================================================================
# CONFLUENCE PAGE MANAGEMENT
# ============================================================================

async def find_existing_confluence_page(space_key: str, title: str) -> Optional[Dict[str, Any]]:
    """
    Search for an existing Confluence page by title and space.
   
    Args:
        space_key: Confluence space key
        title: Page title to search for
       
    Returns:
        Page information if found, None otherwise
    """
    search_params = {
        "title": title,
        "spaceKey": space_key,
        "expand": "version"
    }
   
    search_data = await make_confluence_request("/rest/api/content", search_params, "GET")
   
    if search_data and search_data.get("results"):
        return search_data["results"][0]
   
    return None

async def create_new_confluence_page(
    space_key: str,
    title: str,
    content: str
) -> Dict[str, Any]:
    """
    Create a new Confluence page.
   
    Args:
        space_key: Confluence space key
        title: Page title
        content: Page content in storage format
       
    Returns:
        API response data
    """
    page_data = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        }
    }
   
    return await make_confluence_request("/rest/api/content/", page_data, "POST")

async def update_existing_confluence_page(
    page_id: str,
    space_key: str,
    title: str,
    content: str,
    current_version: int
) -> Dict[str, Any]:
    """
    Update an existing Confluence page.
   
    Args:
        page_id: ID of the page to update
        space_key: Confluence space key
        title: Page title
        content: New page content
        current_version: Current version number of the page
       
    Returns:
        API response data
    """
    update_data = {
        "id": page_id,
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": content,
                "representation": "storage"
            }
        },
        "version": {
            "number": current_version + 1
        }
    }
   
    return await make_confluence_request(f"/rest/api/content/{page_id}", update_data, "PUT")

def extract_page_url(response_data: Dict[str, Any]) -> str:
    """
    Extract the web URL from Confluence API response.
   
    Args:
        response_data: API response containing page information
       
    Returns:
        Full URL to the created/updated page
    """
    links = response_data.get('_links', {})
    base_url = links.get('base', '')
    web_ui = links.get('webui', '')
    return f"{base_url}{web_ui}"

# ============================================================================
# MCP TOOLS
# ============================================================================

@mcp.tool(
    name="get_jira_ticket",
    description="Get details for a Jira ticket by issue key, including child stories and subtasks"
)
async def get_jira_ticket(issue_key: str) -> str:
    """
    Fetch comprehensive details for a Jira ticket.
   
    This tool retrieves the main issue details along with any child stories
    or subtasks. It handles complex Jira field structures and provides
    formatted output suitable for further processing.
   
    Args:
        issue_key: Jira issue key (e.g., PROJ-123)
       
    Returns:
        Formatted string containing issue and subtask details
    """
    print(f"DEBUG: Fetching Jira ticket {issue_key}")
   
    # Fetch main issue details
    issue_details = await fetch_jira_issue_details(issue_key)
    if not issue_details:
        return f"Unable to fetch Jira ticket {issue_key}."
   
    # Fetch subtask details
    subtask_details = []
    for subtask_data in issue_details.get("subtasks", []):
        subtask_info = await fetch_subtask_details(subtask_data)
        subtask_details.append(subtask_info)
   
    # Format and return results
    return format_jira_issue_output(issue_details, subtask_details)

@mcp.tool(
    name="create_confluence_page",
    description="Create a new page in Confluence with specified content"
)
async def create_confluence_page(space_key: str, title: str, body: str) -> str:
    """
    Create a page in Confluence with the given space key, title, and body content.
   
    This tool creates a new Confluence page in the specified space. If a page
    with the same title already exists, this will fail. Use create_test_plan_from_jira
    for create-or-update functionality.
   
    Args:
        space_key: Confluence space key where the page will be created
        title: Title for the new page
        body: HTML content for the page body
       
    Returns:
        Success message with page URL or error description
    """
    print(f"DEBUG: Creating Confluence page '{title}' in space '{space_key}'")
   
    try:
        # Validate inputs
        if not all([space_key, title, body]):
            return "Error: space_key, title, and body are all required"
       
        # Create the page
        response_data = await create_new_confluence_page(space_key, title, body)
       
        if response_data:
            page_url = extract_page_url(response_data)
            return f"Page created successfully: {page_url}"
        else:
            return "Failed to create page: API request failed"
           
    except Exception as e:
        return f"Error creating page: {str(e)}"

@mcp.tool(
    name="create_test_plan_from_jira",
    description="Create or update a Confluence page with a test plan based on Jira ticket data"
)
async def create_test_plan_from_jira(
    issue_key: str,
    confluence_space_key: str,
    confluence_title: str,
    test_plan: str
) -> str:
    """
    Create or update a Confluence page with a provided test plan.
   
    This tool fetches Jira ticket information for validation and logging,
    then creates or updates a Confluence page with the provided test plan content.
    If a page with the same title exists, it will be updated; otherwise,
    a new page will be created.
   
    Args:
        issue_key: Jira issue key for reference and validation
        confluence_space_key: Confluence space where the page should be created
        confluence_title: Title for the Confluence page
        test_plan: Complete test plan content in HTML format
       
    Returns:
        Success message with page URL or error description
    """
    print(f"DEBUG: Creating test plan for {issue_key} in Confluence")
   
    try:
        # Validate inputs
        if not all([issue_key, confluence_space_key, confluence_title, test_plan]):
            return "Error: All parameters (issue_key, confluence_space_key, confluence_title, test_plan) are required"
       
        # Fetch Jira ticket for validation and logging
        issue_details = await fetch_jira_issue_details(issue_key)
        if not issue_details:
            return f"Unable to fetch Jira ticket {issue_key} for validation."
       
        print(f"DEBUG: Validated Jira ticket - Summary: {issue_details['summary']}")
        print(f"DEBUG: Test plan length: {len(test_plan)} characters")
       
        # Check if page already exists
        existing_page = await find_existing_confluence_page(confluence_space_key, confluence_title)
       
        if existing_page:
            # Update existing page
            page_id = existing_page["id"]
            current_version = existing_page["version"]["number"]
           
            print(f"DEBUG: Updating existing page {page_id}, version {current_version}")
           
            response_data = await update_existing_confluence_page(
                page_id, confluence_space_key, confluence_title, test_plan, current_version
            )
           
            if response_data:
                page_url = extract_page_url(response_data)
                return f"Test plan page updated successfully: {page_url}"
            else:
                return "Failed to update existing test plan page"
               
        else:
            # Create new page
            print("DEBUG: Creating new test plan page")
           
            response_data = await create_new_confluence_page(
                confluence_space_key, confluence_title, test_plan
            )
           
            if response_data:
                page_url = extract_page_url(response_data)
                return f"Test plan page created successfully: {page_url}"
            else:
                return "Failed to create new test plan page"
               
    except Exception as e:
        print(f"DEBUG: Exception in create_test_plan_from_jira: {e}")
        import traceback
        traceback.print_exc()
        return f"Error creating or updating test plan page: {str(e)}"

# ============================================================================
# SERVER ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    mcp.run(transport='stdio')