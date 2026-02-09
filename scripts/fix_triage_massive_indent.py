"""Fix massive indentation issue in triage.py - add 4 spaces to lines 174-440"""

file_path = "apps/api/routers/triage.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Add 4 spaces to lines 174-440 (0-indexed: 173-439) that aren't empty
for i in range(173, min(440, len(lines))):
    if lines[i].strip():  # Only non-empty lines
        lines[i] = '    ' + lines[i]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"✅ Reindented lines 174-440 in {file_path}")
