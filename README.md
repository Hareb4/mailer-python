# Mailer Backend

## Overview

This is the backend component of the [Mailer application](https://github.com/Hareb4/mailer), responsible for handling email sending operations using Flask and Flask-SocketIO.

## Installation

Follow these steps to set up and run the backend application:

### 1. Clone the Repository

First, clone the repository from GitHub:

```bash
git clone https://github.com/yourusername/mailxl-backend.git
cd mailxl-backend
```

### 2. Set Up a Virtual Environment

It's recommended to use a virtual environment to manage dependencies. Here are the instructions for different operating systems:

#### Windows

1. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate the Virtual Environment**:
   ```bash
   .\venv\Scripts\activate
   ```

#### macOS/Linux

1. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   ```

2. **Activate the Virtual Environment**:
   ```bash
   source venv/bin/activate
   ```

### 3. Install Requirements

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Run the Application

Start the Flask application:

```bash
python app.py
```

The application will run on `http://localhost:5000` by default. Ensure that your frontend is configured to communicate with this backend.

## Usage

- The backend provides an endpoint `/send-email` for sending emails.
- Ensure that the frontend is running on `http://localhost:8080` to match the CORS configuration.

## Contact

For any inquiries, please contact [your-email@example.com](mailto:your-email@example.com).
