import os
import re

# Directory containing your model files
MODELS_DIR = r"y:\jordan\EventPhotoUploader\app\models"

# Regex to match relationship definitions
RELATIONSHIP_REGEX = r'(\s+)(\w+):\s*List\["([^"]+)"\]\s*=\s*relationship\((.*?)\)'

# Replacement template
REPLACEMENT_TEMPLATE = r'\1\2: Mapped[List["\3"]] = relationship(\4)'

def update_relationships_in_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Replace relationship definitions with the new syntax
    updated_content = re.sub(RELATIONSHIP_REGEX, REPLACEMENT_TEMPLATE, content)

    # Add necessary imports if not already present
    if "from sqlalchemy.orm import Mapped, relationship" not in updated_content:
        updated_content = updated_content.replace(
            "from sqlmodel import SQLModel, Field",
            "from sqlmodel import SQLModel, Field\nfrom sqlalchemy.orm import Mapped, relationship"
        )

    # Save the updated file only if changes were made
    if content != updated_content:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(updated_content)
        print(f"Updated: {file_path}")
    else:
        print(f"No changes needed: {file_path}")

def update_all_models():
    for root, _, files in os.walk(MODELS_DIR):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                update_relationships_in_file(file_path)

if __name__ == "__main__":
    update_all_models()