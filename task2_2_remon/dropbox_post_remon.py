import requests
import json
import webbrowser
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DropboxPOSTRemon:
    def __init__(self):
        self.app_key = os.getenv('DROPBOX_APP_KEY')
        self.app_secret = os.getenv('DROPBOX_APP_SECRET')
        self.redirect_uri = os.getenv('REDIRECT_URI')
        self.access_token = None
        
        print("=== StudyStart JYU Task 2.2 - POST Implementation ===")
        print("Student: Remon")
        
    def get_authorization_url(self):
        params = {
            'client_id': self.app_key,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri
        }
        return f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"
    
    def post_method_1_get_token(self, auth_code):
        print("\nPOST METHOD 1: Getting Access Token")
        print("="*40)
        
        url = "https://api.dropboxapi.com/oauth2/token"
        data = {
            'code': auth_code,
            'grant_type': 'authorization_code',
            'client_id': self.app_key,
            'client_secret': self.app_secret,
            'redirect_uri': self.redirect_uri
        }
        
        response = requests.post(url, data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            print("SUCCESS: Access token obtained!")
            return token_data
        else:
            raise Exception(f"Token request failed: {response.status_code}")
    
    def post_method_2_upload_file(self, local_file, dropbox_path):
        print("\nPOST METHOD 2: File Upload")
        print("="*40)
        
        # Create test file
        with open(local_file, 'w') as f:
            f.write("StudyStart JYU Task 2.2\nPOST Implementation by Remon\nSuccessfully uploaded via POST method")
        
        with open(local_file, 'rb') as f:
            file_content = f.read()
        
        url = "https://content.dropboxapi.com/2/files/upload"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps({'path': dropbox_path, 'mode': 'add', 'autorename': True})
        }
        
        response = requests.post(url, headers=headers, data=file_content)
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: File uploaded!")
            print(f"File: {result['name']}")
            return result
        else:
            raise Exception(f"Upload failed: {response.status_code}")
    
    def post_method_3_create_folder(self, folder_path):
        print("\nPOST METHOD 3: Create Folder (Extra Action)")
        print("="*40)
        
        url = "https://api.dropboxapi.com/2/files/create_folder_v2"
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json={'path': folder_path})
        
        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: Folder created!")
            print(f"Folder: {result['metadata']['name']}")
            return result
        else:
            print("Note: Folder may already exist")
            return {"status": "folder_exists"}

    def list_folder(self, folder_path="/", recursive=False, with_links=False):
        print("\nGET METHOD 4: List Folder")

        if not self.access_token:
            raise Exception("Missing access token. Authorize first.")

        # Dropbox expects "" for root
        path = "" if folder_path in (None, "", "/") else folder_path

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # 1) Initial list
        url = "https://api.dropboxapi.com/2/files/list_folder"
        payload = {
            "path": path,
            "recursive": bool(recursive),
            "include_deleted": False
        }
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            raise Exception(f"List failed: {resp.status_code} {resp.text}")

        data = resp.json()
        entries = data.get("entries", [])
        cursor = data.get("cursor")
        has_more = data.get("has_more", False)

        # 2) Continue while more pages
        cont_url = "https://api.dropboxapi.com/2/files/list_folder/continue"
        while has_more:
            cont_resp = requests.post(cont_url, headers=headers, json={"cursor": cursor})
            if cont_resp.status_code != 200:
                raise Exception(f"List (continue) failed: {cont_resp.status_code} {cont_resp.text}")
            cont_data = cont_resp.json()
            entries.extend(cont_data.get("entries", []))
            cursor = cont_data.get("cursor")
            has_more = cont_data.get("has_more", False)

        # 3) Simplify result
        simplified = []
        for e in entries:
            tag = e.get(".tag")
            base = {
                "tag": tag,  # "file" | "folder"
                "name": e.get("name"),
                "id": e.get("id"),
                "path_lower": e.get("path_lower"),
                "path_display": e.get("path_display")
            }
            if tag == "file":
                base.update({
                    "size": e.get("size"),
                    "server_modified": e.get("server_modified"),
                    "client_modified": e.get("client_modified"),
                    "rev": e.get("rev")
                })
            simplified.append(base)
        return {"entries": simplified}


def main():
    print("StudyStart JYU Task 2.2 - POST Methods by Remon")
    
    client = DropboxPOSTRemon()
    
    auth_url = client.get_authorization_url()
    webbrowser.open(auth_url)
    
    print("\nInstructions:")
    print("1. Login to Dropbox")
    print("2. Copy the code from redirect URL")
    
    auth_code = input("Enter authorization code: ").strip()
    
    try:
        client.post_method_1_get_token(auth_code)
        client.post_method_2_upload_file("remon_test.txt", "/StudyStart_Remon_File.txt")
        client.post_method_3_create_folder("/StudyStart_Remon_Folder")
        
        print("\n" + "="*50)
        print("ALL POST METHODS COMPLETED SUCCESSFULLY!")
        print("Check your Dropbox for uploaded files and folder")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()