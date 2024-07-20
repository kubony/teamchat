import os
import fnmatch
import sys

def get_ignore_patterns(file_path):
    patterns = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

def get_gitignore_patterns(base_dir):
    patterns = []
    gitignore_paths = [
        os.path.join(base_dir, '.gitignore'),
        os.path.join(base_dir, 'app', 'frontend', '.gitignore'),
        os.path.join(base_dir, 'ios', '.gitignore'),
        os.path.join(base_dir, 'android', '.gitignore')
    ]
    for gitignore_path in gitignore_paths:
        patterns.extend(get_ignore_patterns(gitignore_path))
    return patterns

def should_include(file_path, patterns):
    for pattern in patterns:
        if pattern.startswith('/'):
            if fnmatch.fnmatch(file_path, pattern):
                return False
            if os.path.isdir(file_path) and fnmatch.fnmatch(file_path + '/', pattern):
                return False
        else:
            if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return False
            if os.path.isdir(file_path) and fnmatch.fnmatch(os.path.basename(file_path) + '/', pattern):
                return False
    return True

def collect_project_files(base_dir='.'):
    script_dir = os.path.abspath(base_dir)
    print(script_dir)
    utils_dir = os.path.join(script_dir, 'tools/data')
    print(utils_dir)
    output_dir = os.path.join(utils_dir, 'scanned_project_files')
    print(output_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    overview_filename = os.path.join(output_dir, 'tree.txt')
    detailed_filename = os.path.join(output_dir, 'codes.txt')
    log_filename = os.path.join(output_dir, 'log.txt')
    additional_ignore_path = os.path.join(utils_dir, 'additional_ignore.txt')

    gitignore_patterns = get_gitignore_patterns(base_dir)
    additional_ignore_patterns = get_ignore_patterns(additional_ignore_path)
    patterns = list(set(gitignore_patterns + additional_ignore_patterns))

    open(overview_filename, 'w').close()
    open(detailed_filename, 'w').close()
    open(log_filename, 'w').close()

    with open(overview_filename, 'a', encoding='utf-8') as overview_file, \
         open(detailed_filename, 'a', encoding='utf-8') as detailed_file, \
         open(log_filename, 'a', encoding='utf-8') as logfile:
         
        for root, dirs, files in os.walk(script_dir):
            if '.git' in root:
                continue
            dirs[:] = [d for d in dirs if should_include(os.path.relpath(os.path.join(root, d), script_dir), patterns)]
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, script_dir)
                
                if should_include(relative_path, patterns):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            detailed_file.write(f"File: {relative_path}\n")
                            detailed_file.write(infile.read())
                            detailed_file.write("\n\n")
                            logfile.write(f"Including file: {relative_path}\n")
                    except UnicodeDecodeError as e:
                        logfile.write(f"Could not read file (encoding issue) {file_path}: {e}\n")
                    except Exception as e:
                        logfile.write(f"Could not read file {file_path}: {e}\n")
                else:
                    logfile.write(f"Excluded by pattern: {relative_path}\n")
        
        for root, dirs, files in os.walk(script_dir):
            if '.git' in root:
                continue
            dirs[:] = [d for d in dirs if should_include(os.path.relpath(os.path.join(root, d), script_dir), patterns)]
            relative_path = os.path.relpath(root, script_dir)
            if should_include(relative_path, patterns):
                overview_file.write(f"Directory: {relative_path}\n")
                overview_file.write("Contains:\n")
                for dir in dirs:
                    overview_file.write(f"- {dir}\n")
                for file in files:
                    file_relative_path = os.path.relpath(os.path.join(root, file), script_dir)
                    if should_include(file_relative_path, patterns):
                        overview_file.write(f"- {file}\n")
                overview_file.write("\n")
            else:
                logfile.write(f"Excluded directory by pattern: {relative_path}\n")

if __name__ == "__main__":
    base_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    collect_project_files(base_dir)