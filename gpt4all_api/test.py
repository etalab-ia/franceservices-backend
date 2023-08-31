#!/bin/python

import requests
import sseclient

# Install
# - pip install sseclient


url = "http://localhost:5000"
url = "http://gpt.datascience.etalab.studio"

# Send POST request with string parameter
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {"user_text": "Hello World"}
response = requests.post(url + "/", data=data, headers=headers)

# Keep cookie for later requests
cookies = response.cookies

print("Request Header:", response.request.headers)

print(
    f"""Response
code: {response.status_code}
header: {response.headers}
content: {response.text[:100] if response.text else ""}
"""
)

# Open server-sent-event stream
stream = sseclient.SSEClient(url + "/stream_chat", cookies=cookies)

# Print the result data from the stream
for event in stream:
    print(event.data)
