<<<<<<< HEAD
This MCP (Model Context Protocol) client integrates with AWS Bedrock agents to process queries and handle tool calls, specifically designed for creating test plans from Jira issues using Confluence integration.

Prerequisites:
    - Python 3.10 installed
    - AWS credentials configured (via AWS CLI)
    - MCP server script
    - Required environment variables set up

Installation:
    - uv pip install -r requirements.txt

Basic Usage:
    - To configure aws credentials -
        - aws configure sso, select Lab-Engineering profile, AWSPowerUserAccess
    - To run the MCP client - 
        - cd into client directory, then do: uv run atlassian-mcp-client.py "path/to/server.py"
    - Example query -
        - "Create a test plan in confluence where the issue key is "WSD-XXXXX", the confluence space key is "XXXX", the confluence page title is  "Example test plan - WSD XXXXX", and the test plan is a generated test plan."

A Basic Architecture view (from Anthropic's site for MCP client developers):
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server     │◄──►│  External APIs  │
│                 │    │                  │    │ (Jira/Confluence)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ AWS Bedrock     │
│ Agent           │
└─────────────────┘

Key Components:
    - MCPClient: Main class that manages connections and processing
    - Connection Management: Handles MCP server connections
    - Content Generation: Generates test plans using Bedrock agents
    - Tool Handling: Processes returnControl events and tool calls
=======
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


>>>>>>> 31fd4a8afde5492d35184533818f61ea42a4fca8
