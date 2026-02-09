"""
Script to fix indentation in triage.py
"""

# Read the file
with open('apps/api/routers/triage.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "# === MAIN TRIAGE LOGIC ===" and "try:"
# Everything after try: until the first "except Exception" needs to be indented
in_try_block = False
try_line_index = None
except_line_index = None

for i, line in enumerate(lines):
    if '# === MAIN TRIAGE LOGIC ===' in line:
        try_line_index = i + 1  # Next line should be try:
    
    if try_line_index and i > try_line_index and line.strip().startswith('except Exception as e:'):
        except_line_index = i
        break

if try_line_index and except_line_index:
    print(f"Found try block from line {try_line_index} to {except_line_index}")
    
    # Indent all lines between try and except by 4 spaces (if they're not already indented enough)
    for i in range(try_line_index + 1, except_line_index):
        if lines[i].strip() and not lines[i].startswith('        '):  # If line has content but not enough indent
            # Check current indent level
            current_indent = len(lines[i]) - len(lines[i].lstrip())
            if current_indent < 8:  # Should be at least 8 spaces (2 levels)
                # Add 4 more spaces
                lines[i] = '    ' + lines[i]
    
    # Write back
    with open('apps/api/routers/triage.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Fixed indentation!")
else:
    print(f"Could not find try/except block. try_line_index={try_line_index}, except_line_index={except_line_index}")
