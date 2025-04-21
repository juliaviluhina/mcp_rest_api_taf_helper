# MCP Server for Swagger to TypeScript DTO Generation [Functionality will be later extended]

This MCP server automates the process of generating TypeScript Data Transfer Objects (DTOs) from Swagger/OpenAPI JSON definitions stored in GitHub repositories.

**Assumption** User works with test framework based on this template: https://github.com/juliaviluhina/taf_rest_api_template

## Features

- Connect to GitHub repositories
- Read and parse Swagger/OpenAPI JSON files
- Generate TypeScript interfaces and enums from schema definitions
- Prepare generated code for pushing to repositories
- Validate generated TypeScript code for common issues

## Setup Instructions

### 1. Install Requirements

```bash
# Create a new directory for the project
uv init swagger-dto-generator
cd swagger-dto-generator

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install dependencies
uv add "mcp[cli]" pydantic pygithub
```

### 2. Configure GitHub Access

Create a `.env` file in your project directory with your GitHub personal access token:

```
GITHUB_TOKEN=your_github_personal_access_token
```

Make sure your token has appropriate permissions for the repositories you plan to access.

### 3. Configure Claude Desktop

Add the MCP server configuration to your Claude desktop settings:

```json
// Add to claude_desktop_config.json
// Location: ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "SpeedUp REST API test automation": {
      "command": "bash",
      "args": [
        "-c",
        "cd /path/to/this-mcp-server-folder && source .venv/bin/activate && mcp run rest_api_taf_helper.py"
      ],
      "env": {
            "GITHUB_TOKEN":"your_github_personal_access_token_with_access_to_taf_repo"
      }  
    }
  }
}
```

Replace `/path/to/swagger-dto-generator` with the actual path to your project directory.

### 4. Start the Server

Restart the Claude desktop app to load the new configuration.

### 5. Test with MCP Inspector (Optional)

For development and testing purposes, you can use the MCP CLI:

```bash
# Run the server in development mode
mcp dev rest_api_taf_helper.py
```

## Usage Guide

Once the server is running, you can use the following tools through Claude (or amother MCP client, e.g. GitHub copilot chat in the VS Code):

1. **Connect to GitHub Repository**:
   ```
   connect_to_repo("organization_name", "repository_name")
   ```

2. **Read Swagger JSON**:
   ```
   read_swagger_json("path/to/swagger/folder", "service_name")
   ```

3. **Generate TypeScript DTOs**:
   ```
   generate_typescript_dtos()
   ```

4. **Inspect Generated Content**:
   ```
   inspect_context()
   ```

5. **Prepare DTOs for Push**:
   ```
   prepare_dto_for_push()
   ```

## Example Workflow

Here's a complete example of how to use this MCP server:

```
1. First, connect to a repository:
   connect_to_repo("my-organization", "api-project")

2. Read the Swagger definition:
   read_swagger_json("api/definitions", "user-service")

3. Generate TypeScript DTOs:
   generate_typescript_dtos()

4. Review the generated content:
   inspect_context("generated_typescript_dto")

5. Prepare the content for pushing to GitHub:
   prepare_dto_for_push()
```

## Troubleshooting

- If you encounter GitHub API rate limits, make sure your token has appropriate scopes
- If generated TypeScript has issues, check the logs for warnings from the validation process
- For connection issues, verify that your GitHub token is valid and has access to the specified repository

## License

[MIT]