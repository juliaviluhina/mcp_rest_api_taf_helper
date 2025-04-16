# rest_api_taf_helper.py
import os
from dataclasses import dataclass
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Optional, Dict, Any
import json
import httpx

from github import Github, Repository
from mcp.server.fastmcp import FastMCP, Context
from prompt_executor import PromptExecutor

from dotenv import load_dotenv

load_dotenv()

@dataclass
class AppContext:
    github_client: Github
    prompt_executor: PromptExecutor 
    repo: Optional[Repository.Repository] = None
    swagger_json: Optional[Dict[str, Any]] = None 
    service_name: Optional[str] = None
    generated_typescript_dto: Optional[Dict[str, str]] = None 

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Initialize GitHub and Brave Search connections"""
    # Get GitHub token from environment
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    
    # Initialize GitHub client
    github_client = Github(github_token)
    # Initialize prompt executor
    prompt_executor = PromptExecutor()
    
    # Create and return the context
    context = AppContext(
        github_client=github_client,
        prompt_executor=prompt_executor
    )
    try:
        yield context
    finally:
        # Cleanup
        github_client.close()

# Configure the MCP server with lifespan
mcp = FastMCP("SpeedUp REST API test automation", 
              lifespan=app_lifespan, 
              dependencies=["pygithub", "httpx", "anthropic"])

# Repository connection tool
@mcp.tool()
async def connect_to_repo(ctx: Context, owner: str, repo_name: str) -> str:
    """
    Connect to a GitHub repository.
    
    Args:
        owner: GitHub username or organization
        repo_name: Repository name
    """
    app_ctx = ctx.request_context.lifespan_context
    
    try:
        repo = app_ctx.github_client.get_repo(f"{owner}/{repo_name}")
        app_ctx.repo = repo
        return f"Connected to {owner}/{repo_name}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def read_swagger_json(ctx: Context, folder_path: str, service_name: str) -> str:  # Note: return type is str
    """
    Read and parse a Swagger/OpenAPI JSON file from a specific folder in the repository.
    Store the parsed JSON in the context for later use.
    Validate the Swagger/OpenAPI contract.
    If the file is not found or is invalid, return an error message.
    
    Args:
        folder_path: path to folder in the GitHub reposiory
        service_name: Service name which swagger json file belongs to

    Returns:
        str: Success message or error message
    """
    try:
        # Validate repository connection
        app_ctx = ctx.request_context.lifespan_context
        if not app_ctx.repo:
            return "Error: No repository connected. Use connect_to_repo first."
        
        # Construct full file path
        full_file_path = f"{folder_path.rstrip('/')}/{service_name}.json"
        
        # Log the file reading attempt
        await ctx.info(f"Attempting to read Swagger JSON from: {full_file_path}")
        
        # Retrieve file contents
        try:
            content_file = app_ctx.repo.get_contents(full_file_path)
        except Exception:
            return f"Error: Could not retrieve file: {full_file_path}"
        
        # Verify it's a file, not a directory
        if isinstance(content_file, list):
            return f"Error: {full_file_path} is a directory, not a file"
        
        # Decode file content
        try:
            file_content = content_file.decoded_content.decode('utf-8')
        except UnicodeDecodeError:
            return f"Error: Unable to decode file content at {full_file_path}"
        
        # Parse JSON
        try:
            swagger_json = json.loads(file_content)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON in file {full_file_path}"
        
        # Validate Swagger/OpenAPI contract
        if not ('swagger' in swagger_json or 'openapi' in swagger_json):
            return f"Error: Invalid Swagger/OpenAPI definition at {full_file_path}"
        
        # Store the swagger json in context
        app_ctx.swagger_json = swagger_json
        app_ctx.service_name = service_name
        
        return "Swagger JSON is successfully found and stored to context"
    
    except Exception as e:
        # Catch-all for any unexpected errors
        await ctx.error(f"Unexpected error reading Swagger JSON: {str(e)}")
        return f"Error: Unexpected error - {str(e)}"


@mcp.tool()
async def generate_typescript_dtos(ctx: Context) -> str:
    """
    Generate TypeScript DTO classes based on previously retrieved Swagger JSON, using prompts
    Generate path to the TypeScript DTO module, which will be used in the codebase
    Store the generated DTOs and path in the context for later use.
    
    Args:
        ctx: Context object
    
    Returns:
        str: Status message or error description
    """
    try:
        # Retrieve Swagger JSON from context
        app_ctx = ctx.request_context.lifespan_context

        if not app_ctx.swagger_json:
            return "Error: No swagger JSON read. Use read_swagger_json first."
        if not app_ctx.service_name:
            return "Error: No service name stored for flow. Use read_swagger_json first."    
        
        swagger_json = app_ctx.swagger_json
        
        # Determine schema location based on Swagger/OpenAPI version
        if 'components' in swagger_json and 'schemas' in swagger_json['components']:
            # OpenAPI 3.x
            schemas = swagger_json['components']['schemas']
        elif 'definitions' in swagger_json:
            # Swagger 2.0
            schemas = swagger_json['definitions']
        else:
            return "Error: No schemas found in the Swagger/OpenAPI specification"
        
        # Prepare to collect generated DTOs
        generated_dtos = []
        
        # Generate DTO for each schema using prompt
        for schema_name, schema_def in schemas.items():
            # Call the MCP prompt to generate the TypeScript DTO
            dto_content = await app_ctx.prompt_executor.execute_prompt(generate_typescript_dto(schema_name, json.dumps(schema_def, indent=2)))
            
            # Store the generated DTO
            generated_dtos.append({
                'name': schema_name,
                'content': dto_content
            })
        
        # Combine DTOs into a single module
        typescript_module = f"// Generated TypeScript DTOs for {app_ctx.service_name}\n\n"
        typescript_module += "\n".join(dto['content'] for dto in generated_dtos)
        file_path = f"/src/models/{app_ctx.service_name}.model.ts"
        
        # Store information in context
        app_ctx.generated_typescript_dto = {
            'content': typescript_module,
            'path': file_path
        }
        
        return f"Successfully generated TypeScript DTO module for further actions: {file_path}"
    
    except Exception as e:
        return f"Error generating TypeScript DTOs: {str(e)}"

@mcp.tool()
async def inspect_context(ctx: Context, attribute: Optional[str] = None) -> str:
    """
    Inspect the current application context.
    
    Args:
        attribute: Optional specific attribute to inspect
    
    Returns:
        str: Formatted context information
    """
    app_ctx = ctx.request_context.lifespan_context
    
    if not attribute:
        # If no specific attribute, return all available attributes
        context_info = {}
        for attr_name in ['repo', 'swagger_json', 'service_name', 'generated_typescript_dto']:
            value = getattr(app_ctx, attr_name, None)
            if value is not None:
                context_info[attr_name] = (
                    str(type(value)) if not isinstance(value, (dict, str, int, list)) 
                    else value
                )
        
        return json.dumps(context_info, indent=2)
    
    # If specific attribute is requested
    try:
        value = getattr(app_ctx, attribute)
        return json.dumps(value, indent=2) if value is not None else "Attribute is None"
    except AttributeError:
        return f"Error: Attribute '{attribute}' not found in context"      

@mcp.tool()
async def prepare_dto_for_push(ctx: Context) -> dict:
    """
    Prepare context for DTO push
    
    Returns:
        dict: Context information for DTO push
    """
    try:
        app_ctx = ctx.request_context.lifespan_context
        
        # Validate required context
        if not app_ctx.repo:
            return {"error": "No repository connected"}
        if not app_ctx.generated_typescript_dto:
            return {"error": "No generated DTO found"}
        
        return {
            "repo_full_name": f"{app_ctx.repo.owner.login}/{app_ctx.repo.name}",
            "service_name": app_ctx.service_name,
            "file_path": app_ctx.generated_typescript_dto['path'],
            "file_content": app_ctx.generated_typescript_dto['content'],
            "default_branch": app_ctx.repo.default_branch
        }
    
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.prompt()
def generate_typescript_dto(schema_name: str, schema_definition: str) -> str:
    """
    Generate a TypeScript DTO class for a given schema.
    
    Args:
        schema_name: Name of the schema
        schema_definition: Schema definition from Swagger/OpenAPI as JSON string
        
    Returns:
        TypeScript class definition as a string
    """
    return f"""
    You are a TypeScript expert. Your task is to convert the following OpenAPI/Swagger schema definition into a TypeScript DTO class.
    
    Schema Name: {schema_name}
    Schema Definition:
    ```json
    {schema_definition}
    ```
    
    Follow these guidelines:
    1. Create a class with appropriate properties based on the schema
    2. Use proper TypeScript types based on the schema types
    3. Include JSDoc comments for properties using descriptions from the schema
    4. Handle required vs optional properties correctly (use ? for optional properties)
    5. Handle references to other schemas
    6. Handle arrays, enums, and nested objects appropriately
    7. Return ONLY the TypeScript code, nothing else
    
    The output should be a TypeScript class that represents this schema.
    """

if __name__ == "__main__":
    mcp.run()