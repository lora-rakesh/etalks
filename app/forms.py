from django import forms
from app.models import *
from app.forms import *
from django.contrib.auth.models import *
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from app.models import CustomUser
from django.contrib.auth.forms import PasswordChangeForm
import re
from django.core.exceptions import ValidationError


class ResetPasswordForm(forms.Form):
    employee_id = forms.CharField(label="Employee ID", max_length=50)
    old_password = forms.CharField(label="Old Password", widget=forms.PasswordInput)
    new_password = forms.CharField(label="New Password", widget=forms.PasswordInput)
    confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)
 
    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
 
        # Check if the new password and confirm password match
        if new_password != confirm_password:
            self.add_error('confirm_password', "The new password and confirm password do not match.")
       
        # Check for strong password requirements
        self.validate_password_strength(new_password)
 
        return cleaned_data
 
    def validate_password_strength(self, password):
        """
        Validates that the password meets the required strength criteria:
        - At least 8 characters
        - At least 1 uppercase letter
        - At least 1 special character
        - At least 1 number
        """
        errors = []
 
        # Check password length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
 
        # Check for at least 1 uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter.")
 
        # Check for at least 1 special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):  # Special characters
            errors.append("Password must contain at least one special character.")
 
        # Check for at least 1 number
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number.")
 
        # If there are any errors, combine them into one message
        if errors:
            # Combine all errors into a single string with line breaks
            error_message = " ".join(errors)
            self.add_error('new_password', error_message)
 


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=100)
    

# class ResetPasswordWithOTPForm(forms.Form):
#     email = forms.EmailField(label="Email")
#     otp = forms.CharField(label="OTP", max_length=6)
#     new_password = forms.CharField(label="New Password", widget=forms.PasswordInput)
#     confirm_password = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

#     def clean(self):
#         cleaned_data = super().clean()
#         new_password = cleaned_data.get('new_password')
#         confirm_password = cleaned_data.get('confirm_password')

#         if new_password != confirm_password:
#             raise forms.ValidationError("The new password and confirm password do not match.")
#         return cleaned_data
    
    
# class UserCreationForm(forms.ModelForm):
#     class Meta:
#         model = CustomUser
#         fields = '__all__'

#     def save(self, commit=True):
#         user = super(UserCreationForm, self).save(commit=False)
#         user.set_password(self.cleaned_data["password"])
#         if commit:
#             user.save()
#         return user

from django import forms
from django.core.exceptions import ValidationError
import re
from .models import CustomUser  # Make sure to import CustomUser model

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['employee_id', 'first_name','last_name', 'email', 'role', 'company', 'is_active', 'is_staff', 'is_first_login', 'password']
        
    def clean_password(self):
        password = self.cleaned_data.get("password")
        user = self.instance

        # Enforce password validation
        self.validate_password_strength(password, user)
        
        return password

    def validate_password_strength(self, password, user):
        # Check minimum length
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        
        # Check for at least one lowercase letter
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        
        # Check for special characters
        if not re.search(r'[@#$%^&+=]', password):
            raise ValidationError("Password must contain at least one special character (e.g., @, #, $, %, ^, &, +).")
        
        # Check that the password does not contain the username or employee ID
        if user.username and user.username in password:
            raise ValidationError("Password cannot contain your username.")
        if user.employee_id and user.employee_id in password:
            raise ValidationError("Password cannot contain your employee ID.")

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        password = self.cleaned_data["password"]
        user.set_password(password)  # Set the password after validation
        if commit:
            user.save()
        return user

from django import forms
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser

class UserEditForm(UserChangeForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text="Leave blank to keep current password"
    )

    class Meta:
        model = CustomUser
        fields = [
            'employee_id',
            'first_name',
            'last_name',
            'email',
            'role',
            'is_active',
            'is_staff',
            'is_superuser',
            'is_first_login',
            'password',
        ]  # deliberately not including 'company'


class FrontendUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Enter a strong password"
    )

    class Meta:
        model = CustomUser
        fields = [
            'employee_id',
            'first_name',
            'last_name',
            'email',
            'role',
            'is_active',
            'is_staff',
            'is_superuser',
            'is_first_login',
            'password'
        ]  # ✅ This order will now be reflected in the form
    
    def save(self, commit=True, company=None):
        user = super().save(commit=False)
        if company is not None:
            user.company = company
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    
class MusterForm(forms.ModelForm):
    class Meta:
        model = Muster
        fields = '__all__'
        


# class SalaryForm(forms.ModelForm):
#     class Meta:
#         model = Salary
#         fields = '__all__'



# class SalaryForm(forms.ModelForm):
#     employee_id = forms.CharField(max_length=50, required=True, label='Employee ID')  # Text input for employee ID
#     month = forms.DateField(
#         widget=forms.DateInput(attrs={'type': 'date'}),  # This makes the field a date input
#         required=True,
#         label='Month'
#     )

#     class Meta:
#         model = Salary
#         fields = ['employee_id', 'month', 'current_month_calculated_days', 'current_month_paid_days', 
#                   'basic_salary', 'house_rent_allowance', 'special_allowance', 'conveyance_allowance', 
#                   'pf_contribution', 'professional_tax', 'income_tax', 'performance_bonus', 
#                   'other_incentives', 'medical_insurance', 'stationery_misc', 'deductions', 
#                   'gross_salary', 'net_salary', 'total_variable_pay', 'per_day_salary', 'actual_salary', 
#                   'loan_deductions']
#         exclude = ['employee']  # We won't use the Employee field directly here.

#     def clean_employee_id(self):
#         employee_id = self.cleaned_data['employee_id']
#         try:
#             employee = Employee.objects.get(employee_id=employee_id)  # Check if the employee exists
#         except Employee.DoesNotExist:
#             raise forms.ValidationError("Employee with this ID does not exist.")
#         return 

class SalaryForm(forms.ModelForm):
    employee_id = forms.CharField(max_length=50, required=True, label='Employee ID')

    month = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True,
        label='Month'
    )

    class Meta:
        model = Salary
        exclude = ['employee']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:  # Editing existing salary
            self.fields.pop('employee_id')  # Remove employee_id field

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        try:
            employee = Employee.objects.get(employee_id=employee_id)
        except Employee.DoesNotExist:
            raise forms.ValidationError("Employee with this ID does not exist.")
        self.cleaned_data['employee'] = employee
        return employee_id

    def save(self, commit=True):
        salary = super().save(commit=False)
        if 'employee' in self.cleaned_data:
            salary.employee = self.cleaned_data['employee']
        if commit:
            salary.save()
        return salary


# class EmployeeProfileForm(forms.ModelForm):
#     class Meta:
#         model = Employee
#         fields = '__all__'




from django import forms
from django.core.exceptions import ValidationError
from .models import Employee
from .utils import EncryptedCharField  # where Fernet encryption is defined

class EmployeeProfileForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ['user', 'company_name']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        unique_fields = ['uan_number', 'pan_number', 'aadhar_number']

        for field_name in unique_fields:
            field_value = cleaned_data.get(field_name)
            if field_value:
                # Loop through all other employees and decrypt to compare
                for emp in Employee.objects.exclude(pk=self.instance.pk):
                    try:
                        existing_value = getattr(emp, field_name)
                        if existing_value == field_value:  # __eq__ works after decryption
                            self.add_error(
                                field_name,
                                f"This {field_name.replace('_', ' ').title()} is already in use by another employee."
                            )
                            break
                    except Exception:
                        pass

        return cleaned_data


class Company_checkForm(forms.ModelForm):
    class Meta:
        model = Company_check
        fields = '__all__'


class HolidaysForm(forms.ModelForm):
    class Meta:
        model = Holiday
        exclude = ['company']
    date=forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

# class LeaveForm(forms.ModelForm):
#     class Meta:
#         model = Leave
#         fields = '__all__'

from django import forms
from .models import Leave, CustomUser

class LeaveForm(forms.ModelForm):
    employee = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(),
        label='Employee',
        required=True
    )

    class Meta:
        model = Leave
        fields = ['employee', 'advance_privilege_leave', 'sick_leave', 'casual_leave']

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id')
        try:
            employee = CustomUser.objects.get(employee_id=employee_id)  # Match employee by employee_id
        except CustomUser.DoesNotExist:
            raise forms.ValidationError("No employee found with the provided ID.")
        return employee

# class PersonalInfoForm(forms.ModelForm):
#     class Meta:
#         model = Employee
#         fields = [
#             'name', 
#             'date_of_birth', 
#             'gender', 
#             'nationality', 
#             'phone_number', 
#             'address',
#         ]


from django import forms
from django.core.validators import RegexValidator
from .models import Employee  # adjust import path as needed

class PersonalInfoForm(forms.ModelForm):
    date_of_birth = forms.DateField(
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            }
        ),
        required=True
    )

    gender = forms.ChoiceField(
        choices=[
            ('Male', 'Male'),
            ('Female', 'Female'),
            ('Other', 'Other')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    phone_number = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^\+?\d{10,15}$',
                message="Enter a valid phone number (10-15 digits, optional leading +)"
            )
        ],
        widget=forms.TextInput(
            attrs={
                'type': 'tel',           # mobile devices show number pad
                'pattern': '[0-9+]*',    # HTML pattern restriction
                'inputmode': 'numeric',  # forces numeric keypad on most devices
                'class': 'form-control', # Bootstrap styling
                'maxlength': '15'        # limit input length
            }
        )
    )

    class Meta:
        model = Employee
        fields = ['first_name','last_name','date_of_birth', 'gender', 'nationality', 'phone_number', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

 


class ProfessionalInfoForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'designation', 
            'department', 
            'reporting_manager', 
            'employee_type', 
            'work_location', 
        ]


class BankingInfoForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'bank_account_number', 
            'bank_name', 
            'ifsc_code', 
            'aadhar_number', 
            'pan_number', 
            'uan_number',
        ]


class EmployeeMediaForm(forms.ModelForm):
    class Meta:
        model = EmployeeMedia
        fields = ['profile_picture', 'cover_picture']

from django import forms
from .models import HRContact
from app.models import Employee

class HRContactForm(forms.ModelForm):
    class Meta:
        model = HRContact
        fields = ['employee', 'role']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            exclude_ids = HRContact.objects.filter(
                employee__company=company
            ).exclude(pk=self.instance.pk).values_list('employee_id', flat=True)

            employee_queryset = Employee.objects.filter(company=company).exclude(id__in=exclude_ids)

            # Custom label formatting: EMP ID - Name
            self.fields['employee'] = forms.ModelChoiceField(
                queryset=employee_queryset,
                widget=forms.Select(attrs={'class': 'form-control'}),
                label='Employee',
                required=True
            )
            self.fields['employee'].label_from_instance = lambda obj: f"{obj.employee_id} - {obj.first_name} {obj.last_name}"

from django import forms
from django.contrib.auth import get_user_model
from .models import HelpDeskTicket, HRContact, Employee

User = get_user_model()

class HelpDeskTicketForm(forms.ModelForm):
    team_leader = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Team Leader',
        required=True
    )
    hr = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='HR',
        required=True
    )
    manager = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label='Manager',
        required=True
    )
    issue_type = forms.ChoiceField(choices=[], label='Issue Type', required=True)

    class Meta:
        model = HelpDeskTicket
        fields = ['issue_type', 'description', 'team_leader', 'hr', 'manager']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe your issue'}),
        }

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)  # 'HR', 'IT', 'AS'
        company = kwargs.pop('company', None)    # <-- new
        super().__init__(*args, **kwargs)

        # Set issue type choices based on category
        if category == 'HR':
            choices = HelpDeskTicket.HR_ISSUE_CHOICES
        elif category == 'IT':
            choices = HelpDeskTicket.IT_ISSUE_CHOICES
        elif category == 'AS':
            choices = HelpDeskTicket.AS_ISSUE_CHOICES
        else:
            choices = []

        # Add empty placeholder choice at the beginning
        self.fields['issue_type'].choices = [('', '--- Select Issue Type ---')] + choices

        # Set TL and HR queryset using the new ForeignKey-based HRContact model
        if company:
            tl_contacts = HRContact.objects.filter(role='TL', employee__company=company)
            hr_contacts = HRContact.objects.filter(role='HR', employee__company=company)
            manager_contacts = HRContact.objects.filter(role='MG', employee__company=company)

            self.fields['team_leader'].queryset = User.objects.filter(id__in=tl_contacts.values_list('employee__user_id', flat=True))
            self.fields['hr'].queryset = User.objects.filter(id__in=hr_contacts.values_list('employee__user_id', flat=True))
            self.fields['manager'].queryset = User.objects.filter(id__in=manager_contacts.values_list('employee__user_id', flat=True))


class TaskForm(forms.Form):
    task_name = forms.CharField(max_length=255)
    employee_emails = forms.CharField(max_length=1024)  # For comma-separated emails
    due_date = forms.DateField(widget=forms.SelectDateWidget())  # Date widget for picking a due date

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'members']
        widgets = {
            'members': forms.CheckboxSelectMultiple
        }
    
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Only show users from the same company
            self.fields['members'].queryset = CustomUser.objects.filter(
                employee__company=user.employee.company
            )



class PersonalInfoForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'gender',
            'nationality',
            'phone_number',
            'address',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'pattern': '[0-9]*',    
                'inputmode': 'numeric'  
            }),
        }
 
#------------------------------------------------------------- Training #

class TrainingTopicForm(forms.ModelForm):
    class Meta:
        model = TrainingTopic
        fields = ['title', 'topic_link']



#------------------------------------------------------------- Career development 
 
class CareerResourceForm(forms.ModelForm):
    class Meta:
        model = CareerResource
        fields = ['title', 'description', 'detail_content', 'category', 'uploaded_file', 'video_link']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter resource title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Short description of the resource'
            }),
            'detail_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed explanation, guidelines, or content'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'video_link': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/video'
            }),
        }
 
    uploaded_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        }),
        help_text="Upload PDF or document (optional)"
    )
 
class SkillCategoryForm(forms.ModelForm):
    class Meta:
        model = SkillCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Technical Skills'}),
        }

class FAQForm(forms.ModelForm):
    class Meta:
        model = FAQ
        fields = ['question', 'answer']

class ContactHRForm(forms.Form):
    hr = forms.ModelChoiceField(queryset=CustomUser.objects.none(), label="Select HR")
    subject = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')  # Get logged-in user from view
        super().__init__(*args, **kwargs)
        self.fields['hr'].queryset = CustomUser.objects.filter(
            role='HR',
            company=user.company
        )
        self.fields['hr'].widget.attrs.update({'class': 'form-select'})
# forms.py
from django import forms
from .models import Company_check

class CompanyLogoForm(forms.ModelForm):
    class Meta:
        model = Company_check
        fields = ['logo']
