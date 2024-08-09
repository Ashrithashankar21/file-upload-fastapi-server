# Python File upload tracker

A FastAPI server in python

1. That sends an automatic notification email when a file is uploaded
    to local folder and one drive folder.
2. Allow us to upload files to one drive.

## Getting Started

Follow the installation instructions below to set up the project.

## Installation

### 1. Set Up Your Environment

Clone the [Repo link](https://github.com/Ashrithashankar21/file-upload-fastapi-server.git)
and Checkout to `users/ashritha-shankar/files-tracker`

Before proceeding, make sure you have the following installed on your system.

1. python(3.12 v)
2. VS code

Do the below steps:

1. Login to [https://portal.azure.com/](https://portal.azure.com/)
2. Create a new registration by clicking on "App Registrations".
3. Add application name, redirect URL, and click "Register".
   Copy the below tokens from it:
   - Tenant ID
   - Client ID

4. Click on "API permissions", then "Add a permission", select "Microsoft Graph",
and then "Delegated permissions". Choose the below permissions:

   - Files.ReadWrite
   - Files.ReadWrite.All
   - User.Read

5. Click on "Certificates & secrets", then click on "New client secret".
6. Add a description and expiry date, then copy the created value and store it separately,
that will be your client-secret-id. (Please make sure to copy at first instance as
it appears only once)

Create a .env file with the below values:

```bash
    folder_to_track = folder path which will be tracked locally
    file_tracker = file path in which the local file changes are logged
    smtp_server = server name(eg: microsoft, google)
    smtp_port = server port number
    smtp_user = user email id
    smtp_password = user app password
    sender_email = sender email id
    receiver_email = receiver email ids in a list. (eg: ["abc@outlook.com","cdf@outlook.com"])
    client_id = paste the client id
    client_secret_id = paste the secret client id
    one_drive_file_tracker = file path in which one drive changes are logged
    tenant_id =  paste the tenant id
    one_drive_record_file = acts as a local db to store all one drive folder details
    one_drive_folder_to_track = one drive folder name to track
    one_drive_folder_user_id = one drive owner email id
```

Run the below commands:

```bash
pip install poetry
poetry
poetry install
```

### 2. Start the Application

Navigate to src folder in terminal and run the below command.

```bash
fastapi dev main.py
```

### 3. Access the Application

Once the development server is up, open your web browser and go to the
address [http://localhost:8000/docs](http://localhost:8000/docs) and access the
endpoints.
