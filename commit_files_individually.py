import subprocess
import sys
import os

def get_changed_files():
    """Get list of all changed files with their status"""
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
                # Get status code (first 2 characters)
                status = line[:2].strip()
                # Get the filename (starting from index 3)
                file_path = line[3:].strip()
                
                # Handle renamed files (they have -> in them)
                if ' -> ' in file_path:
                    old_name, new_name = file_path.split(' -> ')
                    file_path = new_name
                    status = 'R'
                
                # Determine the action based on status code
                if status in ['A', '??']:
                    action = 'Added'
                elif status == 'D':
                    action = 'Removed'
                elif status == 'R':
                    action = 'Renamed'
                elif status == 'M':
                    action = 'Updated'
                else:
                    action = 'Updated'
                
                files.append((file_path, action))
        return files
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}")
        return []

def commit_file(file_path, action, index, total):
    """Commit a single file with smart commit message"""
    try:
        # Get just the filename for the commit message
        filename = os.path.basename(file_path)
        
        # Stage the file
        subprocess.run(['git', 'add', file_path], check=True)
        
        # Create smart commit message
        commit_message = f"{action} {filename}"
        
        # Commit the file
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        print(f"[{index}/{total}] {commit_message}")
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
    
    for index, (file_path, action) in enumerate(changed_files, 1):
        if commit_file(file_path, action, index, total_files):
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
