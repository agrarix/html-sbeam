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
import shutil
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
    "VERSION": "2.0",
    "FFACE": "verdana",
    "FSIZE": "6",
    "HOSTNAME": "xynix",
    "SIZE_MOBILE": "0.9em",
    "SIZE_DESKTOP": "1.25em",
    "TITLE": "Zonnepanelen opbrengst op CHL14 (mbv SunnyBEAM)",
    "ICON": "solar_pingu.jpg",
    "FOOTER": "${PROCESS_TIME} ${PGM} (${BUILD_TIME}) v${VER} at ${HOSTNAME}"
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
        "-c", "--config",
        default="html-sbeam.rc",
        help="Pad naar het configuratiebestand (standaard: %(default)s)"
    )
    parser.add_argument(
        "-d", "--days",
        action="store_true",
        help="Alleen dagbestanden naar maandbestanden compileren (geen HTML genereren)"
    )
    parser.add_argument(
        "-p", "--proc", "-w", "--www",
        action="store_true",
        dest="proc_only",
        help="Alleen HTML-pagina genereren op basis van bestaande maandbestanden (geen dagbestanden compileren)"
    )
    parser.add_argument(
        "-f", "--filter",
        default="",
        help="Filter om alleen bestanden te verwerken die deze tekst bevatten (bijv. een specifiek jaar)"
    )
    parser.add_argument(
        "-V", "--version",
        action="store_true",
        help="Toon het versienummer en build-informatie"
    )
    parser.add_argument(
        "config_file",
        nargs="?",
        default=None,
        help="Positioneel pad naar configuratiebestand (voor backwards compatibility)"
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

def compile_monthly_files(input_dir, log_func, file_filter=""):
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
        
        # Apply filter on month_key or filename
        if file_filter and (file_filter not in month_key and file_filter not in fname):
            continue
            
        if month_key not in groups:
            groups[month_key] = []
        groups[month_key].append((dd, fpath))
        
    for month_key, items in sorted(groups.items()):
        target_file = os.path.join(input_dir, f"_{month_key}.CSV")
        raw_monthly_file = os.path.join(input_dir, f"{month_key}.CSV")
        
        recreate = False
        if os.path.exists(target_file):
            if os.path.exists(raw_monthly_file):
                mtime_raw = os.path.getmtime(raw_monthly_file)
                mtime_target = os.path.getmtime(target_file)
                if mtime_raw > mtime_target:
                    recreate = True
                    log_func(f"  {month_key}.CSV is nieuwer dan _{month_key}.CSV. _{month_key}.CSV wordt opnieuw aangemaakt.")
            
            if not recreate:
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
        return None, None, False
        
    # Check for anomalies (resets or daily jumps > 50 kWh)
    has_anomaly = False
    for i, (date_str, tot, tod) in enumerate(valid_rows):
        if tod > 50.0:
            msg = f"WARNING: Anomalie gedetecteerd in {filename} op {date_str}: E-Today is {tod} kWh (sprong genegeerd)"
            WARNINGS.append(msg)
            has_anomaly = True
            
    # Check completeness (less than 25 days of data)
    is_incomplete = False
    if len(valid_rows) < 25:
        msg = f"WARNING: Onvolledige gegevens in {filename}: slechts {len(valid_rows)} dagen met metingen gevonden"
        WARNINGS.append(msg)
        is_incomplete = True
        
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
        
    return production, int(last_tot), is_incomplete

def main():
    args = parse_args()
    
    if args.version:
        try:
            build_time_str = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime('%d-%m-%Y %H:%M:%S')
        except Exception:
            build_time_str = "04-07-2026 21:25:23"
        print(f"html-sbeam 2.0 ({build_time_str})")
        return
        
    # Determine config file (support both positional and optional)
    config_path = args.config_file if args.config_file is not None else args.config
    cfg = load_config(config_path)
    
    input_dir_raw = os.path.expandvars(cfg.get("INPUT_DIR", "")).strip()
    if not input_dir_raw or input_dir_raw == ".":
        input_dir = os.getcwd()
    else:
        input_dir = os.path.normpath(input_dir_raw.replace("\\", "/"))
        
    output_dir_raw = os.path.expandvars(cfg.get("OUTPUT_DIR", "")).strip()
    if not output_dir_raw or output_dir_raw == ".":
        output_dir = os.getcwd()
    else:
        output_dir = os.path.normpath(output_dir_raw.replace("\\", "/"))
        
    index_file = cfg["INDEX_FILE"]
    
    cfg_log_file = os.path.expandvars(cfg.get("LOG_FILE", "html-sbeam.log")).strip()
    if Path(cfg_log_file).is_absolute():
        log_path = os.path.normpath(cfg_log_file.replace("\\", "/"))
    elif sys.platform.startswith("linux"):
        log_dir = Path.home() / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = str(log_dir / cfg_log_file)
    else:
        log_path = str(SCRIPT_DIR / cfg_log_file)
        
    version = cfg["VERSION"]
    fface = cfg["FFACE"]
    fsize = cfg["FSIZE"]
    hostname = cfg["HOSTNAME"]
    title = cfg["TITLE"]
    icon_file = cfg["ICON"]
    footer_tmpl = cfg.get("FOOTER", "${PROCESS_TIME} ${PGM} (${BUILD_TIME}) v${VER} at ${HOSTNAME}")
    
    output_file = os.path.join(output_dir, index_file)
    
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
    
    # Compile step (skipped if --proc / -p / --www is specified)
    if not args.proc_only:
        compile_monthly_files(input_dir, log, file_filter=args.filter)
        if args.days:
            log("Alleen compilatie uitgevoerd (--days). HTML-generatie overgeslagen.")
            with open(log_path, "w", encoding="utf-8") as lf:
                lf.write("\n".join(log_messages))
            return
            
    # HTML generation step (skipped if --days / -d is specified)
    # Compile and copy CSS file to output directory
    css_src = SCRIPT_DIR / "html-sbeam.css"
    css_dst = Path(output_dir) / "html-sbeam.css"
    if css_src.exists():
        try:
            with open(css_src, "r", encoding="utf-8") as f:
                css_content = f.read()
            # Replace sizing variables
            css_content = css_content.replace("${SIZE_MOBILE}", cfg.get("SIZE_MOBILE", "0.9em"))
            css_content = css_content.replace("${SIZE_DESKTOP}", cfg.get("SIZE_DESKTOP", "1.25em"))
            with open(css_dst, "w", encoding="utf-8") as f:
                f.write(css_content)
            log(f"CSS-bestand gegenereerd en gekopieerd naar: {css_dst}")
        except Exception as e:
            log(f"Fout bij het genereren van CSS-bestand: {e}")
    else:
        log("Waarschuwing: html-sbeam.css niet gevonden in de scriptmap.")

    # Copy icon file to output directory
    icon_src = SCRIPT_DIR / icon_file
    icon_dst = Path(output_dir) / icon_file
    if icon_src.exists():
        try:
            shutil.copy2(icon_src, icon_dst)
            log(f"Icoon-bestand gekopieerd naar: {icon_dst}")
        except Exception as e:
            log(f"Fout bij het kopiëren van icoon-bestand: {e}")
    else:
        log(f"Waarschuwing: Icoon-bestand {icon_file} niet gevonden in de scriptmap.")

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
            month_str = m.group(0)
            if args.filter and (args.filter not in month_str and args.filter not in fname):
                continue
            files_to_process[month_str] = fpath
            
    # Overwrite with compiled files
    for fpath in compiled_files:
        fname = os.path.basename(fpath)
        m = re.match(r"^_(?P<month_str>\d{4}-\d{2})\.CSV$", fname)
        if m:
            month_str = m.group("month_str")
            target_key = month_str + ".CSV"
            if args.filter and (args.filter not in month_str and args.filter not in fname):
                continue
            files_to_process[target_key] = fpath
            
    log(f"{len(files_to_process)} unieke maanden gevonden om te verwerken.")
    
    monthly_data = {}  # (year, month) -> production
    yearly_gr_ttl = {}  # year -> last total
    incomplete_months = set()  # set of (year, month) tuples
    
    now = datetime.now()
    
    for fname, fpath in sorted(files_to_process.items()):
        # Extract year and month
        m = re.match(r"^(\d{4})-(\d{2})\.CSV$", fname)
        if not m:
            continue
        year = int(m.group(1))
        month = int(m.group(2))
        
        is_current = (year == now.year and month == now.month)
        
        data_rows = parse_csv_file(fpath)
        production, last_tot, is_incomplete = calculate_monthly_production(data_rows, os.path.basename(fpath), is_current)
        
        if production is not None:
            log(f"  Verwerken: {os.path.basename(fpath)} -> {production} kWh (metingen: {len(data_rows)}, eindstand: {last_tot})")
            monthly_data[(year, month)] = production
            yearly_gr_ttl[year] = last_tot
            if is_incomplete:
                incomplete_months.add((year, month))
        else:
            log(f"  Verwerken: {os.path.basename(fpath)} -> Geen geldige gegevens gevonden.")

    if not monthly_data:
        log("Fout: Geen gegevens gevonden in de bestanden. HTML-generatie afgebroken.")
        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write("\n".join(log_messages))
        return
        
    all_years = sorted(list(set(y for y, m in monthly_data.keys())))
    
    # Compute yearly totals (Y.ttl) derived from gr.ttl
    yearly_y_ttl = {}
    for i, year in enumerate(all_years):
        gr_ttl = yearly_gr_ttl.get(year)
        if gr_ttl is not None:
            # Find the closest previous year that has a valid gr.ttl
            prev_gr_ttl = None
            for prev_yr in reversed(all_years[:i]):
                if prev_yr in yearly_gr_ttl:
                    prev_gr_ttl = yearly_gr_ttl[prev_yr]
                    break
            
            if prev_gr_ttl is not None:
                yearly_y_ttl[year] = gr_ttl - prev_gr_ttl
            else:
                # First year or no previous year with data
                yearly_y_ttl[year] = gr_ttl
                    
    # Generate HTML content
    html = []
    html.append("<HTML>")
    html.append("  <HEAD>")
    html.append(f"  <TITLE>{title}</TITLE>")
    html.append(f'  <META NAME="generator" content="html-sbeam.py v{version}" />')
    html.append(f'  <META NAME="up-date" content="{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}" />')
    html.append('  <LINK REL="stylesheet" HREF="html-sbeam.css" TYPE="text/css">')
    html.append(f'  <LINK REL="icon" HREF="{icon_file}" TYPE="image/jpg">')
    html.append('  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
    html.append("  </HEAD>")
    html.append("  <BODY>")
    
    # Header and Legend
    html.append(f"    <H1>{title}</H1>")
    html.append("    <H2>Waarden in kWh</H2>")
    html.append('    <P><span class="kwh-green">&#9632; Groen</span> = hoger dan vorig jaar | <span class="kwh-orange">&#9632; Oranje</span> = lager | <span class="kwh-equal">&#9632; Blauw</span> = gelijk | <span class="kwh-pink">&#9632; Roze</span> = onvolledige maand</P>')
    html.append("    <HR>")
    
    # Table Start
    html.append("    <TABLE border=1>")
    
    # Header Row
    html.append("      <TR>")
    html.append("        <TH>YR/mn</TH>")
    for month in range(1, 13):
        html.append(f"        <TH>{month:02d}</TH>")
    html.append("        <TH>Y.ttl</TH>")
    html.append("        <TH>Gr.ttl</TH>")
    html.append("      </TR>")
    
    # Data Rows
    for year in all_years:
        html.append("      <TR>")
        html.append(f"        <TD>{year}</TD>")
        
        for month in range(1, 13):
            val = monthly_data.get((year, month))
            val_str = str(val) if val is not None else ""
            
            # Year-over-year comparison for color coding
            prev_val = monthly_data.get((year - 1, month))
            
            color_class = ""
            if (year, month) in incomplete_months:
                color_class = " class='kwh-pink'"
            elif val is not None and prev_val is not None:
                if val > prev_val:
                    color_class = " class='kwh-green'"
                elif val < prev_val:
                    color_class = " class='kwh-orange'"
                else:
                    color_class = " class='kwh-equal'"
            elif val is not None:
                color_class = " class='kwh-neutral'"
                
            html.append(f"      <TD{color_class}>{val_str}</TD>")
            
        # Yearly totals
        y_ttl = yearly_y_ttl.get(year, "")
        gr_ttl = yearly_gr_ttl.get(year, "")
        
        html.append(f"      <TD>{y_ttl}</TD>")
        html.append(f"      <TD>{gr_ttl}</TD>")
        html.append("      </TR>")
        
    html.append("    </TABLE>")
    html.append("    <HR>")
    
    # Generate line chart container
    html.append("    <H2>Grafiek per Jaar</H2>")
    html.append("    <div class='chart-container' style='position: relative; max-width: 1000px; margin: 20px 0;'>")
    html.append("        <canvas id='sbeamChart'></canvas>")
    html.append("    </div>")
    html.append("    <HR>")
    
    # Generate datasets JS array for Chart.js
    datasets_js = []
    for idx, year in enumerate(all_years):
        year_data = []
        pt_colors = []
        pt_radius = []
        
        # Distribute colors evenly across the color wheel
        hue = int((idx * 360 / max(1, len(all_years))) % 360)
        color = f"hsl({hue}, 70%, 50%)"
        
        for month in range(1, 13):
            val = monthly_data.get((year, month))
            year_data.append(str(val) if val is not None else "null")
            if (year, month) in incomplete_months:
                pt_colors.append("'#FFC0CB'")
                pt_radius.append("6")
            else:
                pt_colors.append(f"'{color}'")
                pt_radius.append("3")
            
        datasets_js.append(f"""            {{
                label: "{year}",
                data: [{", ".join(year_data)}],
                borderColor: "{color}",
                backgroundColor: "{color}",
                pointBackgroundColor: [{", ".join(pt_colors)}],
                pointBorderColor: [{", ".join(pt_colors)}],
                pointRadius: [{", ".join(pt_radius)}],
                borderWidth: 2,
                tension: 0.1,
                spanGaps: true
            }}""")
    
    # Calculate monthly averages over all years (excluding incomplete months)
    avg_data = []
    for month in range(1, 13):
        vals = []
        for year in all_years:
            if (year, month) not in incomplete_months:
                val = monthly_data.get((year, month))
                if val is not None:
                    vals.append(val)
        if vals:
            avg_val = sum(vals) / len(vals)
            avg_data.append(str(round(avg_val, 1)))
        else:
            avg_data.append("null")

    datasets_js.append(f"""            {{
                label: "Gemiddelde",
                data: [{", ".join(avg_data)}],
                borderColor: "#000000",
                borderDash: [5, 5],
                borderWidth: 3,
                tension: 0.1,
                pointRadius: 4,
                pointBackgroundColor: "#000000",
                spanGaps: true
            }}""")

    datasets_str = ",\n".join(datasets_js)
    
    # Append Chart.js initialization script
    html.append("    <script>")
    html.append("    const ctx = document.getElementById('sbeamChart').getContext('2d');")
    html.append("    const chart = new Chart(ctx, {")
    html.append("        type: 'line',")
    html.append("        data: {")
    html.append("            labels: ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'],")
    html.append(f"            datasets: [\n{datasets_str}\n            ]")
    html.append("        },")
    html.append("        options: {")
    html.append("            responsive: true,")
    html.append("            plugins: {")
    html.append("                legend: {")
    html.append("                    position: 'right',")
    html.append("                    onClick: function(e, legendItem, legend) {")
    html.append("                        const index = legendItem.datasetIndex;")
    html.append("                        const ci = legend.chart;")
    html.append("                        const isCtrl = e.native.ctrlKey || e.native.metaKey;")
    html.append("                        ")
    html.append("                        if (isCtrl) {")
    html.append("                            // Toggle only the clicked dataset")
    html.append("                            ci.setDatasetVisibility(index, !ci.isDatasetVisible(index));")
    html.append("                        } else {")
    html.append("                            let visibleYearsCount = 0;")
    html.append("                            ci.data.datasets.forEach((d, i) => {")
    html.append("                                if (d.label !== 'Gemiddelde' && ci.isDatasetVisible(i)) visibleYearsCount++;")
    html.append("                            });")
    html.append("                            const isSelfVisible = ci.isDatasetVisible(index);")
    html.append("                            const isGemiddelde = ci.data.datasets[index].label === 'Gemiddelde';")
    html.append("                            ")
    html.append("                            if (isGemiddelde) {")
    html.append("                                ci.setDatasetVisibility(index, !isSelfVisible);")
    html.append("                            } else {")
    html.append("                                if (visibleYearsCount === 1 && isSelfVisible) {")
    html.append("                                    ci.data.datasets.forEach((d, i) => {")
    html.append("                                        ci.setDatasetVisibility(i, true);")
    html.append("                                    });")
    html.append("                                } else {")
    html.append("                                    ci.data.datasets.forEach((d, i) => {")
    html.append("                                        if (d.label === 'Gemiddelde') {")
    html.append("                                            ci.setDatasetVisibility(i, true);")
    html.append("                                        } else {")
    html.append("                                            ci.setDatasetVisibility(i, i === index);")
    html.append("                                        }")
    html.append("                                    });")
    html.append("                                }")
    html.append("                            }")
    html.append("                        }")
    html.append("                        ci.update();")
    html.append("                    }")
    html.append("                },")
    html.append("                title: {")
    html.append("                    display: true,")
    html.append("                    text: 'Maandelijkse Opbrengst per Jaar (kWh)'")
    html.append("                }")
    html.append("            },")
    html.append("            scales: {")
    html.append("                y: {")
    html.append("                    beginAtZero: true,")
    html.append("                    title: {")
    html.append("                        display: true,")
    html.append("                        text: 'kWh'")
    html.append("                    }")
    html.append("                },")
    html.append("                x: {")
    html.append("                    title: {")
    html.append("                        display: true,")
    html.append("                        text: 'Maand'")
    html.append("                    }")
    html.append("                }")
    html.append("            }")
    html.append("        }")
    html.append("    });")
    html.append("    </script>")
    
    # Generate cumulative line chart container
    html.append("    <H2>Cumulatieve Opbrengst per Jaar</H2>")
    html.append("    <div class='chart-container' style='position: relative; max-width: 1000px; margin: 20px 0;'>")
    html.append("        <canvas id='sbeamCumChart'></canvas>")
    html.append("    </div>")
    html.append("    <HR>")
    
    # Generate cumulative datasets JS array for Chart.js
    datasets_cum_js = []
    for idx, year in enumerate(all_years):
        year_cum_data = []
        running_total = 0
        has_any_data = False
        for month in range(1, 13):
            val = monthly_data.get((year, month))
            if val is not None:
                running_total += val
                year_cum_data.append(str(running_total))
                has_any_data = True
            else:
                is_future = (year == now.year and month > now.month)
                if is_future:
                    year_cum_data.append("null")
                else:
                    if has_any_data:
                        year_cum_data.append(str(running_total))
                    else:
                        year_cum_data.append("null")
            
        # Distribute colors evenly across the color wheel
        hue = int((idx * 360 / max(1, len(all_years))) % 360)
        color = f"hsl({hue}, 70%, 50%)"
        
        datasets_cum_js.append(f"""            {{
                label: "{year}",
                data: [{", ".join(year_cum_data)}],
                borderColor: "{color}",
                backgroundColor: "{color}",
                borderWidth: 2,
                tension: 0.1,
                spanGaps: true
            }}""")
    
    # Calculate cumulative averages from the monthly average values
    cum_avg_data = []
    running_avg_total = 0.0
    for avg_val_str in avg_data:
        if avg_val_str != "null":
            running_avg_total += float(avg_val_str)
            cum_avg_data.append(str(round(running_avg_total, 1)))
        else:
            cum_avg_data.append("null")

    datasets_cum_js.append(f"""            {{
                label: "Gemiddelde",
                data: [{", ".join(cum_avg_data)}],
                borderColor: "#000000",
                borderDash: [5, 5],
                borderWidth: 3,
                tension: 0.1,
                pointRadius: 4,
                pointBackgroundColor: "#000000",
                spanGaps: true
            }}""")

    datasets_cum_str = ",\n".join(datasets_cum_js)
    
    # Append Chart.js initialization script for cumulative chart
    html.append("    <script>")
    html.append("    const ctxCum = document.getElementById('sbeamCumChart').getContext('2d');")
    html.append("    const chartCum = new Chart(ctxCum, {")
    html.append("        type: 'line',")
    html.append("        data: {")
    html.append("            labels: ['Jan', 'Feb', 'Mrt', 'Apr', 'Mei', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec'],")
    html.append(f"            datasets: [\n{datasets_cum_str}\n            ]")
    html.append("        },")
    html.append("        options: {")
    html.append("            responsive: true,")
    html.append("            plugins: {")
    html.append("                legend: {")
    html.append("                    position: 'right',")
    html.append("                    onClick: function(e, legendItem, legend) {")
    html.append("                        const index = legendItem.datasetIndex;")
    html.append("                        const ci = legend.chart;")
    html.append("                        const isCtrl = e.native.ctrlKey || e.native.metaKey;")
    html.append("                        ")
    html.append("                        if (isCtrl) {")
    html.append("                            ci.setDatasetVisibility(index, !ci.isDatasetVisible(index));")
    html.append("                        } else {")
    html.append("                            let visibleYearsCount = 0;")
    html.append("                            ci.data.datasets.forEach((d, i) => {")
    html.append("                                if (d.label !== 'Gemiddelde' && ci.isDatasetVisible(i)) visibleYearsCount++;")
    html.append("                            });")
    html.append("                            const isSelfVisible = ci.isDatasetVisible(index);")
    html.append("                            const isGemiddelde = ci.data.datasets[index].label === 'Gemiddelde';")
    html.append("                            ")
    html.append("                            if (isGemiddelde) {")
    html.append("                                ci.setDatasetVisibility(index, !isSelfVisible);")
    html.append("                            } else {")
    html.append("                                if (visibleYearsCount === 1 && isSelfVisible) {")
    html.append("                                    ci.data.datasets.forEach((d, i) => {")
    html.append("                                        ci.setDatasetVisibility(i, true);")
    html.append("                                    });")
    html.append("                                } else {")
    html.append("                                    ci.data.datasets.forEach((d, i) => {")
    html.append("                                        if (d.label === 'Gemiddelde') {")
    html.append("                                            ci.setDatasetVisibility(i, true);")
    html.append("                                        } else {")
    html.append("                                            ci.setDatasetVisibility(i, i === index);")
    html.append("                                        }")
    html.append("                                    });")
    html.append("                                }")
    html.append("                            }")
    html.append("                        }")
    html.append("                        ci.update();")
    html.append("                    }")
    html.append("                },")
    html.append("                title: {")
    html.append("                    display: true,")
    html.append("                    text: 'Cumulatieve Jaaropbrengst (kWh)'")
    html.append("                }")
    html.append("            },")
    html.append("            scales: {")
    html.append("                y: {")
    html.append("                    beginAtZero: true,")
    html.append("                    title: {")
    html.append("                        display: true,")
    html.append("                        text: 'kWh'")
    html.append("                    }")
    html.append("                },")
    html.append("                x: {")
    html.append("                    title: {")
    html.append("                        display: true,")
    html.append("                        text: 'Maand'")
    html.append("                    }")
    html.append("                }")
    html.append("            }")
    html.append("        }")
    html.append("    });")
    html.append("    </script>")
    
    # Format date and time
    now_dt = datetime.now()
    date_str = now_dt.strftime("%d-%m-%Y")
    time_str = now_dt.strftime("%H:%M:%S")

    # Get build time of the script file dynamically
    try:
        build_time_str = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime('%d-%m-%Y %H:%M:%S')
    except Exception:
        build_time_str = now_dt.strftime('%d-%m-%Y %H:%M:%S')
        
    process_time_str = now_dt.strftime('%a %b %d %H:%M:%S %Z %Y')
    
    # Format footer text
    footer_text = footer_tmpl
    footer_text = footer_text.replace("${PGM}", "html-sbeam.py").replace("{PGM}", "html-sbeam.py")
    footer_text = footer_text.replace("${VER}", version).replace("{VER}", version).replace("${VERSION}", version).replace("{VERSION}", version)
    footer_text = footer_text.replace("${DATE}", date_str).replace("{DATE}", date_str)
    footer_text = footer_text.replace("${TIME}", time_str).replace("{TIME}", time_str)
    footer_text = footer_text.replace("${BUILD_TIME}", build_time_str).replace("{BUILD_TIME}", build_time_str)
    footer_text = footer_text.replace("${PROCESS_TIME}", process_time_str).replace("{PROCESS_TIME}", process_time_str)
    footer_text = footer_text.replace("${HOSTNAME}", hostname).replace("{HOSTNAME}", hostname)
    
    html.append(f"    <H6>{footer_text}</H6>")
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
