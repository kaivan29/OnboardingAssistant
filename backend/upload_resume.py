import http.client
import os

def upload_resume():
    host = "localhost"
    port = 8000
    endpoint = "/api/upload-resume"
    file_path = "/Users/zy/Desktop/GrokOnboarding/backend/Elon Musk - Resume Professional Template.pdf"
    
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    with open(file_path, "rb") as f:
        file_content = f.read()

    # Construct the body
    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="resume.pdf"\r\n'
        f'Content-Type: application/pdf\r\n\r\n'
    ).encode('utf-8') + file_content + (
        f'\r\n--{boundary}--\r\n'
    ).encode('utf-8')

    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }

    conn = http.client.HTTPConnection(host, port)
    conn.request("POST", endpoint, body, headers)
    response = conn.getresponse()
    
    print(f"Status: {response.status}")
    response_data = response.read().decode('utf-8')
    print(f"Response: {response_data}")
    conn.close()

if __name__ == "__main__":
    upload_resume()
