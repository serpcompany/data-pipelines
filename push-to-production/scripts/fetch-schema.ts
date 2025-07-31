#!/usr/bin/env tsx

import * as fs from 'fs/promises';
import * as path from 'path';

const GITHUB_REPO = 'serpcompany/boxingundefeated.com';
const BRANCH = 'main';
const SCHEMA_PATH = 'server/database';

async function fetchSchemaFiles() {
  console.log('🔍 Fetching schema files from GitHub...\n');

  // First, get the list of files in the schema directory
  const apiUrl = `https://api.github.com/repos/${GITHUB_REPO}/contents/${SCHEMA_PATH}?ref=${BRANCH}`;
  
  const headers: HeadersInit = {
    'Accept': 'application/vnd.github.v3+json',
  };

  // Add token if available (for private repos)
  const token = process.env.GITHUB_TOKEN;
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    const response = await fetch(apiUrl, { headers });
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`Repository or path not found. Is the repo private? You may need to set GITHUB_TOKEN environment variable.`);
      }
      throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
    }

    const files = await response.json();
    
    // Create local schema directory
    const localSchemaDir = path.join(process.cwd(), 'src', 'schema');
    await fs.mkdir(localSchemaDir, { recursive: true });

    // Download each .ts file
    for (const file of files) {
      if (file.name.endsWith('.ts')) {
        console.log(`📥 Downloading ${file.name}...`);
        
        const fileResponse = await fetch(file.download_url);
        const content = await fileResponse.text();
        
        await fs.writeFile(
          path.join(localSchemaDir, file.name),
          content,
          'utf-8'
        );
      }
    }

    console.log('\n✅ Schema files downloaded successfully!');
    console.log(`📁 Saved to: ${localSchemaDir}`);

  } catch (error) {
    console.error('❌ Failed to fetch schema:', error);
    console.error('\n⚠️  Make sure to update GITHUB_REPO in this script!');
    process.exit(1);
  }
}

fetchSchemaFiles();