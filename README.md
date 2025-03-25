# Mailer Backend

## Overview

This is the backend component of the Mailer application, responsible for handling email sending operations using Flask and Flask-SocketIO.

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

### Note on Port Configuration

The Flask application is configured to accept requests from any origin, thanks to the following setup in `app.py`:

```python
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")
```

This allows the backend to receive requests from any domain or port. If you want to restrict access—for example, to only allow requests from `http://localhost:4000`—modify the configuration like this:

```python
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:4000"}})
socketio = SocketIO(app, cors_allowed_origins="http://localhost:4000")
```

## Endpoints

The backend provides the following endpoints for email operations:

### 1. **Send Email**

- **Endpoint**: `/send-email`
- **Method**: `POST`
- **Description**: Sends multiple emails based on the provided data.
- **Request Body**:
  - `smtp_server`: SMTP server address.
  - `port`: SMTP server port.
  - `sender_email`: Email address of the sender.
  - `sender_password`: Password for the sender's email account.
  - `smtp_from`: The "From" address for the email.
  - `excelFile`: Excel file containing recipient details.
  - `subject_template`: Template for the email subject.
  - `body_template`: Template for the email body.
  - `attachments`: List of PDF attachments.
  - `posters`: List of image attachments.
  - `poster_url`: URL for poster images.

### 2. **Send Test Email**

- **Endpoint**: `/send-test`
- **Method**: `POST`
- **Description**: Sends a test email to the specified address.
- **Request Body**:
  - Same parameters as `/send-email`, but only requires the test email address.

### 3. **Test Connection**

- **Endpoint**: `/test-connection`
- **Method**: `GET`
- **Description**: Tests the connection to the backend.
- **Response**: Returns a JSON object indicating success.

## Usage

- Ensure that your frontend is configured to communicate with this backend running on `http://localhost:5000`.
- The application now includes enhanced error handling and logging for email sending operations.

## Contact

For any inquiries, please contact [hareb.div@gmail.com](mailto:hareb.div@gmail.com).
