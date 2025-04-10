from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import uuid
import time
from datetime import datetime, timedelta
import shutil
from bs4 import BeautifulSoup
import os
import re
import unicodedata


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure the upload folder
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Ensure the email_log.txt file exists
if not os.path.exists('email_log.txt'):
    with open('email_log.txt', 'w') as f:
        f.write("\n")


def clean_html_body(body):
    """
    Cleans the HTML body by removing unnecessary <p> tags containing only &nbsp;
    and adjusting the formatting dynamically.
    """
    # Parse the HTML content
    soup = BeautifulSoup(body, 'html.parser')

    # Loop through all <p> tags
    for p in soup.find_all('p'):
        # Check if <p> contains only &nbsp; or is empty
        if not p.get_text(strip=True):  # Empty or only spaces
            p.decompose()
        elif p.get_text(strip=True) == '\xa0':  # &nbsp;
            p.decompose()

    # Optional: Remove empty spans
    for span in soup.find_all('span'):
        if not span.get_text(strip=True):  # Empty or only spaces
            span.decompose()

    # Wrap the cleaned content in a styled div
    cleaned_body = f"""
              <div style="line-height: 1.5; font-family: Tahoma; font-size:10.5pt;">
                {soup}
            </div>
    """
    return cleaned_body


def send_email(smtp_from, smtp_server, port, sender_email, sender_password, recipient_email, subject, body, attachments, posters, poster_url):
    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = recipient_email
    msg['Subject'] = subject

    # Attach PDF files
    for pdf_path in attachments:
        try:
            with open(pdf_path, 'rb') as f:
                part = MIMEApplication(
                    f.read(), Name=os.path.basename(pdf_path))
                part['Content-Disposition'] = f'attachment; filename="{
                    os.path.basename(pdf_path)}"'
                msg.attach(part)
        except FileNotFoundError:
            print(f"Warning: The file {
                  pdf_path} was not found. Skipping attachment.")

    # Attach Poster files
    unique_cids = []
    for poster_path in posters:
        try:
            filename = os.path.basename(poster_path)
            with open(poster_path, 'rb') as f:
                # Adjust _subtype as needed
                img = MIMEImage(f.read(), _subtype='jpeg', name=filename)
                unique_cid = str(uuid.uuid4())
                img.add_header('Content-ID', f'<{unique_cid}>')
                img.add_header('Content-Disposition',
                               f'inline; filename="{filename}"')
                msg.attach(img)
                unique_cids.append(unique_cid)
        except FileNotFoundError:
            print(
                f"Warning: The poster image {poster_path} was not found. Skipping poster.")

    # Generate HTML body with multiple posters inline
    if posters:
        if poster_url:
            print("------with URL--------")
            posters_html = ''.join(
                [f'<a href="{poster_url}"><img src="cid:{cid}" alt="Poster" style="max-width: 100%; height: auto; display: block;"></a>' for cid in unique_cids])
            html_body = f"""
            <html>
                <body style="line-height: 1.2;">
                    {posters_html}
                    {body}
                </body>
            </html>
            """
        else:
            print('without poster link')
            posters_html = ''.join(
                [f'<img src="cid:{cid}" alt="Poster" style="max-width: 100%; height: auto; display: block;">' for cid in unique_cids])
            html_body = f"""
            <html>
                <body style="line-height: 1.2;">
                    {posters_html}
                    {body}
                </body>
            </html>
            """
    else:
        print('without posters')
        html_body = clean_html_body(body)
        html_body2 = f"""
        <html>
            <body >
              <div style="line-height: 1.2;">{body}</div>
            </body>
        </html>
        """

    # Attach the HTML body
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            response = server.send_message(msg)
            print("Server response:", response)
        return True
    except smtplib.SMTPAuthenticationError:
        print("Error: Authentication failed. Please check your email and password.")
        return "Authentication failed. Please check your email and password."
    except smtplib.SMTPConnectError:
        print("Error: Unable to connect to the SMTP server. Please check the server address and port.")
        return "Unable to connect to the SMTP server. Please check the server address and port."
    except Exception as e:
        print(f"Failed to send email: {e} to {recipient_email}")
        # Save failed email details to a text file
        # with open('email_log.txt', 'a') as f:
        #     f.write(f"{recipient_email}\n")
        return e


def send_email_status_to_admin(smtp_from, smtp_server, port, sender_email, sender_password, logs, details):
    msg = MIMEMultipart()
    msg['From'] = smtp_from
    msg['To'] = "hareb.div@gmail.com"
    msg['Subject'] = "Email Sending Finished"

    # Create the email body with the log information
    # Example Python data

    total_emails = details['total_emails']
    success_count = details['success_count']
    failure_count = details['failure_count']
    total_time = details['total_time']
    avg_speed = details['average_speed']

    # Generate logs HTML
    logs_html = ""
    for log in logs:
        color_class = "success" if log["status"] == "success" else "failed"
        logs_html += f'<div class="log-entry">{log["email"]} - <span class="{color_class}">{log["status"].capitalize()}</span></div>'

    # Full HTML template
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ 
            font-family: -apple-system, sans-serif; 
            background: #f7f9f7; 
            margin: 20px; 
            text-align: center;
        }}
        .card {{ 
            background: white; 
            padding: 20px; 
            border-radius: 15px; 
            max-width: 400px; 
            margin: 0 auto; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        h1 {{ 
            font-size: 20px; 
            color: #333; 
            margin: 0 0 15px;
        }}
        .stats {{
            font-size: 14px; 
            color: #666; 
            margin-bottom: 15px;
        }}
        .logs div {{ 
            font-size: 13px; 
            padding: 5px 0; 
            color: #333;
        }}
        .success {{ color: #2ecc71; }}
        .failed {{ color: #ff6b6b; }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Email Summary</h1>
        <div class="stats">
            <div>Total: {total_emails}</div>
            <div class="success">Success: {success_count}</div>
            <div class="failed">Failed: {failure_count}</div>
            <div>Time: {total_time}s</div>
            <div>Speed: {avg_speed}/m</div>
        </div>
        <div class="logs">
            {logs}
        </div>
    </div>
</body>
</html>
                  """

    # Attach the HTML body
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            return True
    except Exception as e:
        print(f"Failed to send admin status email: {e}")
        return False


@app.route('/send-email', methods=['POST'])
def send_email_endpoint():
    with open('email_log.txt', 'a') as f:
        f.write(f"\n{datetime.now()}: Sending multiple emails\n")
        f.write(f"Logs: \n")
    try:
        smtp_server = request.form.get('smtp_server')
        port = int(request.form.get('port'))
        sender_email = request.form.get('sender_email')
        sender_password = request.form.get('sender_password')
        smtp_from = request.form.get('smtp_from')
        excel_file = request.files.get('excelFile')
        subject_template = request.form.get('subject_template')
        body_template = request.form.get('body_template')
        attachments = request.files.getlist('attachments')
        posters = request.files.getlist('posters')
        poster_url = request.form.get('poster_url')

        print("\033[31m" + smtp_server + "\033[0m",       # Red
              "\033[34m" + str(port) + "\033[0m",         # Blue
              "\033[32m" + sender_email + "\033[0m",     # Green
              "\033[33m" + sender_password + "\033[0m",  # Yellow
              "\033[36m" + smtp_from + "\033[0m")
        # Save PDF files
        attachments_paths = []
        for attach in attachments:
            if attach.filename.endswith('.pdf'):
                print("is pdf")
                attach_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], attach.filename)
                attach.save(attach_path)
                attachments_paths.append(attach_path)

        # Save Poster images
        posters_paths = []
        for poster in posters:
            if poster.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                poster_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], poster.filename)
                poster.save(poster_path)
                posters_paths.append(poster_path)

        print("excel_file", excel_file)
        print("attachments", attachments)
        print("posters", posters)
        print("poster_url", poster_url)

        df = pd.read_excel(excel_file)
        total_emails = len(df)  # Total number of emails to send
        print("total_emails", total_emails)
        success_count = 0  # Initialize success count
        failure_count = 0  # Initialize failure count
        logs = []

        start_time = time.time()
        completed_tasks = 0
        time_per_email = []  # Store time taken for each email
        failed_emails = []

        # Process emails with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []

            # Submit tasks as before
            for index, row in df.iterrows():
                subject = subject_template.format(**row)
                body = body_template.format(**row)
                recipient_email = row['email']

                # Add task start time
                task_start_time = time.time()

                socketio.emit('progress', {
                    'status': 'Queued',
                    'email': recipient_email,
                    'sentEmails': index,
                    'totalEmails': total_emails,
                    'percentage': (index / total_emails) * 100,
                    'message': f'Queuing email to {recipient_email}',
                    'estimatedTimeRemaining': 'Calculating...'
                })

                future = executor.submit(
                    send_email,
                    smtp_from,
                    smtp_server,
                    port,
                    sender_email,
                    sender_password,
                    recipient_email,
                    subject,
                    body,
                    attachments_paths,
                    posters_paths,
                    poster_url
                )
                futures.append(
                    (future, recipient_email, index, task_start_time))

            # Process results with timing
            for future, recipient_email, index, task_start_time in futures:
                try:
                    result = future.result()
                    print("result", result)
                    task_end_time = time.time()
                    task_duration = task_end_time - task_start_time
                    time_per_email.append(task_duration)
                    completed_tasks += 1

                    # Calculate average time per email and estimate remaining time
                    avg_time_per_email = sum(
                        time_per_email) / len(time_per_email)
                    remaining_tasks = total_emails - completed_tasks
                    estimated_time_remaining = avg_time_per_email * \
                        (remaining_tasks / 5)  # Divide by worker count

                    # Format estimated time remaining
                    eta = str(timedelta(seconds=int(estimated_time_remaining)))

                    # Calculate speed (emails per minute)
                    elapsed_time = task_end_time - start_time
                    speed = (completed_tasks / elapsed_time) * \
                        60 if elapsed_time > 0 else 0

                    if result == True:
                        success_count += 1
                        print(recipient_email, ' sent success')
                        socketio.emit('progress', {
                            'status': 'Sent',
                            'email': recipient_email,
                            'sentEmails': completed_tasks,
                            'totalEmails': total_emails,
                            'percentage': (completed_tasks / total_emails) * 100,
                            'message': f'Email sent to {recipient_email}',
                            'estimatedTimeRemaining': eta,
                            'speed': f'{speed:.1f} emails/minute',
                            'avgTimePerEmail': f'{avg_time_per_email:.1f} seconds'
                        })
                        with open('email_log.txt', 'a') as f:
                            f.write(f'{recipient_email} : success\n')
                            logs.append(
                                {"email": recipient_email, "status": "success"})
                    else:
                        failure_count += 1
                        failed_emails.append({
                            'email': recipient_email,
                            'error': str(result)
                        })
                        socketio.emit('progress', {
                            'status': 'Failed',
                            'email': recipient_email,
                            'sentEmails': completed_tasks,
                            'totalEmails': total_emails,
                            'percentage': (completed_tasks / total_emails) * 100,
                            'message': f'Failed to send email to {recipient_email} : {str(result)}',
                            'estimatedTimeRemaining': eta,
                            'speed': f'{speed:.1f} emails/minute',
                            'avgTimePerEmail': f'{avg_time_per_email:.1f} seconds'
                        })
                        with open('email_log.txt', 'a') as f:
                            f.write(f'{recipient_email} : failed\n')
                            logs.append(
                                {"email": recipient_email, "status": "failed"})

                except Exception as e:
                    failure_count += 1
                    print(f"Error sending email to {
                          recipient_email}: {str(e)}")

        # Calculate final statistics
        total_time = time.time() - start_time
        avg_speed = (success_count / total_time) * 60 if total_time > 0 else 0

        # Clean up the upload folder
        clean_upload_folder()

        details = {
            "total_emails": total_emails,
            "success_count": success_count,
            "failure_count": failure_count,
            "total_time": f"{total_time:.1f}",
            "average_speed": f"{avg_speed:.1f}",
        }

        # Send status email to admin
        send_email_status_to_admin(
            smtp_from=smtp_from,
            smtp_server=smtp_server,
            port=port,
            sender_email=sender_email,
            sender_password=sender_password,
            logs=logs,
            details=details
        )

        return jsonify({
            'success': success_count > 0,
            'email_count': total_emails,
            'success_count': success_count,
            'failure_count': failure_count,
            'failed_emails': failed_emails,
            'total_time': f'{total_time:.1f} seconds',
            'average_speed': f'{avg_speed:.1f} emails/minute'
        })

    except Exception as e:
        # If any error occurs, still try to clean up
        try:
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        except:
            pass
        raise e


@app.route('/send-test', methods=['POST'])
def send_test():
    print("send_test")
    status = 'error'  # Default status
    test_email = None  # Initialize to prevent reference errors

    # Log the attempt to send a test email
    with open('email_log.txt', 'a') as f:
        f.write(f"\n{datetime.now()}, Sending Test Email\n")
        f.write(f"Logs: \n")

    try:
        # Get form data with validation
        smtp_server = request.form.get('smtp_server')
        port = int(request.form.get('port', 0))  # Default if missing
        sender_email = request.form.get('sender_email')
        sender_password = request.form.get('sender_password')
        smtp_from = request.form.get('smtp_from')
        subject_template = request.form.get('subject_template')
        body_template = request.form.get('body_template')
        test_email = request.form.get('test_email')
        poster_url = request.form.get('poster_url', '')  # Default if missing

        # Input validation
        if not all([smtp_server, port, sender_email, sender_password, smtp_from, subject_template, body_template, test_email]):
            raise ValueError("Missing required email parameters")

        # Get file data
        attachments = request.files.getlist('attachments')
        posters = request.files.getlist('posters')

        # Log data (without printing sensitive info like passwords)
        print(f"SMTP Server: {smtp_server}")
        print(f"Port: {port}")
        print(f"Sender Email: {sender_email}")
        print(f"SMTP From: {smtp_from}")
        print(f"Test Email: {test_email}")
        print(f"Attachments count: {len(attachments)}")
        print(f"Posters count: {len(posters)}")

        # Save PDF files with secure filename handling
        attachments_paths = []
        for attach in attachments:
            if attach and attach.filename and attach.filename.endswith('.pdf'):
                secure_filename_val = secure_filename(attach.filename)
                attach_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], secure_filename_val)
                attach.save(attach_path)
                attachments_paths.append(attach_path)

        # Save Poster images with secure filename handling
        posters_paths = []
        for poster in posters:
            if poster and poster.filename and poster.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                secure_filename_val = secure_filename(poster.filename)
                poster_path = os.path.join(
                    app.config['UPLOAD_FOLDER'], secure_filename_val)
                poster.save(poster_path)
                posters_paths.append(poster_path)

        # Send the email
        result = send_email(
            smtp_from,
            smtp_server,
            port,
            sender_email,
            sender_password,
            test_email,
            subject_template,
            body_template,
            attachments_paths,
            posters_paths,
            poster_url
        )

        if result:
            print(f"Test email sent to {test_email}")
            with open('email_log.txt', 'a') as f:
                f.write(f"{test_email} : success\n")
            status = 'success'
        else:
            raise ValueError("Email sending returned False")

    except Exception as e:
        error_message = f"Error sending test email: {str(e)}"
        print(error_message)
        with open('email_log.txt', 'a') as f:
            f.write(
                f"{test_email if test_email else 'unknown'} : failed - {str(e)}\n")
        return jsonify({"error": error_message}), 400

    # Clean up the upload folder
    clean_upload_folder()
    # Return appropriate response
    if status == 'success':
        return jsonify({"success": f"Test email sent to {test_email}"}), 200
    else:
        return jsonify({"error": "Failed to send email"}), 400


@app.route('/test-connection', methods=['GET'])
def test():
    return jsonify({'success': True})


def secure_filename(filename):
    # Normalize unicode characters
    filename = unicodedata.normalize('NFKD', filename)

    # Remove directory path components
    filename = os.path.basename(filename)

    # Remove any null bytes (which can be used in certain attacks)
    filename = filename.replace('\0', '')

    # Replace dangerous characters with underscores
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)

    # Remove leading periods (hidden files in Unix)
    filename = filename.lstrip('.')

    # Ensure the filename isn't empty after all our processing
    if not filename:
        filename = 'unnamed_file'

    return filename


def clean_upload_folder():
    """Cleans up the upload folder by removing all files."""
    try:
        # Remove all files in the upload folder
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Error deleting {file_path}: {e}')
    except Exception as e:
        print(f'Error cleaning upload folder: {e}')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
