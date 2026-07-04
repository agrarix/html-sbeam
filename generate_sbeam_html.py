#!/usr/bin/env python3
"""
SunnyBEAM HTML Generator with Color-Coded Year-over-Year Comparison
Combines data processing + HTML generation + color coding in one script
"""
import os
from datetime import datetime

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

def get_color_class(current_val, prev_val):
    """Determine color class based on Y-o-Y comparison"""
    if prev_val is None:
        return 'kwh-neutral'
    
    try:
        curr_int = int(''.join(filter(str.isdigit, str(current_val))))
        prev_int = int(''.join(filter(str.isdigit, str(prev_val))))
        
        if curr_int > prev_int:
            return 'kwh-green'
        elif curr_int < prev_int:
            return 'kwh-orange'
        else:
            return 'kwh-equal'
    except ValueError:
        return 'kwh-neutral'

def generate_html(csv_file, output_file, hostname='xynix', version='0.11'):
    """Generate HTML table with colors from CSV data"""
    
    # Load data
    data = get_month_data(csv_file)
    if not data:
        print("No data loaded, aborting")
        return False
    
    # Extract years and months
    years = sorted(set(k.split('-')[0] for k in data.keys()))
    months = sorted(set(k.split('-')[1] for k in data.keys() if '-' in k and len(k.split('-')) == 2))
    
    # Generate HTML
    html = []
    html.append('<HTML>')
    html.append('  <HEAD>')
    html.append(f'  <META NAME="generator" content="SunnyBEAM v{version}" />')
    html.append(f'  <META NAME="up-date" content="{datetime.now().isoformat()}" />')
    html.append('  </HEAD>')
    html.append('  <TITLE>SunnyBEAM DATA</TITLE>')
    html.append('  <LINK REL="icon" HREF="Agrarix-Pingu_2017.jpg" TYPE="image/jpg">')
    html.append('  <BODY>')
    
    # CSS Styling
    html.append('  <STYLE>')
    html.append('    body { font-family: verdana; }')
    html.append('    .kwh-neutral { background-color: #f0f0f0; }')
    html.append('    .kwh-green { background-color: #90EE90; color: #2d5016; font-weight: bold; }')
    html.append('    .kwh-orange { background-color: #FFA500; color: #fff; font-weight: bold; }')
    html.append('    .kwh-equal { background-color: #ADD8E6; color: #003366; font-weight: bold; }')
    html.append('    table { border-collapse: collapse; margin: 15px 0; }')
    html.append('    td, th { padding: 8px 12px; border: 1px solid #ddd; }')
    html.append('    th { background-color: #4CAF50; color: white; }')
    html.append('  </STYLE>')
    
    # Title and Legend
    html.append('    <H1>SunnyBEAM DATA</H1>')
    html.append('    <H2>Numbers in kWh</H2>')
    html.append('    <P><FONT SIZE=2>')
    html.append('      <span class="kwh-green">■ Green</span> = higher than last year | ')
    html.append('      <span class="kwh-orange">■ Orange</span> = lower than last year | ')
    html.append('      <span class="kwh-equal">■ Blue</span> = equal to last year')
    html.append('    </FONT></P>')
    html.append('    <HR>')
    
    # Table
    html.append('    <TABLE border=1>')
    
    # Header row
    html.append('      <TR>')
    html.append('        <TH>YR/mn</TH>')
    for month in months:
        html.append(f'        <TH>{month}</TH>')
    html.append('      </TR>')
    
    # Data rows
    for year in years:
        html.append('      <TR>')
        html.append(f'        <TD><B>{year}</B></TD>')
        
        for month in months:
            key = f'{year}-{month}'
            current_val = data.get(key, '')
            
            # Get previous year value for color comparison
            prev_year = str(int(year) - 1)
            prev_key = f'{prev_year}-{month}'
            prev_val = data.get(prev_key)
            
            color_class = get_color_class(current_val, prev_val)
            html.append(f"        <TD class='{color_class}'>{current_val}</TD>")
        
        html.append('      </TR>')
    
    html.append('    </TABLE>')
    html.append('')
    html.append('    <HR>')
    html.append(f'    <H6>{datetime.now().strftime("%c")} SunnyBEAM v{version} at {hostname}</H6>')
    html.append('  </BODY>')
    html.append('</HTML>')
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(html))
    
    print(f"Generated: {output_file}")
    return True

if __name__ == '__main__':
    # Configuration
    csv_file = '/tmp/proc_sbeam-data_month.csv'
    output_file = '/mnt/nas/WWW/domains/www.agrarix.net/pages/sbeam/index.html'
    
    if os.path.exists(csv_file):
        generate_html(csv_file, output_file)
    else:
        print(f"Error: {csv_file} not found")
        print("Make sure to run proc_sbeam-data.sh first with -p flag to generate month data")
