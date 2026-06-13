import os
import re

# Define the mapping for replacements
replacements = {
    r'\bWeek\s*2\b': 'Week 22',
    r'\bWeek\s*3\b': 'Week 23',
    r'\bWeek\s*4\b': 'Week 24',
    r'\bW02\b': 'W22',
    r'\bW03\b': 'W23',
    r'\bW2\b': 'W22',
    r'\bW3\b': 'W23',
    r'\bW4\b': 'W24',
}

TEXT_EXTENSIONS = {'.md', '.txt', '.py', '.yml', '.yaml', '.html', '.json', '.sh'}

def update_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        new_content = content
        for pattern, replacement in replacements.items():
            new_content = re.sub(pattern, replacement, new_content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Updated content: {file_path}")
    except Exception as e:
        print(f"Error updating content in {file_path}: {e}")

def rename_file_or_dir(root, name):
    old_path = os.path.join(root, name)
    new_name = name
    
    if 'W22' in new_name: new_name = new_name.replace('W22', 'W22')
    elif 'W22' in new_name: new_name = new_name.replace('W22', 'W22')
    
    if 'W23' in new_name: new_name = new_name.replace('W23', 'W23')
    elif 'W23' in new_name: new_name = new_name.replace('W23', 'W23')
    
    if new_name != name:
        new_path = os.path.join(root, new_name)
        os.rename(old_path, new_path)
        print(f"Renamed: {old_path} -> {new_path}")
        return new_name
    return name

def main():
    print("Starting repository refactor...")
    for root, dirs, files in os.walk('.', topdown=False):
        if '.git' in root.split(os.sep):
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            _, ext = os.path.splitext(file.lower())
            if ext in TEXT_EXTENSIONS:
                update_content(file_path)
        
        for file in files:
            rename_file_or_dir(root, file)
            
        for d in dirs:
            rename_file_or_dir(root, d)

    print("\nRefactor complete!")

if __name__ == "__main__":
    main()