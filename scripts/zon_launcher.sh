#!/usr/bin/env bash

# [ ⌐■_■] <( Locating the source code... )
# Detects the repository root relative to this script
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ "$1" == "update" ]; then
    echo "[ ⌐■_■] <( Checking for updates on GitHub... )"
    
    # 1. Fetch metadata without touching local files
    git -C "$REPO_DIR" fetch origin main -q

    # 2. Get commit messages
    REMOTE_MSG=$(git -C "$REPO_DIR" log -1 origin/main --pretty=format:%s)
    LOCAL_MSG=$(git -C "$REPO_DIR" log -1 --pretty=format:%s)

    # 3. Check stability flags
    if [[ "$REMOTE_MSG" == *"[NOSTABLE]"* ]]; then
        echo "[ ⌐■_■] <( Error: Remote version is marked as [NOSTABLE]. )"
        echo "[ ⌐■_■] <( Update aborted to keep your system safe. )"
        exit 1
    fi

    # 4. Check if already updated
    if [[ "$REMOTE_MSG" == "$LOCAL_MSG" ]]; then
        echo "[ ⌐■_■] <( You are already up to date! Version: $LOCAL_MSG )"
        exit 0
    fi

    # 5. Perform the update
    echo "[ ⌐■_■] <( New version found: $REMOTE_MSG )"
    echo "[ ⌐■_■] <( Updating now... )"
    
    git -C "$REPO_DIR" reset --hard origin/main -q
    git -C "$REPO_DIR" clean -fd -q
    
    echo "[ ⌐■_■] <( Update complete! You are now on $REMOTE_MSG )"
    exit 0
fi

# [ ⌐■_■] <( Running Zonetic Compiler... )
# Pass all arguments to the Python main.py
python3 "$REPO_DIR/src/zonc/main.py" "$@"
