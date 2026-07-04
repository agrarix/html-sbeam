#!/usr/bin/env python3
"""
Post-processor for SunnyBEAM HTML output
Adds color classes to cells based on year-over-year comparison
"""

import re
import sys

def get_month_data(csv_file):
    """Parse month CSV and return data dictionary"""
    data = {}
    try:
        with open(csv_file, 'r') as f:
            for line in f:
                if line.strip().startswith('#'):
                    continue
                parts = line.strip().split(';')
                if len(parts) >= 2:
                    key = parts[0].strip()
                    try:
                        value = int(''.join(filter(str.isdigit, parts[1])))
                        data[key] = value
                    except ValueError:
                        pass
    except FileNotFoundError:
        print(f"Warning: {csv_file} not found")
    return data

def add_colors_to_html(html_file, month_csv):
    """Add color classes to HTML cells based on Y-o-Y comparison"""
    
    # Load data
    data = get_month_data(month_csv)
    if not data:
        print("No data loaded")
        return
    
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Parse table
    lines = content.split('\n')
    output_lines = []
    current_year = None
    month_index = 0
    
    for i, line in enumerate(lines):
        # Detect year cells
        year_match = re.search(r'>(\d{4})<', line)
        if year_match and '<TH>' not in line:
            current_year = year_match.group(1)
            month_index = 0
            output_lines.append(line)
            continue
        
        # Process data cells
        if current_year and '<TD><FONT' in line and not line.strip().startswith('<TH'):
            month_index += 1
            
            # Extract value
            value_match = re.search(r'>([^<]+)<', line)
            if value_match:
                current_val_str = value_match.group(1).strip()
                current_val = int(''.join(filter(str.isdigit, current_val_str)))
                
                # Get previous year value
                prev_year = int(current_year) - 1
                prev_key = f"{prev_year}-{month_index:02d}"
                prev_val = data.get(prev_key, None)
                
                color_class = 'kwh-neutral'
                if prev_val is not None:
                    if current_val > prev_val:
                        color_class = 'kwh-green'
                    elif current_val < prev_val:
                        color_class = 'kwh-orange'
                    elif current_val == prev_val:
                        color_class = 'kwh-equal'
                
                # Add class to cell
                line = line.replace('<TD><FONT', f"<TD class='{color_class}'><FONT", 1)
        
        output_lines.append(line)
    
    # Write back
    with open(html_file, 'w') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Updated {html_file} with color classes")

if __name__ == '__main__':
    html_file = '/mnt/nas/WWW/domains/www.agrarix.net/pages/sbeam/index.html'
    month_csv = '/tmp/proc_sbeam-data_month.csv'
    
    add_colors_to_html(html_file, month_csv)
