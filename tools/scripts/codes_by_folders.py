import os
import fnmatch
import shutil
from pathlib import Path

def get_gitignore_patterns(base_dir):
    gitignore_path = Path(base_dir) / '.gitignore'
    patterns = []
    if gitignore_path.exists():
        with open(gitignore_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if not line.startswith('/'):
                        line = f'**/{line}'
                    patterns.append(line)
    return patterns

def is_ignored(path, base_path, patterns):
    rel_path = path.relative_to(base_path)
    for pattern in patterns:
        if fnmatch.fnmatch(str(rel_path), pattern) or fnmatch.fnmatch(str(rel_path) + '/', pattern):
            return True
    return False

def is_code_file(file_path):
    code_extensions = ['.py', '.dart', '.js', '.ts']  # 필요한 파일 확장자를 추가하세요
    return file_path.suffix in code_extensions

def combine_code_files(source_dir, dest_dir):
    source_path = Path(source_dir).resolve()
    dest_path = Path(dest_dir).resolve()
    
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory '{source_path}' does not exist.")
    
    dest_path.mkdir(parents=True, exist_ok=True)
    
    ignore_patterns = get_gitignore_patterns(source_path)
    
    all_included_files = []

    # 먼저 root 폴더의 주요 파일들을 처리합니다
    for file in source_path.glob('*'):
        if file.is_file() and is_code_file(file) and not is_ignored(file, source_path, ignore_patterns):
            shutil.copy2(file, dest_path)
            all_included_files.append(file.name)

    for root, dirs, files in os.walk(source_path):
        rel_path = Path(root).relative_to(source_path)
        current_path = source_path / rel_path
        
        dirs[:] = [d for d in dirs if not is_ignored(current_path / d, source_path, ignore_patterns)]
        
        if not is_ignored(current_path, source_path, ignore_patterns):
            (dest_path / rel_path).mkdir(parents=True, exist_ok=True)
            
            combined_code = f"Combined code for {rel_path}\n\n"
            included_files = []
            
            for file in files:
                file_path = current_path / file
                if is_code_file(file_path) and not is_ignored(file_path, source_path, ignore_patterns):
                    rel_file_path = file_path.relative_to(source_path)
                    included_files.append(str(rel_file_path))
                    all_included_files.append(str(rel_file_path))
                    combined_code += f"File: {rel_file_path}\n"
                    with open(file_path, 'r', encoding='utf-8') as f:
                        combined_code += f.read()
                    combined_code += "\n\n"
            
            # Write combined code
            with open(dest_path / rel_path / 'combined_code.txt', 'w', encoding='utf-8') as f:
                f.write(combined_code)
            
            # Write list of included files for this directory
            with open(dest_path / rel_path / 'included_files.txt', 'w', encoding='utf-8') as f:
                for file in included_files:
                    f.write(f"{file}\n")

    # Write list of all included files in the root directory
    with open(dest_path / 'all_included_files.txt', 'w', encoding='utf-8') as f:
        for file in sorted(all_included_files):
            f.write(f"{file}\n")

    print(f"Directory structure and combined code created in '{dest_path}'")

# 실행
if __name__ == "__main__":
    source_directory = "."  # 현재 디렉토리를 root로 설정
    destination_directory = "docs_gen"  # docs_gen 폴더 경로
    
    combine_code_files(source_directory, destination_directory)