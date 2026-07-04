#!/usr/bin/env python3
"""
html-sbeam.py
Processes solar panel data from daily logs (YY-MM-DD.CSV) to compile monthly logs (_YYYY-MM.CSV),
then generates a color-coded HTML webpage showing solar panel kWh production.
Supports configuration via html-sbeam.rc file and detects logging anomalies.
"""

import os
import sys
import glob
import re
import argparse
from datetime import datetime
from pathlib import Path

# Force UTF-8 output to prevent issues on Windows console with special characters
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Configuration defaults
DEFAULTS = {
    "INPUT_DIR": r"Z:\DATA\SBEAM",
    "OUTPUT_DIR": r"Z:\WWW\domains\www.agrarix.net\pages\sbeam",
    "INDEX_FILE": "index.html",
    "LOG_FILE": "html-sbeam.log",
    "VERSION": "1.03",
    "FFACE": "verdana",
    "FSIZE": "6",
    "HOSTNAME": "xynix"
}

SCRIPT_DIR = Path(__file__).parent
WARNINGS = []

def parse_args():
    """Parse command line arguments"""
    # Windows-style /help and /? mapping
    for i, arg in enumerate(sys.argv):
        if arg.lower() in ("/help", "/?", "?"):
            sys.argv[i] = "--help"
            
    parser = argparse.ArgumentParser(
        prog="html-sbeam",
        description="Generates a static color-coded HTML page from SunnyBeam solar data CSV files."
    )
    parser.add_argument(
        "config_file",
        nargs="?",
        default="html-sbeam.rc",
        help="Path to the configuration file (default: %(default)s)"
    )
    return parser.parse_args()

def load_config(config_path_str):
    """Load configuration from .rc file with key=\"value\" syntax"""
    cfg = DEFAULTS.copy()
    config_file = Path(config_path_str)
    
    if not config_file.is_absolute():
        if sys.platform != "win32":
            # On Linux, look in ~/etc/
            config_file = Path.home() / "etc" / config_path_str
        else:
            # On Windows, look in the script's directory
            config_file = SCRIPT_DIR / config_file
            
    if not config_file.exists():
        print(f"Informatie: {config_file.name} niet gevonden, standaardwaarden worden gebruikt.")
        return cfg
        
    print(f"Configuratie geladen uit: {config_file}")
    try:
        with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip()
                    # Strip comments on the same line
                    if "#" in val:
                        parts = val.split("#", 1)
                        if parts[0].count('"') % 2 == 0 and parts[0].count("'") % 2 == 0:
                            val = parts[0].strip()
                    # Strip outer quotes
                    if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                        val = val[1:-1]
                    cfg[key] = val
        return cfg
    except Exception as e:
        print(f"Fout bij het laden van {config_file.name}: {e}")
        return cfg

def parse_daily_file(fpath):
    """
    Parses a daily YY-MM-DD.CSV file.
    If E-Today is missing or invalid, calculates it from 10-minute power values.
    Returns (e_total_str, e_today_str)
    """
    e_today = "-"
    e_total = "-"
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            lines = [line.strip() for line in f]
            
        for line in lines:
            if line.startswith("E-Today kWh;"):
                e_today = line.split(";", 1)[1].strip()
            elif line.startswith("E-Total kWh;"):
                e_total = line.split(";", 1)[1].strip()
                
        # Check if E-Today is missing or invalid
        if e_today in ("-", "-,---", ""):
            powers = []
            for line in lines:
                if ";" in line:
                    parts = line.split(";")
                    if len(parts) >= 2 and re.match(r"^\d{2}:\d{2}$", parts[0].strip()):
                        val_str = parts[1].strip()
                        if val_str != "-,---" and val_str != "":
                            try:
                                powers.append(float(val_str.replace(",", ".")))
                            except ValueError:
                                pass
            if powers:
                # Calculate energy: Sum(Power in kW) * (10 / 60) hours
                calc_today = sum(powers) / 6.0
                e_today = f"{calc_today:.3f}".replace(".", ",")
                msg = f"WARNING: E-Today was leeg in {os.path.basename(fpath)}. Berekend uit 10-minuten waarden: {e_today} kWh"
                WARNINGS.append(msg)
    except Exception as e:
        pass
    return e_total, e_today

def compile_monthly_files(input_dir, log_func):
    """
    Compiles daily YY-MM-DD.CSV files into monthly _YYYY-MM.CSV files.
    Skips compilation if the monthly file already exists.
    """
    log_func("Compileren van maandelijkse bestanden uit dagelijkse logs...")
    daily_files = glob.glob(os.path.join(input_dir, "[0-9][0-9]-[0-9][0-9]-[0-9][0-9].CSV"))
    
    # Group daily files by 20YY-MM
    groups = {}
    for fpath in daily_files:
        fname = os.path.basename(fpath)
        m = re.match(r"^(\d{2})-(\d{2})-(\d{2})\.CSV$", fname)
        if not m:
            continue
        yy, mm, dd = m.groups()
        month_key = f"20{yy}-{mm}"
        if month_key not in groups:
            groups[month_key] = []
        groups[month_key].append((dd, fpath))
        
    for month_key, items in sorted(groups.items()):
        target_file = os.path.join(input_dir, f"_{month_key}.CSV")
        if os.path.exists(target_file):
            log_func(f"  _{month_key}.CSV bestaat al. Overslaan.")
            continue
            
        log_func(f"  Maandbestand aanmaken: _{month_key}.CSV uit {len(items)} dagbestanden...")
        
        # Sort items by day
        items.sort(key=lambda x: x[0])
        
        rows = []
        rows.append("sep=;")
        rows.append("Time;E-Total;E-Today")
        rows.append("DD-MM-YYYY;kWh;kWh")
        
        for dd, fpath in items:
            yy, mm = month_key[2:4], month_key[5:7]
            date_str = f"{dd}-{mm}-20{yy}"
            e_total, e_today = parse_daily_file(fpath)
            rows.append(f"{date_str};{e_total};{e_today}")
            
        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write("\n".join(rows) + "\n")
        except Exception as e:
            log_func(f"  Fout bij het schrijven van _{month_key}.CSV: {e}")

def parse_csv_file(fpath):
    """
    Parses a compiled _YYYY-MM.CSV file (or YYYY-MM.CSV fallback).
    Returns a list of tuples: (date_str, e_total_float, e_today_float)
    """
    data = []
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if ";" not in line:
                    continue
                parts = line.strip().split(";")
                if len(parts) < 3:
                    continue
                date_str = parts[0].strip()
                # Match DD-MM-YYYY date format
                if not re.match(r"^\d{2}-\d{2}-\d{4}$", date_str):
                    continue
                
                tot_str = parts[1].strip()
                tod_str = parts[2].strip()
                
                # Check for empty or invalid readings
                if tot_str == "" or tot_str == "-,---" or tod_str == "" or tod_str == "-,---" or tot_str == "-" or tod_str == "-":
                    continue
                
                try:
                    tot = float(tot_str.replace(",", "."))
                    tod = float(tod_str.replace(",", "."))
                    data.append((date_str, tot, tod))
                except ValueError:
                    pass
    except Exception as e:
        print(f"Fout bij het lezen van {os.path.basename(fpath)}: {e}")
    return data

def calculate_monthly_production(data_rows, filename, is_current_month):
    """
    Calculates monthly production and detects anomalies.
    """
    # Filter rows where e_total is greater than 0
    valid_rows = [r for r in data_rows if r[1] > 0]
    if not valid_rows:
        msg = f"WARNING: Geen geldige metingen gevonden in {filename}"
        WARNINGS.append(msg)
        return None, None
        
    # Check for anomalies (resets or daily jumps > 50 kWh)
    has_anomaly = False
    for i, (date_str, tot, tod) in enumerate(valid_rows):
        if tod > 50.0:
            msg = f"WARNING: Anomalie gedetecteerd in {filename} op {date_str}: E-Today is {tod} kWh (sprong genegeerd)"
            WARNINGS.append(msg)
            has_anomaly = True
            
    # Check completeness (less than 25 days of data), except for the current month
    if not is_current_month and len(valid_rows) < 25:
        msg = f"WARNING: Onvolledige gegevens in {filename}: slechts {len(valid_rows)} dagen met metingen gevonden"
        WARNINGS.append(msg)
        
    last_tot = valid_rows[-1][1]
    
    if has_anomaly:
        # Fallback calculation: sum E-Today values that are <= 50.0
        clean_sum = sum(tod for _, _, tod in valid_rows if tod <= 50.0)
        production = int(clean_sum)
    else:
        # Standard historical formula
        first_tot = valid_rows[0][1]
        first_tod = valid_rows[0][2]
        production = int(last_tot) - (int(first_tot) - int(first_tod))
        
    return production, int(last_tot)

def main():
    args = parse_args()
    cfg = load_config(args.config_file)
    
    input_dir = cfg["INPUT_DIR"]
    output_dir = cfg["OUTPUT_DIR"]
    index_file = cfg["INDEX_FILE"]
    log_file_name = cfg["LOG_FILE"]
    version = cfg["VERSION"]
    fface = cfg["FFACE"]
    fsize = cfg["FSIZE"]
    hostname = cfg["HOSTNAME"]
    
    output_file = os.path.join(output_dir, index_file)
    log_path = log_file_name
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Log messages capturing
    log_messages = []
    
    def log(msg):
        print(msg)
        log_messages.append(msg)
        
    log(f"SunnyBEAM Kleurgecodeerde HTML-generator v{version}")
    log(f"Inputmap: {input_dir}")
    log(f"Outputmap: {output_dir}")
    log(f"HTML-bestand: {output_file}")
    log(f"Logbestand: {log_path}")
    
    # Compile _YYYY-MM.CSV from daily logs
    compile_monthly_files(input_dir, log)
    
    # 2. Scan for compiled monthly files (_YYYY-MM.CSV) first, fallback to YYYY-MM.CSV
    log("Scannen naar maandelijkse gegevensbestanden...")
    
    # Look for compiled files first
    compiled_files = glob.glob(os.path.join(input_dir, "_[0-9][0-9][0-9][0-9]-[0-9][0-9].CSV"))
    # Look for raw files
    raw_files = glob.glob(os.path.join(input_dir, "[0-9][0-9][0-9][0-9]-[0-9][0-9].CSV"))
    
    # Merge, prioritizing compiled files
    files_to_process = {}
    
    # Populate with raw files first
    for fpath in raw_files:
        fname = os.path.basename(fpath)
        m = re.match(r"^(\d{4})-(\d{2})\.CSV$", fname)
        if m:
            files_to_process[m.group(0)] = fpath
            
    # Overwrite with compiled files
    for fpath in compiled_files:
        fname = os.path.basename(fpath)
        m = re.match(r"^_(?P<month_str>\d{4}-\d{2})\.CSV$", fname)
        if m:
            month_str = m.group("month_str")
            files_to_process[month_str + ".CSV"] = fpath
            
    log(f"{len(files_to_process)} unieke maanden gevonden om te verwerken.")
    
    monthly_data = {}  # (year, month) -> production
    yearly_gr_ttl = {}  # year -> last total
    
    now = datetime.now()
    
    for fname, fpath in sorted(files_to_process.items()):
        # Extract year and month
        # fname is either YYYY-MM.CSV or from compiled list
        m = re.match(r"^(\d{4})-(\d{2})\.CSV$", fname)
        if not m:
            continue
        year = int(m.group(1))
        month = int(m.group(2))
        
        is_current = (year == now.year and month == now.month)
        
        data_rows = parse_csv_file(fpath)
        production, last_tot = calculate_monthly_production(data_rows, os.path.basename(fpath), is_current)
        
        if production is not None:
            log(f"  Verwerken: {os.path.basename(fpath)} -> {production} kWh (metingen: {len(data_rows)}, eindstand: {last_tot})")
            monthly_data[(year, month)] = production
            yearly_gr_ttl[year] = last_tot
        else:
            log(f"  Verwerken: {os.path.basename(fpath)} -> Geen geldige gegevens gevonden.")

    if not monthly_data:
        log("Fout: Geen gegevens gevonden in de bestanden. HTML-generatie afgebroken.")
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write("\n".join(log_messages))
        return
        
    all_years = sorted(list(set(y for y, m in monthly_data.keys())))
    
    # Compute yearly totals (Y.ttl)
    yearly_y_ttl = {}
    for i, year in enumerate(all_years):
        gr_ttl = yearly_gr_ttl.get(year)
        if gr_ttl is not None:
            if i == 0:
                yearly_y_ttl[year] = gr_ttl
            else:
                prev_year = all_years[i - 1]
                prev_gr_ttl = yearly_gr_ttl.get(prev_year)
                if prev_gr_ttl is not None:
                    yearly_y_ttl[year] = gr_ttl - prev_gr_ttl
                else:
                    yearly_y_ttl[year] = gr_ttl
                    
    # Generate HTML content
    html = []
    html.append("<HTML>")
    html.append("  <HEAD>")
    html.append(f'  <META NAME="generator" content="html-sbeam.py v{version}" />')
    html.append(f'  <META NAME="up-date" content="{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}" />')
    html.append("  </HEAD>")
    html.append("  <TITLE>SunnyBEAM DATA</TITLE>")
    html.append('  <LINK REL="icon" HREF="Agrarix-Pingu_2017.jpg" TYPE="image/jpg">')
    html.append("  <BODY>")
    
    # CSS Styling matching the live webpage
    html.append("  <STYLE>")
    html.append(f"    body {{ font-family: {fface}; }}")
    html.append("    .kwh-neutral { background-color: #f0f0f0; }")
    html.append("    .kwh-green { background-color: #90EE90; color: #2d5016; font-weight: bold; }")
    html.append("    .kwh-orange { background-color: #FFA500; color: #fff; font-weight: bold; }")
    html.append("    .kwh-equal { background-color: #ADD8E6; color: #003366; font-weight: bold; }")
    html.append("    table { border-collapse: collapse; margin: 15px 0; }")
    html.append("    td, th { padding: 8px 12px; border: 1px solid #ddd; }")
    html.append("    th { background-color: #4CAF50; color: white; }")
    html.append("  </STYLE>")
    
    # Header and Legend
    html.append("    <H1>SunnyBEAM DATA</H1>")
    html.append("    <H2>Numbers in kWh</H2>")
    html.append('    <P><FONT SIZE=2><span class="kwh-green">■ Green</span> = higher than last year | <span class="kwh-orange">■ Orange</span> = lower | <span class="kwh-equal">■ Blue</span> = equal</FONT></P>')
    html.append("    <HR>")
    
    # Table Start
    html.append("    <TABLE border=1>")
    
    # Header Row
    html.append("      <TR>")
    html.append(f"        <TH><FONT FACE={fface} SIZE={fsize}>YR/mn</FONT></TH>")
    for month in range(1, 13):
        html.append(f"        <TH><FONT FACE={fface} SIZE={fsize}>{month:02d}</FONT></TH>")
    html.append(f"        <TH><FONT FACE={fface} SIZE={fsize}>Y.ttl</FONT></TH>")
    html.append(f"        <TH><FONT FACE={fface} SIZE={fsize}>gr.ttl</FONT></TH>")
    html.append("      </TR>")
    
    # Data Rows
    for year in all_years:
        html.append("      <TR>")
        html.append(f"        <TD><FONT FACE={fface} SIZE={fsize}>{year}</FONT></TD>")
        
        for month in range(1, 13):
            val = monthly_data.get((year, month))
            val_str = str(val) if val is not None else ""
            
            # Year-over-year comparison for color coding
            prev_val = monthly_data.get((year - 1, month))
            
            color_class = ""
            if val is not None and prev_val is not None:
                if val > prev_val:
                    color_class = " class='kwh-green'"
                elif val < prev_val:
                    color_class = " class='kwh-orange'"
                else:
                    color_class = " class='kwh-equal'"
            elif val is not None:
                color_class = " class='kwh-neutral'"
                
            html.append(f"      <TD{color_class}><FONT FACE={fface} SIZE={fsize}>{val_str}</FONT></TD>")
            
        # Yearly totals
        y_ttl = yearly_y_ttl.get(year, "")
        gr_ttl = yearly_gr_ttl.get(year, "")
        
        html.append(f"      <TD><FONT FACE={fface} SIZE={fsize}>{y_ttl}</FONT></TD>")
        html.append(f"      <TD><FONT FACE={fface} SIZE={fsize}>{gr_ttl}</FONT></TD>")
        html.append("      </TR>")
        
    html.append("    </TABLE>")
    html.append("    <HR>")
    html.append(f"    <H6>{datetime.now().strftime('%a %b %d %H:%M:%S %Z %Y')} html-sbeam.py v{version} at {hostname}</H6>")
    html.append("  </BODY>")
    html.append("</HTML>")
    
    # Write HTML output
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    log(f"Bestand met succes gegenereerd op: {output_file}")
    
    # Output warnings summary at the end
    if WARNINGS:
        log("\n" + "=" * 80)
        log("SAMENVATTING VAN ANOMALIEËN / WAARSCHUWINGEN:")
        log("=" * 80)
        for w in WARNINGS:
            log(w)
        log("=" * 80 + "\n")
    else:
        log("\nGeen anomalieën of waarschuwingen gedetecteerd.\n")
        
    # Write log file
    with open(log_path, "w", encoding="utf-8") as lf:
        lf.write("\n".join(log_messages))

if __name__ == "__main__":
    main()
