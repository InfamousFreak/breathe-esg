import requests

url = "http://127.0.0.1:8000/api/v1/ingest/utility/"
file_path = "utility_portal_raw.csv"

with open(file_path, "rb") as f:
    response = requests.post(url, files={"file": f})

print(f"Utility Status: {response.status_code}")
print(f"Response: {response.json()}")