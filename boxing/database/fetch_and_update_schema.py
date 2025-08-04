#!/usr/bin/env python3
"""
Fetch schema files from GitHub and update local schema for Drizzle.
"""

import os
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class SchemaSync:
    """Sync schema files from production GitHub repository."""
    
    def __init__(self):
        self.repo = os.getenv('GITHUB_MAIN_PROJECT_REPO', 'serpcompany/boxingundefeated.com')
        self.branch = 'staging'  # staging branch = production-preview
        self.github_token = os.getenv('GITHUB_PAT')
        self.schema_dir = Path(__file__).parent / "drizzle" / "schema"
        
    def fetch_file(self, file_path: str) -> Optional[str]:
        """Fetch a file from GitHub."""
        url = f"https://raw.githubusercontent.com/{self.repo}/{self.branch}/{file_path}"
        
        headers = {}
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
            
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {file_path}: {e}")
            return None
    
    def sync_schema_files(self):
        """Fetch and save schema files from GitHub."""
        logger.info(f"Syncing schema from {self.repo}@{self.branch}")
        
        # Schema files to fetch
        schema_files = [
            'boxers.ts',
            'boxerBouts.ts', 
            'divisions.ts',
            'index.ts'
        ]
        
        # Ensure schema directory exists
        self.schema_dir.mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        for file_name in schema_files:
            remote_path = f"server/db/schema/{file_name}"
            content = self.fetch_file(remote_path)
            
            if content:
                local_path = self.schema_dir / file_name
                with open(local_path, 'w') as f:
                    f.write(content)
                logger.info(f"Updated {file_name}")
                success_count += 1
            else:
                logger.error(f"Failed to fetch {file_name}")
        
        logger.info(f"Synced {success_count}/{len(schema_files)} schema files")
        return success_count == len(schema_files)
    
    def sync_migrations(self):
        """Fetch migration files from GitHub."""
        logger.info(f"Syncing migrations from {self.repo}@{self.branch}")
        
        migrations_dir = Path(__file__).parent / "drizzle" / "migrations"
        migrations_dir.mkdir(parents=True, exist_ok=True)
        meta_dir = migrations_dir / "meta"
        meta_dir.mkdir(parents=True, exist_ok=True)
        
        # Migration files to fetch
        migration_files = [
            '0000_small_norman_osborn.sql',
            '0001_melodic_sentinel.sql',
            '0002_sweet_argent.sql',
            '0003_worried_songbird.sql'
        ]
        
        success_count = 0
        for file_name in migration_files:
            remote_path = f"server/db/migrations/{file_name}"
            content = self.fetch_file(remote_path)
            
            if content:
                # Save with our naming convention
                local_name = file_name.replace('_small_norman_osborn', '_initial_schema') \
                                    .replace('_melodic_sentinel', '_add_unique_constraints') \
                                    .replace('_sweet_argent', '_add_division_shortname') \
                                    .replace('_worried_songbird', '_add_unique_boxer_bout')
                
                local_path = migrations_dir / local_name
                with open(local_path, 'w') as f:
                    f.write(content)
                logger.info(f"Updated migration: {local_name}")
                success_count += 1
        
        # Also fetch and update the journal
        journal_content = self.fetch_file("server/db/migrations/meta/_journal.json")
        if journal_content:
            import json
            journal = json.loads(journal_content)
            
            # Update the tags to match our naming
            for entry in journal.get('entries', []):
                if entry['tag'] == '0000_small_norman_osborn':
                    entry['tag'] = '0000_initial_schema'
                elif entry['tag'] == '0001_melodic_sentinel':
                    entry['tag'] = '0001_add_unique_constraints'
                elif entry['tag'] == '0002_sweet_argent':
                    entry['tag'] = '0002_add_division_shortname'
                elif entry['tag'] == '0003_worried_songbird':
                    entry['tag'] = '0003_add_unique_boxer_bout'
            
            # Save updated journal
            journal_path = meta_dir / "_journal.json"
            with open(journal_path, 'w') as f:
                json.dump(journal, f, indent=2)
            logger.info("Updated migration journal")
                
        return success_count == len(migration_files)


def sync_schema_from_github():
    """Sync schema from GitHub before running Drizzle commands."""
    sync = SchemaSync()
    schema_success = sync.sync_schema_files()
    migrations_success = sync.sync_migrations()
    return schema_success and migrations_success


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = sync_schema_from_github()
    if success:
        print("Schema sync completed successfully")
    else:
        print("Schema sync failed")
        exit(1)