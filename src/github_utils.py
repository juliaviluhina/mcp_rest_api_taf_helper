import base64
from github import Github
import json
from typing import Union, Dict, Any
from dotenv import load_dotenv
import os

load_dotenv()

class GitHubJsonReaderError(Exception):
    def __init__(self, message):
        super().__init__(message)

class JsonSectionNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)

class GitHubFileReaderError(Exception):
    def __init__(self, message):
        super().__init__(message)                  

def read_nested_json_section(
    owner: str, 
    repo: str, 
    file_path: str, 
    section_path: list[str]
) -> Union[Dict[str, Any], Any, None]:
    """
    Read a nested section from a JSON file in a GitHub repository.
    :param owner: Repository owner's username
    :param repo: Repository name
    :param file_path: Path to the JSON file in the repository
    :param section_path: List of nested keys to navigate to the desired section
                         E.g., ['components', 'schemas'] to get the 'schemas' section
    :return: Requested nested section of the JSON
    """
    # Use GitHub token from environment variable
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GitHub token not found in environment variables")

    try:
        with Github(github_token) as g:
            
            # Get the repository
            repository = g.get_repo(f"{owner}/{repo}")
            
            # Get the file contents
            file_contents = repository.get_contents(file_path)
            
            # Decode the file content
            file_content_decoded = base64.b64decode(file_contents.content).decode('utf-8')
            
            # Parse the JSON
            json_data = json.loads(file_content_decoded)
            
            # Navigate through nested sections
            current_section = json_data
            for key in section_path:
                if isinstance(current_section, dict):
                    current_section = current_section.get(key)
                else:
                    raise JsonSectionNotFoundError(f"Cannot navigate to {key}. Current section is not a dictionary. section path {section_path}, file path {file_path}")
                
                if current_section is None:
                    raise JsonSectionNotFoundError(f"Section '{key}' not found. section path {section_path}, file path {file_path}")
            
            return current_section
    
    except Exception as e:
        raise GitHubJsonReaderError(f"An error occurred: {e}. section path {section_path}, file path {file_path}")

def get_service_schemas(owner, repo, service_name):
    schema1 = ''
    schema2 = ''
    error1 = ''
    error2 = ''

    try:
        schema1 = read_nested_json_section(owner, repo, f"serviceContracts/{service_name}.json", ['components', 'schemas'])
    except Exception as e:
        error1 = f"Error reading serviceContracts/{service_name}.json (components/schemas): {str(e)}"  
    
    if not schema1:
        try:
            schema2 = read_nested_json_section(owner, repo, f"serviceContracts/{service_name}.json", ['definitions'])
        except Exception as e:
            error2 = f"Error reading serviceContracts/{service_name}.json (definitions): {str(e)}"    
    
    if not schema1 and not schema2:
        raise  GitHubJsonReaderError(f"Errors: {error1}, {error2}")
    
    return schema1 or schema2  

def read_text_file_contents(
    owner: str, 
    repo: str, 
    file_path: str
) -> str:
    """
    Read the full contents of a text file from a GitHub repository.
    
    :param owner: Repository owner's username
    :param repo: Repository name
    :param file_path: Path to the text file in the repository
    :return: Full contents of the text file as a string
    :raises GitHubFileReaderError: If there are issues reading the file
    """
    # Use GitHub token from environment variable
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GitHub token not found in environment variables")

    try:
        # Use context manager for GitHub client
        with Github(github_token) as g:
            repository = g.get_repo(f"{owner}/{repo}")
            file_contents = repository.get_contents(file_path)
            file_content_decoded = base64.b64decode(file_contents.content).decode('utf-8')
          
            return file_content_decoded
    
    except Exception as e:
        raise GitHubFileReaderError(f"Error reading file: {e}. file path {file_path}")

