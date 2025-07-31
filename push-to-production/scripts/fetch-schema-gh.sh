#!/bin/bash

# Fetch schema files using GitHub CLI (gh)

REPO="serpcompany/boxingundefeated.com"
BRANCH="main"
SCHEMA_PATH="server/database/schema"
LOCAL_DIR="src/schema"

echo "🔍 Fetching schema files using GitHub CLI..."

# Create local schema directory
mkdir -p "$LOCAL_DIR"

# List all files in the schema directory
echo "📂 Getting file list from $REPO/$SCHEMA_PATH..."
FILES=$(gh api "repos/$REPO/contents/$SCHEMA_PATH?ref=$BRANCH" --jq '.[] | select(.type=="file") | .name')

# Download each file
for file in $FILES; do
    if [[ $file == *.ts ]]; then
        echo "📥 Downloading $file..."
        gh api "repos/$REPO/contents/$SCHEMA_PATH/$file?ref=$BRANCH" \
            --jq '.content' | base64 -d > "$LOCAL_DIR/$file"
    fi
done

echo ""
echo "✅ Schema files downloaded successfully!"
echo "📁 Files in $LOCAL_DIR:"
ls -la "$LOCAL_DIR"