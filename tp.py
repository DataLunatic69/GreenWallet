import requests

# ⚠️ Replace with your actual key safely
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImM4ZTEzOTRjLWRiNzYtNDAxZC1hZGRiLTljZWYzZGE4ZDAwZiIsIm9yZ0lkIjoiNDc0MTcyIiwidXNlcklkIjoiNDg3Nzg2IiwidHlwZUlkIjoiNmUwOGNhN2QtMzM5OC00MGRjLWE0ZGUtZjViZjdjY2VlYjFjIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NTk2NDUyNDgsImV4cCI6NDkxNTQwNTI0OH0.YhnsITac0DCdhFp1krx61JS1In4jtSRsbn80W4LWHko"
address = "0x00000000219ab540356cBB839Cbe05303d7705Fa"  # Example address

url = f"https://deep-index.moralis.io/api/v2.2/{address}?chain=eth"

headers = {
    "accept": "application/json",
    "X-API-Key": api_key
}

response = requests.get(url, headers=headers)
print(response.status_code)
print(response.json())
