import json

with open('output/sync_check_report_v2.json') as f:
    data = json.load(f)

print("="*70)
print("BACKEND ENDPOINTS - projects.py")
print("="*70)
projects_endpoints = [e for e in data['endpoints'] if 'projects.py' in e['router_file']]
for e in sorted(projects_endpoints, key=lambda x: x['line_number']):
    print(f"{e['method']:7s} {e['path']:50s} (line {e['line_number']})")

print("\n" + "="*70)
print("FRONTEND API CALLS - projects related")
print("="*70)
projects_calls = [c for c in data['api_calls'] if 'projects' in c['path'].lower()]
for c in sorted(projects_calls, key=lambda x: x['component_file'])[:20]:
    print(f"{c['method']:7s} {c['path']:50s} ({c['component_file']}:{c['line_number']})")
