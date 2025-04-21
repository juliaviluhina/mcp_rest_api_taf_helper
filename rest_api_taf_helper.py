# rest_api_taf_helper.py
import os
from mcp.server.fastmcp import FastMCP
from pydantic import Field

from dotenv import load_dotenv

load_dotenv()

# Configure the MCP server with lifespan
mcp = FastMCP("SpeedUp REST API test automation")

@mcp.prompt()
def generate_typescript_dto(
    repository_name: str = Field(description="The name of repository with test automation framework"),
    service_name: str = Field(description="Service name which is under test implementation")) -> str:
    """
    Prompt to generate TypeScript module with DTOs for each data item used in service with service_name 

    Args:
        repository_name: Name of the repository whete test framework is located
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

    if (repository_name == "" or service_name == ""):
        return "Error: Please provide the repository name and service name."

    return f"""
    You are test automation engineer with expertise in REST API test automation, Swagger, TypeScript. 
    Your task is to analyse the following OpenAPI/Swagger schema definition, and generate TypeScript module with DTOs for each data class mentioned in theshema definition.
    
    
    # Instructions
    * Use 'github' tool to interact with repository: {repository_name}
    * repository already contains example for another service, use it as an template. Example description:
        * service name: {example_service_name}
        * shema for example service is located in the repository in '{path_to_exapmpe_contract}' 
        * module with DTO's for this example service is located in '{path_to_example_dto}'
    * Service name which is under analysis is '{service_name}'
    * If shema for this service is not found in the repository (it should be located in 'serviceContracts/{service_name}.json'), then stop further analysis, inform user about this problem
    * Otherwise, proceed with analysis, use guidelines and example
    * Return result to chat for user's review

    # Follow these guidelines:
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