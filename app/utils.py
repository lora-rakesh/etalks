


from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse



from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

# def send_approval_email(request, muster_entry, recipient_email):
#     # Generate the approval link
#     token = muster_entry.approval_token
#     approval_url = f"http://{get_current_site(request).domain}/lora/muster/approve/{token}/"

#     # Prepare the email content (plain text version)
#     subject = "Muster Approval Request"
#     message = f"""
#     Muster Approval Request

#     Please review the following muster entry:

#     Employee ID: {muster_entry.employee_id}
#     Name: {muster_entry.name}
#     Date: {muster_entry.date}
#     Check-In: {muster_entry.check_in_time}
#     Check-Out: {muster_entry.check_out_time}
#     Reason: {muster_entry.reason}
#     Notes: {muster_entry.notes}

#     Click here to approve the muster entry: {approval_url}
#     """

#     # Send the email
#     send_mail(
#         subject,
#         message,
#         settings.EMAIL_HOST_USER,  # Sender's email address
#         [recipient_email],  # Recipient's email address
#         fail_silently=False
#     )




# def send_approval_email(request, muster_entry, recipient_email):
#     # Generate the approval and rejection links with the approval token
#     approve_url = request.build_absolute_uri(reverse('approve_muster', kwargs={'token': muster_entry.approval_token}))
#     reject_url = request.build_absolute_uri(reverse('reject_muster', kwargs={'token': muster_entry.approval_token}))

#     subject = f"Approval Request for Muster Entry - {muster_entry.name}"
#     message = f"""
#     Hi,

#     A muster entry has been submitted for approval.

#     Employee Name: {muster_entry.name}
#     Employee ID: {muster_entry.employee_id}
#     Date: {muster_entry.date}
#     Reason: {muster_entry.reason}
#     Notes: {muster_entry.notes}

#     To approve or reject the muster entry, please click on one of the following links:
    
#     Approve: {approve_url}
#     Reject: {reject_url}

#     Thank you.
#     """
#     send_mail(subject, message, settings.EMAIL_HOST_USER, [recipient_email])




# def send_muster_request_email(request, muster_request):
#     # Generate the approve and reject URLs for the admin
#     approve_url = f"{get_current_site(request).domain}{reverse('approve_muster', args=[muster_request.id])}"
#     reject_url = f"{get_current_site(request).domain}{reverse('reject_muster', args=[muster_request.id])}"

#     # Prepare the email content
#     subject = f"Muster Request from {muster_request.employee.name}"
#     message = f"""
#     A new muster request has been submitted by {muster_request.employee.name}:

#     Date: {muster_request.date}
#     Check-In: {muster_request.check_in}
#     Check-Out: {muster_request.check_out}
#     Reason: {muster_request.reason}
#     Notes: {muster_request.notes}

#     Please approve or reject the muster request:

#     Approve: {approve_url}
#     Reject: {reject_url}
#     """

#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,
#         [settings.EMAIL_HOST_USER],  # Admin email (configured in settings)
#         fail_silently=False
#     )



# utils.py

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string

# def send_muster_approve_mail(muster_request):
#     # Prepare the subject and message for the email
#     subject = f"Muster Request for {muster_request.employee.name} - Action Required"
#     approve_url = reverse('approve_muster', args=[muster_request.id])
#     reject_url = reverse('reject_muster', args=[muster_request.id])
    
#     # Prepare the body of the email
#     context = {
#         'employee_name': muster_request.employee.name,
#         'employee_id': muster_request.employee.emp_id,
#         'date': muster_request.date,
#         'check_in': muster_request.check_in,
#         'check_out': muster_request.check_out,
#         'reason': muster_request.reason,
#         'notes': muster_request.notes,
#         'approve_url': approve_url,
#         'reject_url': reject_url,
#     }
    
#     message = render_to_string('muster_approval_email.html', context)

#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,  # From email
#         ['loraemployee@gmail.com'],  # To email (you can replace this with the actual admin email)
#         fail_silently=False,
#     )


def send_approval_email(request, muster_entry, recipient_email):
    # Generate the approval link
    token = muster_entry.approval_token
    approval_url = f"http://{get_current_site(request).domain}/lora/muster/approve/{token}/"

    # Prepare the email content (plain text version)
    subject = "Muster Approval Request"
    message = f"""
    Muster Approval Request

    Please review the following muster entry:

    Employee ID: {muster_entry.employee_id}
    Name: {muster_entry.name}
    Date: {muster_entry.date}
    Check-In: {muster_entry.check_in_time}
    Check-Out: {muster_entry.check_out_time}
    Reason: {muster_entry.reason}
    Notes: {muster_entry.notes}

    Click here to approve the muster entry: {approval_url}
    """

    # Send the email
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,  # Sender's email address
        [recipient_email],  # Recipient's email address
        fail_silently=False
    )



def send_leave_request_email(request, leave_request):
    # Generate the approve and reject URLs for the admin
    approve_url = f"{get_current_site(request).domain}{reverse('approve_leave', args=[leave_request.id])}"
    reject_url = f"{get_current_site(request).domain}{reverse('reject_leave', args=[leave_request.id])}"

    # Prepare the email content
    subject = f"Leave Request from {leave_request.employee.employee_id}"
    message = f"""
    A new leave request has been submitted by {leave_request.employee.employee_id}:

    Leave Type: {leave_request.leave_type}
    Start Date: {leave_request.start_date}
    End Date: {leave_request.end_date}
    Reason: {leave_request.reason}

    Please approve or reject the leave request:

    Approve: {approve_url}
    Reject: {reject_url}
    """

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.EMAIL_HOST_USER],  # Admin email (you can configure this in settings)
        fail_silently=False
    )



# def send_loan_request_email(loan_request):
#     # Loan request details
#     employee_name = loan_request.employee.name  # Assuming the Employee model has a name field
#     loan_type = loan_request.loan_type
#     loan_amount = loan_request.loan_amount
#     repayment_duration = loan_request.repayment_duration
#     interest_rate = loan_request.interest_rate

#     # Email subject and body
#     subject = f"Loan Request: {loan_type} - {employee_name}"
#     message = f"""
#     Dear Admin,

#     A new loan request has been submitted. Here are the details:

#     Employee: {employee_name}
#     Loan Type: {loan_type}
#     Loan Amount: ${loan_amount}
#     Repayment Duration: {repayment_duration} months
#     Interest Rate: {interest_rate}%

#     Please review the request and click the appropriate link below to approve or reject:

#     Approve: {loan_request.get_approve_url()}
#     Reject: {loan_request.get_reject_url()}

#     Regards,
#     Your Company
#     """

#     # Send email to your Gmail account
#     send_mail(
#         subject,
#         message,
#         settings.DEFAULT_FROM_EMAIL,  # This should be configured in your settings.py
#         [settings.ADMIN_EMAIL],  # Your Gmail address
#     )

from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

def send_loan_request_email(request, loan_request):

    approve_url = f"http://{get_current_site(request).domain}/approve_loan_request/{loan_request.id}/"
    reject_url = f"http://{get_current_site(request).domain}/reject_loan_request/{loan_request.id}/"

    # Prepare the email content (plain text version)
    subject = f"Loan Request: {loan_request.loan_type} - {loan_request.employee.first_name} {loan_request.employee.last_name}"
    message = f"""
    Loan Request Details:

    Employee: {loan_request.employee.first_name} {loan_request.employee.last_name}
    Loan Type: {loan_request.loan_type}
    Loan Amount: ${loan_request.loan_amount}
    Repayment Duration: {loan_request.repayment_duration} months
    Interest Rate: {loan_request.interest_rate}%
    Date Requested: {loan_request.date_requested}

    Please review the request and click the appropriate link below to approve or reject:

    Approve: {approve_url}
    Reject: {reject_url}
    """

    # Send the email
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,  # Sender's email address
        [settings.EMAIL_HOST_USER],  # Recipient's email address (admin's email)
        fail_silently=False
    )


def send_expense_claim_email(request, expense_claiming):
    # Generate the approval and rejection URLs
    approve_url = f"http://{get_current_site(request).domain}/approve_expense_claim_request/{expense_claiming.id}/"
    reject_url = f"http://{get_current_site(request).domain}/reject_expense_claim_request/{expense_claiming.id}/"

    # Prepare the email content (plain text version)
    subject = f"Expense Claim Request: {expense_claiming.category} - {expense_claiming.employee.first_name} {expense_claiming.employee.last_name}"
    message = f"""
    Expense Claim Request Details:

    Employee: {expense_claiming.employee.first_name} {expense_claiming.employee.last_name}
    Category Type: {expense_claiming.category}
    Date : {expense_claiming.date}
    Description: {expense_claiming.description}
    Amount: {expense_claiming.amount}
    Bill No: {expense_claiming.bill_no}

    
    Please review the request and click the appropriate link below to approve or reject:

    Approve: {approve_url}
    Reject: {reject_url}
    """

    # Send the email
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,  # Sender's email address
        [settings.EMAIL_HOST_USER],  # Recipient's email address (admin's email)
        fail_silently=False
    )
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
import base64

from cryptography.fernet import Fernet
from django.conf import settings
from cryptography.fernet import InvalidToken
from django.db import models

from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet, InvalidToken
import base64

class EncryptedCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        self.fernet = Fernet(settings.ENCRYPTION_KEY.encode())
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        if value:
            value = str(value).encode()
            return self.fernet.encrypt(value).decode()
        return value

    def from_db_value(self, value, expression, connection):
        if value:
            try:
                return self.fernet.decrypt(value.encode()).decode()
            except InvalidToken:
                return value  # Already decrypted or corrupted
        return value

    def to_python(self, value):
        if value and isinstance(value, str):
            try:
                return self.fernet.decrypt(value.encode()).decode()
            except InvalidToken:
                return value
        return value