import requests

API_KEY = "AQ.Ab8RN6K9JqWuacblF_2WdYqA9ZJUBgS5CM1QEbSYg4jrHw3lbg"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [
        {
            "parts": [
                {
                    "text": "Hello"
                }
            ]
        }
    ]
}

r = requests.post(url, json=payload)

print("Status Code:", r.status_code)
print("Response:")
print(r.text)