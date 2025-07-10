Prerequisites:
    - Python 3.10 with required dependencies
    - Atlassian account with access to Jira and Confluence
    - API tokens for both Jira and Confluence

Installation:
    - install uv: 
        - powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    - install fastmcp:
        - pip install fastmcp httpx

Configuration:
    - You need to configure the following in the server code:
        - JIRA_EMAIL = "your.account@onedatascan.com"
        - JIRA_API_TOKEN = "your_jira_api_token_here"
        - CONFLUENCE_API_TOKEN = "your_confluence_api_token_here"

Available tools:
    1. get_jira_ticket
        - Fetches comprehensive details for a Jira issue including child stories and subtasks.
        - Parameters:
            - issue_key (str): Jira issue key (e.g., "PROJ-123")
        - Returns: Formatted string with issue details, status, reporter, description, and all subtasks.
    
    2. create_confluence_page
        - Creates a new page in Confluence with specified content.
        - Parameters:
            - space_key (str): Confluence space key 
            - title (str): Page title
            - body (str): HTML content for the page
        - Returns: Success message with page URL or error description.

    3. create_test_plan_from_jira
        - Creates or updates a Confluence page with a test plan based on Jira ticket data.
        - Parameters:
            - issue_key (str): Jira issue key for reference
            - confluence_space_key (str): Confluence space key
            - confluence_title (str): Title for the page
            - test_plan (str): Complete test plan content in HTML
        - Returns: Success message with page URL or error description.


