"""
Email Setup and Notification Module

This module provides functions to set up email configurations and send email notifications.

Functions:
    send_email(too_email, subject, body): Sends an email to the specified recipients.
    notify_success(subject, body): Sends a success notification email.
    notify_failure(subject, body): Sends a failure notification email.
"""

# Standard library imports (for sending emails)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Application-specific imports from our application(for email configuration details)
from App.email_configurations import (
    RECEIVER_EMAIL,
    ERROR_HANDLING_GROUP_EMAIL,
    SENDER_EMAIL,
    PASSWORD,
    SMTP_SERVER,
    SMTP_PORT
)


def send_email(too_email, subject, body):
    """
    This function is used to send emails whenever there are changes in CRUD operations
    :param too_email: list of email addresses needed to be sent
    :param subject: The subject of the email
    :param body: The message which user needs to be notified
    :return: None
    """
    if too_email is None:
        too_email = []

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(too_email)
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, PASSWORD)
        server.sendmail(SENDER_EMAIL, too_email, msg.as_string())


def notify_success(subject, body):
    """
       Sends an email notification for successful operations.

       :param subject: Subject of the success email.
       :param body: Body content of the success email.
       :return: None
       """
    send_email(RECEIVER_EMAIL, subject, body)


def notify_failure(subject, body):
    """
        Sends an email notification for failed operations.

        :param subject: Subject of the failure email.
        :param body: Body content of the failure email.
        :return: None
        """
    send_email(ERROR_HANDLING_GROUP_EMAIL, subject, body)


def format_enquiries_for_email(enquiries_data):
    """
    Helper function to format the enquiries data for email content.
    :param enquiries_data: List of dictionaries containing enquiry details.
    :return: A formatted string with enquiry details for email content.
    """
    formatted_enquiries = ""
    for enquiry in enquiries_data:
        formatted_enquiries += f"""
        Customer Name: {enquiry['CustomerName']}
        Gender: {enquiry['Gender']}
        Age: {enquiry['Age']}
        Mobile No: {enquiry['MobileNo']}
        Email: {enquiry['Email']}
        Vehicle Model: {enquiry['VehicleModel']}
        State: {enquiry['State']}
        District: {enquiry['District']}
        City: {enquiry['City']}
        Lead ID: {enquiry['LeadId']}
        Created Date: {enquiry['CreatedDate']}
        Purchased: {'Yes' if enquiry['IsPurchased'] else 'No'}
        ---------------------------
        """
    return formatted_enquiries


def format_dealers_for_email(dealers_data):
    """
    Formats dealer data for inclusion in an email.

    This function takes a list of dealer records and formats them into a human-readable
    string that can be included in an email body. Each dealer's information is presented
    in a tabular format for clarity.

    Parameters:
        - dealers_data (list of dict): List of dictionaries containing dealer codes and names.

    Returns:
        - str: A formatted string representing the dealer data.
    """
    if not dealers_data:
        return "No dealer data available."

    # Header for the dealer list
    formatted_data = "Dealer Code | Dealer Name\n"
    formatted_data += "-" * 40 + "\n"

    # Format each dealer's information
    for dealer in dealers_data:
        # Ensure that dealer_code and dealer_name are strings
        dealer_code = str(dealer.get('dealercode', 'N/A')).strip()
        dealer_name = str(dealer.get('dealername', 'N/A')).strip()
        formatted_data += f"{dealer_code.ljust(15)} |       {dealer_name}\n"

    return formatted_data
