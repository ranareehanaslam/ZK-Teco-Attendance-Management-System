# ZK Teco Attendance Management System

Welcome to the ZK Teco Attendance Management System! This system is built using FastAPI and allows you to manage attendance data collected from ZK Teco devices. You can generate PDF reports, fetch user data, and view attendance records through a simple API interface.

## Table of Contents
- [Features](#features)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Assigning Static IP to the ZK Teco Machine](#assigning-static-ip-to-the-zk-teco-machine)

## Features

- **Fetch User Data**: Retrieve user data from the ZK Teco device.
- **Attendance Records**: View and download attendance records.
- **PDF Reports**: Generate and download attendance reports in PDF format.
- **User-specific Attendance**: Get attendance details for a specific user.

## Setup and Installation

### Prerequisites

- Python 3.8+
- FastAPI
- ZK Teco device
- ReportLab
- Starlette

### Installation

1. Clone the repository:

```sh
git clone https://github.com/your-repo/zk-teco-attendance-management.git
cd zk-teco-attendance-management
```

2. Create a virtual environment and activate it:

```sh
python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`
```

3. Install the required packages:

```sh
pip install fastapi uvicorn reportlab starlette zk
```

4. Run the FastAPI server:

```sh
uvicorn main:app --reload
```

## Usage

Open your browser and go to `http://127.0.0.1:8000` to access the API. You can use tools like [Swagger UI](http://127.0.0.1:8000/docs) or [ReDoc](http://127.0.0.1:8000/redoc) to explore the available endpoints.

## Endpoints

### GET `/`
Returns the index page.

### GET `/download-attendance/{time_period}`
Downloads the attendance report for the specified time period (`current-month` or `last-month`). Optionally, you can specify user IDs to filter the report.

### GET `/refresh_users`
Fetches the latest user data from the ZK Teco device.

### GET `/get_users`
Returns the user data stored in the system.

### GET `/refresh-attendance`
Fetches and updates the attendance records for the last two months.

### GET `/user-attendance/{user_id}`
Returns the attendance records for a specific user for the specified time period (`current-month` or `last-month`).

## Assigning Static IP to the ZK Teco Machine

To assign a static IP to your ZK Teco device, follow these steps:

1. **Access Your Router Settings**:
    - Open your web browser and enter the IP address of your router (commonly `192.168.1.1` or `192.168.0.1`).
    - Log in using your router's username and password.

2. **Find the DHCP Settings**:
    - Look for DHCP settings in your router's menu. This is usually found under "Network", "LAN", or "Advanced Settings".

3. **Reserve an IP Address**:
    - Find the section for "Address Reservation" or "DHCP Reservation".
    - Add a new reservation by entering the MAC address of the ZK Teco device and the desired IP address.

4. **Configure the ZK Teco Device**:
    - On the ZK Teco device, go to `Menu > Comm. > Ethernet > IP Address`.
    - Enter the static IP address you reserved in the router settings.
    - Set the subnet mask (usually `255.255.255.0`) and the default gateway (the IP address of your router).
    - Save the settings and restart the device if necessary.

5. **Verify the Connection**:
    - Ensure that the ZK Teco device is connected to your network with the static IP address.
    - Ping the device from your computer to confirm it is reachable.

By following these steps, you can successfully assign a static IP to your ZK Teco device, ensuring it remains consistent on your network.
