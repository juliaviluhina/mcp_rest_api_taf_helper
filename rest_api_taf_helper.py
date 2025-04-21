import os
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from src.github_utils import read_nested_json_section
from src.github_utils import read_text_file_contents
from src.github_utils import get_service_schemas
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()

@dataclass
class AppContext:
    repository_owner: str
    repository_name: str
    service_name: str

mcp_server_name = "SpeedUp REST API test automation"
app_context: AppContext = AppContext(
        repository_owner = os.environ.get("GITHUB_REPO_OWNER"),
        repository_name = os.environ.get("GITHUB_REPO_NAME"),
        service_name = '')

# Configure the MCP server with lifespan
mcp = FastMCP(mcp_server_name)

@mcp.resource("config://context")
def get_config() -> str:
    """Repository owner, repository name, service name"""
    return f"MCP server works with context: {app_context}"

@mcp.tool()
def configure_flow(repository_owner: str, repository_name: str, service_name:str) -> str:
    """
    Tool that helps with flow configuration: user can configure repository name, owner and service name
    
    Args:
        repository_owner: Owner name of repository which is used for user's requests
        repository_name: repository name which is used for user's requests
        service_name: service name which is used for user's requests

    Returns:
        updated configuration    
    """
    app_context.repository_owner = repository_owner
    app_context.repository_name = repository_name
    app_context.service_name = service_name

    return f"MCP server works with context: {app_context}"   

@mcp.tool()
def generate_typescript_dto() -> str:
    """
    Tool that returns prompt for further execution, to generate TypeScript module with DTOs
    
    Returns:
        prompt for further run    
    """    
    return run_step1_generate_typescript_dto()

@mcp.prompt()
def step0_configure_flow(
    repository_owner: str = Field(description="Owner name of GitHub repository which is used"),
    repository_name: str = Field(description="Repository name of GitHub repository which is used"),
    service_name: str = Field(description="Service name which is under test implementation")) -> str:
    """
    Prompt to store configuration for this MCP server
    
    Args:
        repository_owner: Owner name of repository which is used for user's requests
        repository_name: repository name which is used for user's requests
        service_name: service name which is used for user's requests
        
    Returns:
        Prompt to process this request
    """

    return f"""
    Use 'configure_flow' tool of '{mcp_server_name}' MCP server to set configuration

        repository_owner = {repository_owner}
        repository_name = {repository_name}
        service_name: {service_name}
        
    """

@mcp.prompt()
def step1_generate_typescript_dto() -> str:
    """
    Prompt to generate TypeScript module with DTOs for each data item used in service with service_name 
    
    Returns:
        Prompt to process this request
    """
    return run_step1_generate_typescript_dto()

def run_step1_generate_typescript_dto() -> str:
    """
    Prompt to generate TypeScript module with DTOs for each data item used in service with service_name 
    
    Returns:
        Prompt to process this request
    """
    # Assumptions: 
    #     - test framework is built based on specific template, with approved structure
    #     - test framework already contains example for each layer of the test framework
    service_name = app_context.service_name
    owner = app_context.repository_owner
    repo = app_context.repository_name
    if (repo == ""):
        return "Error: Repository name is not defined. Use step0_configure_flow to configure flow."
    if (owner == ""):
        return "Error: Repository owner is not defined. Use step0_configure_flow to configure flow."
    if (service_name == ""):
        return "Error: Service name is not defined. Use step0_configure_flow to configure flow."

    example_service_name = "wizardWorld"
    path_to_exapmpe_contract = "serviceContracts/wizardWorld.json"
    path_to_example_dto = "src/models/wizardWorld.model.ts"

    schema = ''
    example_schema = ''

    try:
        schema = get_service_schemas(owner, repo, service_name)
    except Exception as e:
        return f"Error reading serviceContracts/{service_name}.json: {str(e)}"  
                     
    try:
        example_schema = read_nested_json_section(owner, repo,  path_to_exapmpe_contract, ['components', 'schemas'])
    except Exception as e:
        return f"Error reading {path_to_exapmpe_contract}: {str(e)}" 

    try:
        example_dto_module = read_text_file_contents(owner, repo,  path_to_example_dto)
    except Exception as e:
        return f"Error reading {path_to_example_dto}: {str(e)}"     

    return f"""
    You are test automation engineer with expertise in REST API test automation, Swagger, TypeScript. 
    Your task is to analyse the following OpenAPI/Swagger schema definition, and generate TypeScript module with DTOs for each data class mentioned in the schema definition.
    
    <schema_for_analysis>
    {schema}
    </schema_for_analysis>
    
    Use example and guidelines below to generate Typescript module
    <example_schema>
    {example_schema}
    </example_schema>

    <example_dto_module>
    {example_dto_module}
    <example_dto_module>

    <guidelines>
    1. Create a class with appropriate properties based on the schema
    2. Use proper TypeScript types based on the schema types
    3. Include JSDoc comments for properties using descriptions from the schema
    4. Handle required vs optional properties correctly (use ? for optional properties)
    5. Handle references to other schemas
    6. Handle arrays, enums, and nested objects appropriately
    7. Return ONLY the TypeScript code, nothing else
    8. Return result to chat for user's review
    9. Ask whether user would like to review and adjust module, or push changes to repository
    10. For further push to repository, strictly follow steps: 
        10.1. use 'github' tool, 
        10.2. for repository '{owner}/{repo}, 
        10.3. create branch dto_{service_name}, 
        10.4. store prepared TypeScript module as src/models/{service_name}.model.ts
        10.5. raise PR
        10.6. inform user about result
    </guidelines>
        
    """


if __name__ == "__main__":
    mcp.run()