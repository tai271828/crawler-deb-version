#!/usr/bin/env python3
import subprocess
import requests
import os
import json


LAST_VERSION_FILE = "last_known_version.json"

# Fetch the API key from the environment variable
api_key = os.getenv("SENDGRID_API_KEY")
email_from = os.getenv("SENDGRID_EMAIL_FROM")
email_to = os.getenv("SENDGRID_EMAIL_TO")
email_subject = os.getenv("SENDGRID_EMAIL_SUBJECT")

# SendGrid API endpoint
url_sendgrid_api = "https://api.sendgrid.com/v3/mail/send"

# Headers
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}


def check_if_in_github_action():
    # Check if GITHUB_ENV and GITHUB_WORKSPACE environment variables are set
    github_env = os.getenv('GITHUB_ENV')
    github_workspace = os.getenv('GITHUB_WORKSPACE')

    if github_env and github_workspace:
        print("Both GITHUB_ENV and GITHUB_WORKSPACE are set.")
        print(f"GITHUB_ENV: {github_env}")
        print(f"GITHUB_WORKSPACE: {github_workspace}")

        return True

    elif not github_env and not github_workspace:
        print("Neither GITHUB_ENV nor GITHUB_WORKSPACE are set.")
    elif not github_env:
        print("GITHUB_ENV is not set.")
    elif not github_workspace:
        print("GITHUB_WORKSPACE is not set.")

    return False


if not (api_key and email_from and email_to and email_subject) and not check_if_in_github_action():
    raise ValueError("Necessary environment variables are not set.")


def send_result_notification(email_content):
    # Email payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": f"{email_to}"}]
            }
        ],
        "from": {"email": f"{email_from}"},
        "subject": f"{email_subject}",
        "content": [
            {"type": "text/plain", "value": f"{email_content}"}
        ]
    }

    # Send the POST request
    response = requests.post(url_sendgrid_api, json=payload, headers=headers)

    # Check the response
    if response.status_code == 202:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email: {response.status_code}")
        print(response.text)


def load_last_known_version():
    # Load the last known version from a file
    if os.path.exists(LAST_VERSION_FILE):
        with open(LAST_VERSION_FILE, 'r') as f:
            return json.load(f).get('last_version')
    return None


def save_last_known_version(version):
    # Save the last known version to a file
    with open(LAST_VERSION_FILE, 'w') as f:
        json.dump({'last_version': version}, f)


def get_debian_keyring_version():
    # Run the rmadison command and capture the output
    try:
        output = subprocess.check_output(['rmadison', '-u', 'debian', 'debian-keyring'], text=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing rmadison: {e}")
        return None

    # Parse the output to get the latest version
    latest_version = None
    for line in output.splitlines():
        parts = line.split('|')
        if len(parts) >= 3:
            version = parts[1].strip()
            if latest_version is None or version > latest_version:
                latest_version = version

    return latest_version


def main():
    # Step 1: Get the current version
    current_version = get_debian_keyring_version()
    if current_version is None:
        print("Failed to retrieve the current version of debian-keyring.")
        return

    # Step 2: Load the last known version
    last_known_version = load_last_known_version()

    # Step 3: Compare the versions
    if last_known_version != current_version:
        print(f"Version update detected: {last_known_version} -> {current_version}")
        save_last_known_version(current_version)
    else:
        print(f"No version update detected. Current version is still {current_version}.")
    
    if not check_if_in_github_action():
        send_result_notification(current_version)


if __name__ == "__main__":
    main()
