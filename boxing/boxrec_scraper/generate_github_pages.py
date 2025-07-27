#!/usr/bin/env python3
"""Generate GitHub Pages site from boxer JSON data."""

import json
import os
from pathlib import Path
from datetime import datetime

def generate_boxer_page(boxer_data, template):
    """Generate individual boxer HTML page."""
    # Replace template variables
    html = template
    html = html.replace('{{NAME}}', str(boxer_data.get('name') or 'Unknown'))
    html = html.replace('{{BOXER_ID}}', str(boxer_data.get('boxrec_id') or ''))
    
    # Record
    record = boxer_data.get('record', {})
    html = html.replace('{{WINS}}', str(record.get('wins', 0)))
    html = html.replace('{{LOSSES}}', str(record.get('losses', 0)))
    html = html.replace('{{DRAWS}}', str(record.get('draws', 0)))
    html = html.replace('{{KOS}}', str(record.get('kos', 0)))
    
    # Details
    html = html.replace('{{NATIONALITY}}', boxer_data.get('nationality', 'N/A'))
    html = html.replace('{{DIVISION}}', boxer_data.get('division', 'N/A'))
    html = html.replace('{{STANCE}}', boxer_data.get('stance', 'N/A'))
    html = html.replace('{{HEIGHT}}', boxer_data.get('height', 'N/A'))
    html = html.replace('{{REACH}}', boxer_data.get('reach', 'N/A'))
    html = html.replace('{{STATUS}}', boxer_data.get('status', 'N/A'))
    
    # Bouts
    bouts_html = ''
    for bout in boxer_data.get('bouts', [])[:20]:  # Show last 20 fights
        result_class = f'result-{bout.get("result", "")}'
        bouts_html += f'''
        <div class="bout">
            <div class="bout-date">{bout.get('date', '')}</div>
            <div class="bout-opponent">{bout.get('opponent', '')}</div>
            <div class="bout-venue">{bout.get('venue', '')}</div>
            <div class="bout-result {result_class}">{bout.get('result', '')}</div>
        </div>
        '''
    html = html.replace('{{BOUTS}}', bouts_html)
    
    return html

def create_template():
    """Create HTML template for boxer pages."""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{NAME}} - BoxRec Data</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .boxer-id {
            color: #666;
            font-size: 0.9em;
        }
        .record {
            display: flex;
            gap: 30px;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .record-item {
            text-align: center;
        }
        .record-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #007bff;
            line-height: 1;
        }
        .record-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .detail-item {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }
        .detail-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
        }
        .detail-value {
            font-weight: 600;
            color: #333;
        }
        .bouts {
            margin-top: 40px;
        }
        .bouts h2 {
            color: #333;
            margin-bottom: 20px;
        }
        .bout {
            display: grid;
            grid-template-columns: 100px 1fr 2fr 60px;
            gap: 15px;
            padding: 15px;
            border-bottom: 1px solid #eee;
            align-items: center;
        }
        .bout:hover {
            background: #f8f9fa;
        }
        .bout-date {
            font-weight: 600;
            color: #555;
        }
        .bout-opponent {
            font-weight: 500;
        }
        .bout-venue {
            color: #666;
            font-size: 0.9em;
        }
        .bout-result {
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 600;
            text-align: center;
        }
        .result-W {
            background: #d4edda;
            color: #155724;
        }
        .result-L {
            background: #f8d7da;
            color: #721c24;
        }
        .result-D {
            background: #fff3cd;
            color: #856404;
        }
        .nav {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            text-align: center;
        }
        .nav a {
            color: #007bff;
            text-decoration: none;
            margin: 0 10px;
        }
        .nav a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{NAME}}</h1>
            <div class="boxer-id">BoxRec ID: #{{BOXER_ID}}</div>
        </div>
        
        <div class="record">
            <div class="record-item">
                <div class="record-value">{{WINS}}</div>
                <div class="record-label">Wins</div>
            </div>
            <div class="record-item">
                <div class="record-value">{{LOSSES}}</div>
                <div class="record-label">Losses</div>
            </div>
            <div class="record-item">
                <div class="record-value">{{DRAWS}}</div>
                <div class="record-label">Draws</div>
            </div>
            <div class="record-item">
                <div class="record-value">{{KOS}}</div>
                <div class="record-label">KOs</div>
            </div>
        </div>
        
        <div class="details">
            <div class="detail-item">
                <div class="detail-label">Nationality</div>
                <div class="detail-value">{{NATIONALITY}}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Division</div>
                <div class="detail-value">{{DIVISION}}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Stance</div>
                <div class="detail-value">{{STANCE}}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Height</div>
                <div class="detail-value">{{HEIGHT}}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Reach</div>
                <div class="detail-value">{{REACH}}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Status</div>
                <div class="detail-value">{{STATUS}}</div>
            </div>
        </div>
        
        <div class="bouts">
            <h2>Recent Fights</h2>
            {{BOUTS}}
        </div>
        
        <div class="nav">
            <a href="index.html">← Back to Index</a>
        </div>
    </div>
</body>
</html>'''

def create_index_page(boxers):
    """Create index page listing all boxers."""
    rows = ''
    for boxer in sorted(boxers, key=lambda x: x.get('name', '')):
        record = boxer.get('record', {})
        total = record.get('total_fights', 0)
        rows += f'''
        <tr>
            <td><a href="boxers/{boxer.get('boxrec_id', '')}.html">{boxer.get('name', 'Unknown')}</a></td>
            <td>{boxer.get('nationality', 'N/A')}</td>
            <td>{boxer.get('division', 'N/A')}</td>
            <td>{record.get('wins', 0)}-{record.get('losses', 0)}-{record.get('draws', 0)}</td>
            <td>{total}</td>
        </tr>
        '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BoxRec Data - Index</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #666;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        a {{
            color: #007bff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        .stats {{
            display: flex;
            gap: 30px;
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            font-size: 0.9em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>BoxRec Data Collection</h1>
        <div class="subtitle">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{len(boxers)}</div>
                <div class="stat-label">Total Boxers</div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Nationality</th>
                    <th>Division</th>
                    <th>Record</th>
                    <th>Total Fights</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</body>
</html>'''

def main():
    # Create output directory
    output_dir = Path('github_pages')
    boxers_dir = output_dir / 'boxers'
    boxers_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all boxer JSON files
    json_dir = Path('boxrec_data')
    json_files = list(json_dir.glob('*box-pro*.json'))
    
    boxers = []
    template = create_template()
    
    print(f"Generating pages for {len(json_files)} boxers...")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                boxer_data = json.load(f)
            
            boxers.append(boxer_data)
            
            # Generate individual page
            html = generate_boxer_page(boxer_data, template)
            output_file = boxers_dir / f"{boxer_data.get('boxrec_id', 'unknown')}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
                
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    # Create index page
    index_html = create_index_page(boxers)
    with open(output_dir / 'index.html', 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    print(f"\nGenerated {len(boxers)} boxer pages")
    print(f"Output directory: {output_dir}")
    print("\nTo deploy to GitHub Pages:")
    print("1. Create a new GitHub repository")
    print("2. Copy the 'github_pages' folder contents to the repo")
    print("3. Enable GitHub Pages in Settings > Pages")
    print("4. Select 'Deploy from a branch' and choose 'main' branch")

if __name__ == "__main__":
    main()