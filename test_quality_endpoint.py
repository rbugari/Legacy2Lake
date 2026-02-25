"""
Test Code Quality endpoint
"""
import requests

url = "http://localhost:8085/projects/ec771d1a-4fe4-4499-970d-54e28de4d926/quality"

response = requests.get(url)

print(f"Status: {response.status_code}")
print(f"\nResponse:")
print(response.json())
