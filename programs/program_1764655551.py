__PROGRAM__ = {
    "name": "ProjectGenerator",
    "version": "1.0",
    "description": "Generates a complete Python project structure with multiple files.",
    "params": [
        {"key": "project_name", "label": "Project Name", "type": "str", "required": True, "placeholder": "MyProject"},
        {"key": "add_comments", "label": "Add Comments", "type": "bool", "required": True, "default": False},
        {"key": "lightweight", "label": "Lightweight Version", "type": "bool", "required": True, "default": False},
        {"key": "model_settings", "label": "Model Settings", "type": "list[str]", "required": True, "choices": ["ModelA", "ModelB", "ModelC"], "placeholder": "Select models"},
        {"key": "folder_structure", "label": "Folder Structure", "type": "select", "required": True, "choices": ["flat", "standard"], "placeholder": "Choose structure"}
    ],
    "kind": "project_generator"
}

def run(params: dict) -> dict:
    """Generates a dictionary mapping file names to their corresponding source code."""
    if not params or not isinstance(params, dict):
        return {}

    project_name = params.get("project_name", "DefaultProject")
    add_comments = params.get("add_comments", False)
    lightweight = params.get("lightweight", False)
    model_settings = params.get("model_settings", [])
    folder_structure = params.get("folder_structure", "flat")

    files = {
        "main.py": generate_main_code(project_name, add_comments),
        "registry.py": generate_registry_code(add_comments),
        "ai_codegen.py": generate_ai_codegen_code(lightweight, add_comments),
        "config.py": generate_config_code()
    }

    if folder_structure == "standard":
        # Here you could modify the file structure if needed
        pass

    return files

def generate_main_code(project_name: str, add_comments: bool) -> str:
    """Generates the main.py code."""
    comments = "# Main entry point for the project\n" if add_comments else ""
    return f"{comments}if __name__ == '__main__':\n    print('Welcome to {project_name}!')\n"

def generate_registry_code(add_comments: bool) -> str:
    """Generates the registry.py code."""
    comments = "# Registry for managing project components\n" if add_comments else ""
    return f"{comments}class Registry:\n    pass\n"

def generate_ai_codegen_code(lightweight: bool, add_comments: bool) -> str:
    """Generates the ai_codegen.py code."""
    comments = "# AI Code Generation Module\n" if add_comments else ""
    mode = "lightweight" if lightweight else "full"
    return f"{comments}def generate_code():\n    return 'Code generated in {mode} mode'\n"

def generate_config_code() -> str:
    """Generates the config.py code."""
    return 'OPENAI_API_KEY = ""  # Set your API key here\n'