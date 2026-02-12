import requests
import json
import time

BASE_URL = "http://localhost:5002" # Corrected port based on app.py
ENDPOINT = "/validate-email"

def test_validate_email(email):
    url = f"{BASE_URL}{ENDPOINT}"
    payload = {"email": email}
    headers = {"Content-Type": "application/json"}
    
    print(f"Testing with email: {email}")
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        try:
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=4))
            
            if response.status_code == 200 and data.get("status") == "success":
                print("SUCCESS: Endpoint returned success.")
                records = data.get("records", [])
                if records:
                     print(f"User found/created: {records[0].get('email')}, Google ID: {records[0].get('google_id')}")
                else:
                    print("WARNING: No records returned.")
            else:
                print("FAILURE: Endpoint returned error or unexpected status.")

        except json.JSONDecodeError:
            print("Response is not JSON.")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to server. Is it running?")

if __name__ == "__main__":
    # Test 1: Valid format
    test_validate_email("romarioariza@gmail.com")
    
    # Test 2: Invalid format
    print("\n--- Testing Invalid Email ---")
    test_validate_email("invalid-email")
