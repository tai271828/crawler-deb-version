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
        print("The crawler seems to run in Github Action.")
        print("\tBoth GITHUB_ENV and GITHUB_WORKSPACE are set.")
        print(f"\tGITHUB_ENV: {github_env}")
        print(f"\tGITHUB_WORKSPACE: {github_workspace}")

        return True

    else:
        print("The crawler seems not to run in Github Action.")
        print("\tEither GITHUB_ENV or GITHUB_WORKSPACE is not set.")

        return False


if not (api_key and email_from and email_to and email_subject) and not check_if_in_github_action():
    raise ValueError("Necessary environment variables are not set.")


def send_result_notification(email_content, subject_prefix="DEB-VERSION"):
    subject = f"[{subject_prefix}]{email_subject}"

    # Email payload
    payload = {
        "personalizations": [
            {
                "to": [{"email": f"{email_to}"}]
            }
        ],
        "from": {"email": f"{email_from}"},
        "subject": subject,
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


def load_last_known_version(deb_name):
    # Load the last known version from a file
    if os.path.exists(LAST_VERSION_FILE):
        with open(LAST_VERSION_FILE, 'r') as f:
            return json.load(f).get(deb_name)
    return None


def save_last_known_version(deb_name, version):
    # Save the last known version to a file
    with open(LAST_VERSION_FILE, 'w') as f:
        json.dump({deb_name: version}, f)


def get_deb_version(deb_name):
    # Run the rmadison command and capture the output
    try:
        output = subprocess.check_output(['rmadison', '-u', 'debian', deb_name], text=True)
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
    deb_name="debian-keyring"
    # Step 1: Get the current version
    current_version = get_deb_version(deb_name)
    if current_version is None:
        print("Failed to retrieve the current version of debian-keyring.")
        return

    # Step 2: Load the last known version
    last_known_version = load_last_known_version(deb_name)

    # Step 3: Compare the versions
    email_content="EMAIL CONTENT IS NOT READY YET."
    if last_known_version != current_version:
        email_content=f"{deb_name}: Version update detected: {last_known_version} -> {current_version}"
        save_last_known_version(deb_name, current_version)

        if not check_if_in_github_action():
            send_result_notification(email_content, subject_prefix=deb_name)

    else:
        email_content=f"{deb_name}: No version update detected. Current version is still {current_version}."
    
    print(email_content)


if __name__ == "__main__":
    main()
