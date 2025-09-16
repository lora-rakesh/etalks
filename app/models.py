from django.db import models
from django.core.validators import RegexValidator
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from app.manager import UserManager
from django.db.models import ImageField
from .validators import StrongPasswordValidator
from django.contrib.auth.models import User
from django.conf import settings

#------------------------------------------------------------- Company Check #

from django.utils.text import slugify

class Company_check(models.Model):
    company_name = models.CharField(max_length=500, null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    logo = models.ImageField(upload_to="company_logos/", null=True, blank=True)  # ✅ Logo
    def save(self, *args, **kwargs):
        if not self.slug and self.company_name:
            self.slug = slugify(self.company_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.company_name or "Unnamed Company"


#------------------------------------------------------------- Roles #

ROLE_TYPE = (
    ('Manager', "Manager"),
    ('HR', "HR"),
    ('Employee', "Employee")
)

#------------------------------------------------------------- Custom User #
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractUser):
    username = None
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True,default="")
    role = models.CharField(choices=ROLE_TYPE, max_length=100, error_messages={'required': "Role must be provided"})
    employee_id = models.CharField(max_length=100, unique=True, db_index=True)
    email = models.EmailField(max_length=254, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    is_first_login = models.BooleanField(default=True)

    # 🔹 New Fields
    failed_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    unlock_requested = models.BooleanField(default=False)  # ✅ User requests HR unlock
    is_locked = models.BooleanField(default=False)
    lock_expires_at = models.DateTimeField(null=True, blank=True)
    USERNAME_FIELD = "employee_id"
    REQUIRED_FIELDS = ['email']

    def __str__(self):
                # Show employee ID, name, and company
        company_name = self.company.company_name if self.company else "No Company"
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{self.employee_id} - {full_name}"# ✅ Shows ID and Name in dropdowns

    def save(self, *args, **kwargs):
        if self.first_name == 'unknown' or not self.first_name:
            full_name = f"{self.first_name} {self.last_name}".strip()
            self.name = full_name if full_name else self.email.split('@')[0]
        super().save(*args, **kwargs)

    objects = UserManager()

    def lock_account(self):
        from datetime import timedelta
        self.is_locked = True
        self.lock_expires_at = timezone.now() + timedelta(minutes=15)
        self.save()

    def unlock_account(self):
        self.is_locked = False
        self.failed_attempts = 0
        self.lock_expires_at = None
        self.save()

    def check_lock_status(self):
        """Check if lock period expired and auto-unlock"""
        if self.is_locked and self.lock_expires_at:
            if timezone.now() >= self.lock_expires_at:
                # unlock automatically if time expired
                self.unlock_account()
                return False  # not locked anymore
            return True  # still locked
        return False  # not locked
class UnlockRequest(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)   # locked employee
    requested_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        "CustomUser", on_delete=models.SET_NULL, null=True, blank=True, related_name="resolved_unlocks"
    )
    hr = models.ForeignKey(   # HR who will unlock
        "CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_unlock_requests"
    )

    def __str__(self):
        return f"Unlock request for {self.user.username}"




#------------------------------------------------------------- Notification #

class Notification(models.Model):
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    def __str__(self):
        return f"Notification for {self.recipient.employee_id}: {self.message[:5]}"


#------------------------------------------------------------- Holiday #

class Holiday(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True)
    day = models.CharField(max_length=500, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True, blank=True, related_name='holidays')
    def __str__(self):
        return self.name
    


#------------------------------------------------------------- Employee #
from django.db import models
from .utils import EncryptedCharField  # ✅ Only import what you actually use

class Employee(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True, blank=True, related_name='employees')
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default="")
    designation = models.CharField(max_length=50)
    department = models.CharField(max_length=50)
    uan_number = EncryptedCharField(max_length=20, unique=True, verbose_name="UAN Number")
    pan_number = EncryptedCharField(max_length=20, unique=True, verbose_name="PAN Number")
    pf_number = models.CharField(max_length=30, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=30, null=True, blank=True)
    phone_number = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\+?\d{10,15}$')], null=True, blank=True)
    reporting_manager = models.CharField(max_length=100, null=True, blank=True)
    employee_type = models.CharField(max_length=20, choices=[('Full-time', 'Full-time'), ('Part-time', 'Part-time'), ('Contract', 'Contract')], null=True, blank=True)
    work_location = models.CharField(max_length=20, choices=[('On-site', 'On-site'), ('Remote', 'Remote'), ('Hybrid', 'Hybrid')], null=True, blank=True)
    bank_account_number = EncryptedCharField(max_length=20, null=True, blank=True, verbose_name="Bank Account Number")
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    ifsc_code = models.CharField(max_length=11, null=True, blank=True)
    aadhar_number = EncryptedCharField(max_length=12, unique=True, null=True, blank=True, verbose_name="Aadhar Number")
    
    def save(self, *args, **kwargs):
        if not self.employee_id and self.user:
            self.employee_id = self.user.employee_id
        if not self.company and self.user:
            self.company = self.user.company  # 👈 This line should exist
        super(Employee, self).save(*args, **kwargs)

    def __str__(self):
        return self.first_name or self.user.employee_id


#------------------------------------------------------------- Salary #

class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField()
    current_month_calculated_days = models.IntegerField(blank=True, null=True)
    current_month_paid_days = models.IntegerField(blank=True, null=True)
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2)
    house_rent_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    special_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    conveyance_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    total_fixed_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)

    pf_contribution = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    professional_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)

    performance_bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)
    other_incentives = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)

    medical_insurance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, null=True, blank=True)
    stationery_misc = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    total_variable_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    per_day_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    actual_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    loan_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)

    def save(self, *args, **kwargs):
        self.total_fixed_salary = self.basic_salary + self.house_rent_allowance + self.special_allowance + self.conveyance_allowance
        self.deductions = self.pf_contribution + (self.professional_tax or 0) + (self.medical_insurance or 0) + (self.stationery_misc or 0) + (self.income_tax or 0)
        self.total_variable_pay = (self.performance_bonus or 0) + (self.other_incentives or 0)
        self.gross_salary = self.total_fixed_salary + self.deductions
        self.net_salary = self.total_fixed_salary - self.total_variable_pay
        if self.current_month_calculated_days:
            self.per_day_salary = self.net_salary / self.current_month_calculated_days
            self.actual_salary = self.per_day_salary * (self.current_month_paid_days or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.month.strftime('%B %Y')}"



#------------------------------------------------------------- TimeEntry #

class TimeEntry(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    clock_in_time = models.DateTimeField(null=True, blank=True)
    clock_out_time = models.DateTimeField(null=True, blank=True)
    clock_in_latitude = models.FloatField(null=True, blank=True)
    clock_in_longitude = models.FloatField(null=True, blank=True)
    clock_out_latitude = models.FloatField(null=True, blank=True)
    clock_out_longitude = models.FloatField(null=True, blank=True)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True, blank=True, related_name='time_entries')

    def __str__(self):
        return f"{self.user.employee_id} - Clock In: {self.clock_in_time} - Clock Out: {self.clock_out_time}"


#------------------------------------------------------------- Muster #

REASON_TYPE = (
    ('On-site', "On-site"),
    ('Forgot Login/out', "Forgot Login/out"),
    ('Forgot Logout', "Forgot Logout"),
    ('Network Issue', "Network Issue"),
    ('Work From Home', "Work From Home"),
)

class Muster(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=100)
    date = models.DateTimeField()
    clock_in_time = models.DateTimeField()
    clock_out_time = models.DateTimeField()
    reason = models.CharField(choices=REASON_TYPE, max_length=150, blank=True, null=True)
    notes = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leave Application by {self.employee_id} - {self.reason} on {self.date.strftime('%d-%m-%Y')}"


#------------------------------------------------------------- Leave & Balance #

class Leave(models.Model):
    employee = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    advance_privilege_leave = models.IntegerField(default=6)
    sick_leave = models.IntegerField(default=6)
    casual_leave = models.IntegerField(default=6)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True, blank=True, related_name='leave')

    def __str__(self):
        return f"{self.employee.employee_id} Leave Balance"

    def update_balance(self, leave_type, days_requested, start_date, end_date):
        weekdays_requested = sum(1 for i in range((end_date - start_date).days + 1)
                                 if (start_date + timedelta(days=i)).weekday() < 5)

        if leave_type == 'advance_privilege':
            self.advance_privilege_leave = max(0, self.advance_privilege_leave - weekdays_requested)
        elif leave_type == 'sick':
            self.sick_leave = max(0, self.sick_leave - weekdays_requested)
        elif leave_type == 'casual':
            self.casual_leave = max(0, self.casual_leave - weekdays_requested)

        self.save()
        return weekdays_requested


class LeaveRequest(models.Model):
    LEAVE_CHOICES = [
        ('advance_privilege', 'Advance Privilege Leave'),
        ('sick', 'Sick Leave'),
        ('casual', 'Casual Leave'),
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=20, choices=LEAVE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    days_requested = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Leave request for {self.employee.employee_id} ({self.leave_type})"


#------------------------------------------------------------- Expense Claims #

class ExpenseClaim(models.Model):
    CATEGORY_CHOICES = [
        ('Travel Expense', 'Travel Expense'),
        ('Food Expense', 'Food Expense'),
        ('Accommodation', 'Accommodation'),
        ('Team Lunch', 'Team Lunch'),
        ('Other', 'Other')
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bill_no = models.CharField(max_length=50, blank=True, null=True)
    receipt = models.FileField(upload_to='expense_receipts/')
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')

    def __str__(self):
        return f"{self.employee} - {self.category} - {self.date}"


#------------------------------------------------------------- Loan Requests #

class LoanRequest(models.Model):
    LOAN_TYPE_CHOICES = [
        ('Personal Loan', 'Personal Loan'),
        ('Home Loan', 'Home Loan'),
        ('Education Loan', 'Education Loan')
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    loan_type = models.CharField(max_length=50, choices=LOAN_TYPE_CHOICES)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    repayment_duration = models.IntegerField()
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    date_requested = models.DateTimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.employee_id} - {self.loan_type} ({self.status})"

    def get_approve_url(self):
        return f"/loan-requests/approve/{self.id}/"

    def get_reject_url(self):
        return f"/loan-requests/reject/{self.id}/"


#------------------------------------------------------------- Task Management #

from django.db import models

class Team(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(CustomUser, related_name='teams')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE) 
    
    class Meta:
        unique_together = ('name', 'created_by')  # Team names unique per creator

    def __str__(self):
        return self.name

class Task(models.Model):
    name = models.CharField(max_length=255, default='No Task Name')
    assigned_to = models.ManyToManyField(CustomUser, related_name="tasks")
    assigned_team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name="team_tasks")
    due_date = models.DateField()
    start_date = models.DateField()  # New field
    completed = models.BooleanField(default=False)
    company = models.ForeignKey(Company_check, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="tasks_created", null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['due_date']


#------------------------------------------------------------- Performance #

'''class Performance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    performance_score = models.IntegerField()
    date = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['-date']'''


from django.db import models
from django.conf import settings
 
class EmployeeMedia(models.Model):
    employee = models.OneToOneField('Employee', on_delete=models.CASCADE, related_name='media')
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True, default='profile_pictures/default_profile.jpg')
    cover_picture = models.ImageField(upload_to='cover_pictures/', null=True, blank=True, default='cover_pictures/default_cover.jpg')
 
    def __str__(self):
        return f"{self.employee.first_name} - Media"
 

#------------------------------------------------------------- HR4U #

# models.py

from django.db import models
from app.models import Employee  # Adjust path if needed

class HRContact(models.Model):
    ROLE_CHOICES = [
        ('TL', 'Team Leader'),
        ('HR', 'HR'),
        ('MG', 'Manager'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    

    role = models.CharField(max_length=2, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.employee.first_name} {{self.employee.last_name}} ({self.get_role_display()})"

    @property
    def name(self):
        return self.employee.first_name

    @property
    def email(self):
        return self.employee.user.email


# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class HelpDeskTicket(models.Model):
    CATEGORY_CHOICES = [
        ('HR', 'HR Support'),
        ('IT', 'IT Support'),
        ('AS', 'Asset Support'),  # Changed from "Assessment"
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    # Separate issue choices for each category
    HR_ISSUE_CHOICES = [
        ('attendance', 'Attendance Issue'),
        ('payroll', 'Payroll Issue'),
        ('leave', 'Leave Request'),
        ('policy', 'Policy Clarification'),
        ('other', 'Other HR Issue'),
    ]

    IT_ISSUE_CHOICES = [
        ('login', 'Login Problem'),
        ('hardware', 'Hardware Issue'),
        ('software', 'Software Problem'),
        ('network', 'Network Issue'),
        ('other', 'Other IT Issue'),
    ]

    AS_ISSUE_CHOICES = [ 
        ('laptop', 'Laptop Not Working'),
        ('mouse', 'Mouse Not Working'),
        ('keyboard', 'Need New Equipment'),
        ('return', 'Return Asset Request'),
        ('other', 'Other Asset Issue'),
    ]

    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=2, choices=CATEGORY_CHOICES)
    issue_type = models.CharField(max_length=100)
    description = models.TextField()

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='tl_tickets', null=True, blank=True)
    escalate_to_hr = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='hr_tickets', null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='manager_tickets', null=True, blank=True)

    viewed_by_tl = models.BooleanField(default=False)
    viewed_by_hr = models.BooleanField(default=False)

    escalated_to_hr_at = models.DateTimeField(null=True, blank=True)
    escalated_to_manager_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.issue_type} ({self.employee})"






#------------------------------------------------------------- Training #

from django.db import models
from django.conf import settings

class TrainingTopic(models.Model):
    title = models.CharField(max_length=200)
    topic_link = models.URLField(verbose_name="Link to topic")  # ✅ Add this line
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    company = models.ForeignKey('app.Company_check', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class LoggedInUser(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40, blank=True, null=True)
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

fernet = Fernet(settings.ENCRYPTION_KEY)

class LoginLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    _ip_address = models.BinaryField(db_column="ip_address")
    _device_info = models.BinaryField(db_column="device_info")
    ip_hash = models.CharField(max_length=64, blank=True)
    login_time = models.DateTimeField(auto_now_add=True)

    @property
    def ip_address(self):
        return fernet.decrypt(self._ip_address).decode()

    @ip_address.setter
    def ip_address(self, value):
        self._ip_address = fernet.encrypt(value.encode())
        self.ip_hash = hashlib.sha256(value.encode()).hexdigest()

    @property
    def device_info(self):
        return fernet.decrypt(self._device_info).decode()

    @device_info.setter
    def device_info(self, value):
        self._device_info = fernet.encrypt(value.encode())

    def __str__(self):
        return f"{self.user} - {self.ip_address} - {self.device_info[:30]}"


#------------------------------------------------------------- Resignation #
class ResignationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resignations')
    resignation_date = models.DateField()
    last_working_day = models.DateField()
    resignation_reason = models.CharField(max_length=100)
    other_reason = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    resignation_letter = models.FileField(upload_to='resignation_letters/', blank=True, null=True)
    signature_data = models.TextField(help_text="Base64 image of signature", blank=True, null=True)
    agreement = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Resignation by {self.employee.get_full_name()} on {self.submitted_at.date()}"



#--------------------------------------------------------------Career development#
 
from django.db import models
from django.utils.text import slugify
 
class SkillCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
 
    def __str__(self):
        return self.name
 
from django.db import models
from django.utils.text import slugify

class CareerResource(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    detail_content = models.TextField()
    category = models.ForeignKey('SkillCategory', on_delete=models.CASCADE)
    company = models.ForeignKey('app.Company_check', on_delete=models.CASCADE, null=True, blank=True)
    uploaded_file = models.FileField(upload_to='career_resources/files/', null=True, blank=True)
    video_link = models.URLField(max_length=500, null=True, blank=True)

    def _generate_unique_slug(self):
        """
        Generate a unique slug from title, appending a number if needed.
        """
        base_slug = slugify(self.title)
        slug = base_slug
        num = 1
        while CareerResource.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{num}"
            num += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question
from django.db import models
from django.conf import settings
class Message(models.Model):
    room = models.CharField(max_length=255)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_messages"
    )
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.content[:20]}"


# -------------------------------
# Call Model (Audio/Video)
# -------------------------------
class Call(models.Model):
    CALL_TYPES = (
        ("audio", "Audio"),
        ("video", "Video"),
    )
    caller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="outgoing_calls"
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incoming_calls"
    )
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[("ongoing", "Ongoing"), ("ended", "Ended"), ("missed", "Missed")],
        default="ongoing"
    )

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.call_type.title()} Call ({self.caller} → {self.receiver}) [{self.status}]"