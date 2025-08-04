#!/usr/bin/env python3
"""
Validate HTML files and move from pending to validated directory.
This implements Step 2 of the pipeline flow.
"""

import sys
from pathlib import Path
import shutil
import logging
from typing import Tuple, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from boxing.utils.config import PENDING_HTML_DIR, VALIDATED_HTML_DIR, LOG_DIR
from boxing.validators import (
    blank_page,
    error_page,
    login_page,
    rate_limit,
    file_size
)
from boxing.validators.page import boxer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'html_validation.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def validate_html_file(file_path: Path) -> Tuple[bool, str]:
    """
    Validate a single HTML file using all validators.
    Returns (is_valid, reason).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check file size first
        if not file_size.validate(content):
            return False, "File too small"
        
        # Check for error pages
        if not error_page.validate(content):
            return False, "Error page detected"
        
        # Check for login page
        if not login_page.validate(content):
            return False, "Login page detected"
        
        # Check for rate limiting
        if not rate_limit.validate(content):
            return False, "Rate limit page detected"
        
        # Check for blank page
        is_valid, message = blank_page.validate(content)
        if not is_valid:
            return False, f"Blank page: {message}"
        
        # Check if it's a valid boxer page
        if not boxer.validate(content):
            return False, "Not a valid boxer page"
        
        return True, "Valid"
        
    except Exception as e:
        return False, f"Error reading file: {e}"


def validate_all_pending(limit: int = None) -> Dict:
    """Validate all pending HTML files and move valid ones to validated directory."""
    
    # Ensure validated directory exists
    VALIDATED_HTML_DIR.mkdir(parents=True, exist_ok=True)
    
    # Get pending files
    pending_files = list(PENDING_HTML_DIR.glob('*.html'))
    
    if limit:
        pending_files = pending_files[:limit]
    
    logger.info(f"Found {len(pending_files)} pending HTML files to validate")
    
    stats = {
        'total': len(pending_files),
        'valid': 0,
        'invalid': 0,
        'errors': []
    }
    
    for file_path in pending_files:
        logger.info(f"Validating {file_path.name}")
        
        is_valid, reason = validate_html_file(file_path)
        
        if is_valid:
            # Move to validated directory
            dest_path = VALIDATED_HTML_DIR / file_path.name
            shutil.move(str(file_path), str(dest_path))
            logger.info(f"✓ Moved {file_path.name} to validated")
            stats['valid'] += 1
        else:
            logger.warning(f"✗ Invalid: {file_path.name} - {reason}")
            stats['invalid'] += 1
            stats['errors'].append({
                'file': file_path.name,
                'reason': reason
            })
    
    return stats


def main():
    """Run HTML validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate HTML files')
    parser.add_argument('--limit', type=int, help='Limit number of files to validate')
    
    args = parser.parse_args()
    
    logger.info("Starting HTML validation")
    stats = validate_all_pending(limit=args.limit)
    
    logger.info(f"\nValidation complete:")
    logger.info(f"  Total files: {stats['total']}")
    logger.info(f"  Valid: {stats['valid']}")
    logger.info(f"  Invalid: {stats['invalid']}")
    
    if stats['errors']:
        logger.info(f"\nInvalid files:")
        for error in stats['errors'][:10]:  # Show first 10
            logger.info(f"  - {error['file']}: {error['reason']}")
        
        if len(stats['errors']) > 10:
            logger.info(f"  ... and {len(stats['errors']) - 10} more")
    
    return 0 if stats['invalid'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())