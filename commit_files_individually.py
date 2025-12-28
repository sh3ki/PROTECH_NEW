import subprocess
import sys

def get_changed_files():
    """Get list of all changed files"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        files = []
        for line in result.stdout.strip().split('\n'):
            if line:
                # Remove the status indicators (first 3 characters) and get the filename
                file_path = line[3:].strip()
                # Handle renamed files (they have -> in them)
                if ' -> ' in file_path:
                    file_path = file_path.split(' -> ')[1]
                files.append(file_path)
        return files
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []

def commit_file(file_path, index, total):
    """Commit a single file"""
    try:
        # Stage the file
        subprocess.run(['git', 'add', file_path], check=True)
        
        # Commit the file
        subprocess.run(['git', 'commit', '-m', 'commit'], check=True)
        
        print(f"[{index}/{total}] Committed: {file_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[{index}/{total}] Error committing {file_path}: {e}")
        return False

def main():
    print("Getting list of changed files...")
    changed_files = get_changed_files()
    
    if not changed_files:
        print("No changed files found!")
        return
    
    total_files = len(changed_files)
    print(f"\nFound {total_files} changed files.")
    print("Starting to commit each file individually...\n")
    
    successful = 0
    failed = 0
    
    for index, file_path in enumerate(changed_files, 1):
        if commit_file(file_path, index, total_files):
            successful += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Commit process completed!")
    print(f"Total files: {total_files}")
    print(f"Successfully committed: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
