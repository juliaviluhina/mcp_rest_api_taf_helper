import os
from mcp.server.fastmcp import FastMCP
from pydantic import Field
from src.github_utils import read_nested_json_section
from src.github_utils import read_text_file_contents
from src.github_utils import get_service_schemas
from dotenv import load_dotenv

load_dotenv()

# Configure the MCP server with lifespan
mcp = FastMCP("SpeedUp REST API test automation")

@mcp.prompt()
def step1_generate_typescript_dto(
    service_name: str = Field(description="Service name which is under test implementation")) -> str:
    """
    Prompt to generate TypeScript module with DTOs for each data item used in service with service_name 

    Args:
        service_name: Service name which is under analysis for DTO generation
        
    Returns:
        Prompt to process this request
    """
    # Assumptions: 
    #     - test framework is built based on specific template, with approved structure
    #     - test framework already contains example for each layer of the test framework
    example_service_name = "wizardWorld"
    path_to_exapmpe_contract = "serviceContracts/wizardWorld.json"
    path_to_example_dto = "src/models/wizardWorld.model.ts"
    owner = 'juliaviluhina'
    repo = 'taf_rest_api_result'
    schema = ''
    example_schema = ''
    if (service_name == ""):
        return "Error: Please provide service name."

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
    </guidelines>
        
    """

if __name__ == "__main__":
    mcp.run()