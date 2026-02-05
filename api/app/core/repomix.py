"""
Repomix: The 'Eyes' of the Agent.
This module generates a script to be executed INSIDE the sandbox.
It walks the repository, ignores junk (node_modules, etc.), and packs 
relevant code into a format Gemini can understand.
"""

def get_repomix_script() -> str:
    return """
import os

# Configuration: Files/Dirs to strictly ignore to save tokens
IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', 'venv', 'env', 
    '.next', 'dist', 'build', 'coverage', '.pytest_cache'
}
IGNORE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.mp4', 
    '.zip', '.tar', '.gz', '.pyc', '.lock', '.pdf'
}
IGNORE_FILES = {
    'package-lock.json', 'yarn.lock', 'poetry.lock', 'repomix-output.xml'
}

def is_text_file(filepath):
    # Simple heuristic to avoid reading binary files
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.read(1024)
        return True
    except (UnicodeDecodeError, IOError):
        return False

def pack_repo(root_dir="/repo"):
    print("<repository_context>")
    
    for root, dirs, files in os.walk(root_dir):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            
            _, ext = os.path.splitext(file)
            if ext.lower() in IGNORE_EXTENSIONS:
                continue
                
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, root_dir)
            
            if is_text_file(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    print(f'<file path="{rel_path}">')
                    print(content)
                    print('</file>')
                except Exception as e:
                    print(f'')

    print("</repository_context>")

if __name__ == "__main__":
    pack_repo()
"""