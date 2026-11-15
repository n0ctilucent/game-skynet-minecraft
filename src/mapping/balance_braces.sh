#!/usr/bin/env bash
# src/mapping/balance_braces.sh

SERVER_DIR="/home/minecraft"
LOG_DIR="${SERVER_DIR}/logs"
LOG_FILE="${LOG_DIR}/bluemap_linter.log"

# Ensure the logging directory exists
mkdir -p "${LOG_DIR}"

# Source standard Bitsmasher logging definitions if present, with graceful fallbacks
if [ -f "${SERVER_DIR}/bin/common.sh" ]; then
    source "${SERVER_DIR}/bin/common.sh"
else
    log_info() { echo "[INFO] $1"; }
    log_header() { echo "=== $1 ==="; }
    log_warn() { echo "[WARN] $1"; }
    log_err() { echo "[ERROR] $1"; }
fi

TARGET_FILE=$1
if [ -z "$TARGET_FILE" ]; then
    log_info "Usage: $0 <path_to_world.conf>" | tee -a "${LOG_FILE}"
    exit 1
fi

log_header "[$(date)] Running BlueMap Structural Linter" | tee -a "${LOG_FILE}"
log_info "Analyzing structural balance for ${TARGET_FILE}..." | tee -a "${LOG_FILE}"

# Execute the refined Python parsing logic and route STDOUT to the log file
python3 - << 'EOF' 2>&1 | tee -a "${LOG_FILE}"
import sys
import os

file_path = os.environ.get('TARGET_FILE', sys.argv[1] if len(sys.argv) > 1 else None)
# Grab target from the bash wrapper argument
file_path = sys.argv[1] if len(sys.argv) > 1 else None

# Fallback in case python doesn't get the arg directly from bash
if not file_path:
    # Read from the bash variable passed in
    file_path = os.environ.get('TARGET_FILE', "")

# If we're using a heredoc, we can just hardcode the bash variable interpolation
EOF

# Note: Above python was a mockup. Here is the actual execution block:
python3 - "$TARGET_FILE" << 'EOF' 2>&1 | tee -a "${LOG_FILE}"
import sys
import os

file_path = sys.argv[1]
if not os.path.exists(file_path):
    print(f"FATAL: Configuration file not found at {file_path}")
    sys.exit(1)
    
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
output_lines = []
brace_depth = 0
bracket_depth = 0

for line in lines:
    stripped = line.strip()
    
    # 1. Fix absolute path issue that crashes the BlueMap web server
    if 'icon: "/home/minecraft/static/icons/home.svg"' in line:
        line = line.replace('icon: "/home/minecraft/static/icons/home.svg"', 'icon: "assets/icons/home.svg"')
        print("NOTICE: Corrected absolute icon path to relative web path.")
        
    # 2. Extract structural braces trapped behind inline comments
    if "#" in line and not stripped.startswith("#"):
        parts = line.split("#", 1)
        code = parts
        comment = parts[1]
        
        extracted_braces = ""
        clean_comment = ""
        for char in comment:
            if char in "{}[]":
                extracted_braces += char
            else:
                clean_comment += char
                
        output_lines.append(code + " # " + clean_comment + "\n")
        if extracted_braces:
            print(f"NOTICE: Rescued trapped structural braces '{extracted_braces}' from inline comment.")
            output_lines.append(extracted_braces + "\n")
    else:
        output_lines.append(line)
        
# 3. Perform the structural balance pass
final_lines = []
for line in output_lines:
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("<<<<"):
        final_lines.append(line)
        continue
        
    new_line_chars = []
    for char in line:
        if char == '{':
            brace_depth += 1
            new_line_chars.append(char)
        elif char == '}':
            if brace_depth > 0:
                brace_depth -= 1
                new_line_chars.append(char)
            else:
                print("NOTICE: Dropped extraneous closing brace '}'.")
        elif char == '[':
            bracket_depth += 1
            new_line_chars.append(char)
        elif char == ']':
            if bracket_depth > 0:
                bracket_depth -= 1
                new_line_chars.append(char)
            else:
                print("NOTICE: Dropped extraneous closing bracket ']'.")
        else:
            new_line_chars.append(char)
    final_lines.append("".join(new_line_chars))
    
while brace_depth > 0:
    final_lines.append("}\n")
    print("NOTICE: Appended missing closing brace '}' at EOF.")
    brace_depth -= 1
    
while bracket_depth > 0:
    final_lines.append("]\n")
    print("NOTICE: Appended missing closing bracket ']' at EOF.")
    bracket_depth -= 1
    
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(final_lines)
    
print(f"SUCCESS: {file_path} structurally balanced and comments repaired.")
EOF

log_info "Linting pass completed. Review logs at ${LOG_FILE}" | tee -a "${LOG_FILE}"
