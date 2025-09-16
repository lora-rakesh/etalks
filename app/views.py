import calendar
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate,login,logout
from app.models import *
from app.forms import *
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.core.mail import send_mail
import random
from django.dispatch import receiver
from django.views.decorators.http import require_GET
import logging
from django.contrib.auth.signals import user_logged_out
from django.conf import settings
from app.decorators import *
from datetime import datetime, timedelta, date
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.templatetags.static import static
from django.urls import reverse
from weasyprint import HTML
from django.utils.timezone import now
from rest_framework.decorators import api_view
from rest_framework.response import Response
#from .serializers import PerformanceSerializer
from django.http import Http404
from django.db.models import F
import re
from django.db import transaction
from django.contrib.auth.hashers import make_password
import zoneinfo
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import localdate  

from .models import Notification, Employee, Salary, Company_check, CustomUser, TimeEntry, Muster, Holiday, LeaveRequest, Leave, Task, Team, ExpenseClaim, LoanRequest, ResignationRequest, FAQ, LoggedInUser, UnlockRequest, EmployeeMedia
from .models import TrainingTopic, LoginLog, HRContact, CareerResource, SkillCategory
from .forms import FAQForm, ContactHRForm, EmployeeProfileForm, EmployeeMediaForm, PersonalInfoForm, ProfessionalInfoForm, CareerResourceForm, SkillCategoryForm, TrainingTopicForm, CompanyLogoForm, TeamForm
from app.models import HelpDeskTicket, Employee, HRContact
from app.forms import HelpDeskTicketForm 
 
CustomUser = get_user_model()
 
#------------------------------------------------------------- Index #
 
User = get_user_model()
#   HELPERS
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def get_device_info(request):
    return request.META.get('HTTP_USER_AGENT', 'Unknown device')


def hash_ip(ip):
    return hashlib.sha256(ip.encode()).hexdigest()


def is_hr_or_manager(user):
    return hasattr(user, "role") and user.role in ["HR", "Manager"]

def indexview(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error_message = None

    if request.method == "POST":
        company_name = request.POST.get('company_name', '').strip()

        if company_name:
            try:
                # Case-sensitive match
                company = Company_check.objects.get(company_name__exact=company_name)
                return redirect(f'/login/?company_id={company.id}')
            except Company_check.DoesNotExist:
                error_message = (
                    "Company name not found. Please check capitalization. "
                    "Example: 'Tech' is different from 'tech'."
                )
        else:
            error_message = "Please enter a company name."

    return render(request, 'index.html', {
        'message': error_message
    })

#   COMPANY AUTOCOMPLETE
def company_autocomplete(request):
    term = request.GET.get('term', '')
    companies = Company_check.objects.filter(
        company_name__icontains=term
    ).values_list('company_name', flat=True)
    return JsonResponse(list(companies), safe=False)

#   LOGIN VIEW
def loginview(request):
    if request.user.is_authenticated:
        return redirect("dashboard")   # direct to common dashboard

    company_id = request.GET.get('company_id') or request.POST.get('company_id')

    if request.method == 'POST':
        employee_id = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user_obj = User.objects.get(employee_id=employee_id)
        except User.DoesNotExist:
            return render(request, 'login.html', {
                'message': 'User not found',
                'company_id': company_id
            })

        # Company restriction
        if str(user_obj.company_id) != str(company_id):
            return render(request, 'login.html', {
                'message': 'You are not authorized for this company',
                'company_id': company_id
            })

        # ✅ Account lock check
        if hasattr(user_obj, "check_lock_status") and user_obj.check_lock_status():
            return render(request, "send_unlock_request.html", {"user": user_obj, "company_id": company_id})

        # Authenticate
        user = authenticate(request, employee_id=employee_id, password=password)
        if user is not None:
            # Single device restriction
            existing_login = LoggedInUser.objects.filter(user=user).first()
            if existing_login and Session.objects.filter(session_key=existing_login.session_key).exists():
                return render(request, 'login.html', {
                    'message': 'You are already logged in on another device or browser.',
                    'company_id': company_id
                })
            elif existing_login:
                existing_login.delete()

            # Reset failed attempts
            if hasattr(user_obj, "failed_attempts"):
                user_obj.failed_attempts = 0
                user_obj.save()

            login(request, user)

            if not request.session.session_key:
                request.session.save()

            LoggedInUser.objects.update_or_create(
                user=user,
                defaults={'session_key': request.session.session_key}
            )

            # Log IP/device (only once per day)
            ip = get_client_ip(request)
            ip_hash_val = hash_ip(ip)
            today = timezone.now().date()

            already_logged_today = LoginLog.objects.filter(
                user=user,
                ip_hash=ip_hash_val,
                login_time__date=today
            ).exists()

            if not already_logged_today:
                LoginLog.objects.create(
                    user=user,
                    ip_address=ip,
                    device_info=get_device_info(request)
                )

            # ✅ same dashboard for all roles
            return redirect("dashboard")

        # Wrong password handling
        if hasattr(user_obj, "failed_attempts"):
            user_obj.failed_attempts += 1
            if user_obj.failed_attempts >= 5 and hasattr(user_obj, "lock_account"):
                user_obj.lock_account()
                return render(request, "send_unlock_request.html", {"user": user_obj, "company_id": company_id})
            user_obj.save()

        return render(request, 'login.html', {
            'message': 'Incorrect password',
            'company_id': company_id
        })

    return render(request, "login.html", {'company_id': company_id})


#   LOGOUT
def logoutview(request):
    logout(request)
    return redirect('login')

#   HR/Manager: Unlock Requests
@login_required
@user_passes_test(is_hr_or_manager)
def unlock_requests_view(request):
    requests = UnlockRequest.objects.all().order_by("-requested_at")
    return render(request, "unlock_requests.html", {"requests": requests})


@login_required
@user_passes_test(is_hr_or_manager)
def unlock_user(request, request_id):
    unlock_request = get_object_or_404(UnlockRequest, id=request_id)

    user_obj = unlock_request.user
    user_obj.is_locked = False
    user_obj.failed_attempts = 0
    user_obj.save()

    unlock_request.is_resolved = True
    unlock_request.resolved_by = request.user
    unlock_request.save()

    # ✅ Send email to user
    subject = "Your AIHR4U Account Has Been Unlocked"
    message = f"Hello {user_obj.first_name},\n\nYour account has been unlocked by HR/Manager. You can now log in to your account.\n\nRegards,\nAIHR4U Team"
    recipient_list = [user_obj.email]  # make sure your User model has email field
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)

    messages.success(request, f"{user_obj.first_name} has been unlocked and notified via email.")
    return redirect("unlock_requests")

#   Employee: Send Unlock Request
def send_unlock_request(request, user_id):
    reason = request.POST.get("reason", "").strip()
    user = get_object_or_404(User, id=user_id)
    if not UnlockRequest.objects.filter(user=user, is_resolved=False).exists():
        UnlockRequest.objects.create(user=user, requested_at=timezone.now(), reason=reason)
    messages.info(request, "Unlock request sent successfully.")
    return redirect('request_sent')

def request_sent(request):
    user = request.user
    return render(request, "request_sent.html", {"user": user})

#   CLEAR SESSIONS on logout
@receiver(user_logged_out)
def clear_logged_in_user(sender, request, user, **kwargs):
    LoggedInUser.objects.filter(user=user).delete()
 
#------------------------------------------------------------- Search bar #
@login_required(login_url='/')
def search_results(request):
    query = request.GET.get('query', '').lower()
    normalized_query = query.replace('-', ' ').strip()
 
    page_urls = {
        'home': 'dashboard',
        'index': 'dashboard',
        'dashboard': 'dashboard',
        'login': 'login',
        '404': 'page_not_found',
 
        # Profile
        'profile': 'profile',
        'edit': 'profile',
        'details': 'profile',
        'personal': 'profile',
        'professional': 'profile',
        'banking': 'profile',
        'picture': 'profile',
        'cover': 'profile',
 
        # Employee
        'employee': 'employee_list',
        'employee list': 'employee_list',
        'employee detail': 'employee_detail',
        'employee create': 'employee_create',
        'employee edit': 'employee_edit',
 
        # Leave & Holidays
        'leave balance': 'leave_balance',
        'leave request': 'leave_balance',
        'leave list': 'leave_list',
        'leave create': 'leave_create',
        'leave edit': 'leave_list',
        'leave delete': 'leave_list',
        'holidays': 'holidays',
        'holiday list': 'holidays_list',
        'holiday create': 'holiday_create',
        'holiday edit': 'holidays_list',
        'holiday delete': 'holidays_list',
 
        # Muster
        'muster': 'muster',
        'status': 'muster_status',
        'review': 'review_muster',
        'working': 'working_days',
 
        # Salary
        'salary': 'salary_details',
        'salary list': 'salary_list',
        'salary create': 'create_salary',
        'salary edit': 'salary_list',
        'salary delete': 'salary_list',
        'view salary': 'salary_list',
        'payslip': 'salary_details',
 
        # Expense & Loan
        'expense': 'expense_claims',
        'expense claim': 'expense_claims',
        'loan': 'loan_requests',
        'loan request': 'loan_requests',
 
        # Tasks & Training
        'task': 'task_management',
        'management': 'task_management',
        'training': 'training',
 
        # Policies
        'policy': 'policy',
        'cookie': 'cookie_policy',
        'terms': 'terms_of_service',
        'refund': 'refund_cancellation_policy',
        'acceptable': 'acceptable_use_policy',
        'retention': 'data_retention_policy',
 
        # Forms & Company
        'company': 'company_list',
        'company form': 'company_list',
 
        # Users
        'user': 'user_list',
        'user list': 'user_list',
        'user create': 'user_create',
        'user edit': 'user_list',
        'user delete': 'user_list',
 
        # Others
        'faq': 'faq',
        'contact': 'contact_us',
        'notifications': 'staff_notifications',
 
        # HR4U
        'hr4u': 'hr_dashboard',
        'employee self service': 'employee_self_service',
        'benefits': 'benefits_compensation',
        'career': 'career_development',
        'help desk': 'help_desk',
 
        # Data
        'data': 'employee_requests',
    }
 
    # Admin/Manager/HR access
    if normalized_query in page_urls:
        url_name = page_urls[normalized_query]
        return redirect(reverse(url_name))
    for page_name, url_name in page_urls.items():
        if page_name in normalized_query or normalized_query in page_name:
            return redirect(reverse(url_name))
 
    # No match found
    messages.warning(request, "No results found for your search.")
    return redirect('dashboard')
 
 
#------------------------------------------------------------- FAQ #
# Utility function to check if user is HR or Manager
def is_hr_or_manager(user):
    return getattr(user, "role", "").lower() in ["hr", "manager"]

@login_required
def faq(request):
    faqs = FAQ.objects.all().order_by('-created_at')
    can_edit = is_hr_or_manager(request.user)  # Only HR & Manager can modify FAQs

    # Handle Add FAQ
    if request.method == "POST" and 'add_faq' in request.POST:
        if can_edit:
            form = FAQForm(request.POST)
            if form.is_valid():
                faq_instance = form.save(commit=False)
                faq_instance.created_by = request.user  # ✅ Assign creator
                faq_instance.save()
                return redirect("faq")
        else:
            return JsonResponse({"error": "Permission denied"}, status=403)

    # Handle Edit FAQ
    if request.method == "POST" and 'edit_faq' in request.POST:
        if can_edit:
            faq_id = request.POST.get("faq_id")
            faq_instance = get_object_or_404(FAQ, id=faq_id)
            form = FAQForm(request.POST, instance=faq_instance)
            if form.is_valid():
                form.save()  # ✅ Keep created_by unchanged
                return redirect("faq")
        else:
            return JsonResponse({"error": "Permission denied"}, status=403)

    # Handle Delete FAQ
    if request.method == "POST" and 'delete_faq' in request.POST:
        if can_edit:
            faq_id = request.POST.get("faq_id")
            faq_instance = get_object_or_404(FAQ, id=faq_id)
            faq_instance.delete()
            return redirect("faq")
        else:
            return JsonResponse({"error": "Permission denied"}, status=403)

    return render(request, "faq.html", {
        "faqs": faqs,
        "can_edit": can_edit,
        "form": FAQForm()
    })


#------------------------------------------------------------- Chat Bot #
 
@login_required(login_url='/')
def chat_bot(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    return render(request,'chat_bot.html' , {'employee': employee})
 
#------------------------------------------------------------- CTraining #
 
@login_required(login_url='/')
def training(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request,'training.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
#------------------------------------------------------------- Contact us #
def contact_us(request):
    if request.method == "POST":
        form = ContactHRForm(request.POST, user=request.user)
        if form.is_valid():
            hr_user = form.cleaned_data['hr']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']

            send_mail(
                subject,
                f"Message from {request.user.first_name} (ID: {request.user.employee_id}, Email: {request.user.email}):\n\n{message}",
                request.user.email,
                [hr_user.email],
                fail_silently=False,
            )

            messages.success(request, f"Message sent to {hr_user.first_name} ({hr_user.email})")
            return redirect('contact_us')
    else:
        form = ContactHRForm(user=request.user)

    return render(request, "contact_us.html", {"form": form})

#------------------------------------------------------------- Company records #
@login_required(login_url='/')
def company_check(request):
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
       
        if not company_name:
            return render(request, 'company_check.html', {'message': 'Company name is required.'})
       
        company, created = Company_check.objects.get_or_create(company_name=company_name)
       
        return redirect('company_detail', company_id=company.id)
 
    return render(request, 'company_check.html')
 
@login_required(login_url='/')
def company_detail(request, company_id):
    company = Company_check.objects.get(id=company_id)
    return render(request, 'company_detail.html', {'company': company})
 
 
 
#------------------------------------------------------------- Company records #
 
from .models import (
    Notification, Employee, Muster,
    LeaveRequest, ExpenseClaim, LoanRequest, ResignationRequest
)

@login_required(login_url='/')
def base(request):
    user = request.user  # Always first
    
    # Basic info common to all roles
    company = user.company
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(
        recipient=user,
        is_read=False,
        company=company
    ).order_by('-created_at')


    context = {
        'employee': employee,
        'notifications': notifications,
    }

    if user.role == 'Employee':
        # For normal employees, render user dashboard
        return render(request, 'dashboard.html', context)

    elif user.role in ['HR', 'Manager'] or user.is_superuser:
        # For HR, Manager and superuser, add pending approvals
        context.update({
            'pending_musters': Muster.objects.filter(status='Pending', company=company),
            'pending_leave_request': LeaveRequest.objects.filter(status='pending', company=company),
            'pending_expense': ExpenseClaim.objects.filter(status='pending', company=company),
            'pending_loan': LoanRequest.objects.filter(status='pending', company=company),
            'pending_resignations': ResignationRequest.objects.filter(status__iexact='pending', employee__company=company)


        })
        return render(request, 'base.html', context)

    # Default fallback
    return render(request, 'base.html', context)

 
 
#------------------------------------------------------------- Dashboard #

@login_required(login_url='/')
def dashboard(request):
    user = request.user
    company = getattr(user, 'company', None)
    today = datetime.now().date()

    context = {
        'today': today,
        'current_time': timezone.now().strftime("%I:%M %p"),
    }

    try:
        employee = Employee.objects.get(employee_id=user.employee_id, company=company)
        context['employee'] = employee
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('logout')

    # Show tips logic
    if request.session.get('show_tips'):
        context['show_tips'] = True
        del request.session['show_tips']
    elif user.is_first_login:
        request.session['show_tips'] = True
        context['show_tips'] = True
        user.is_first_login = False
        user.save()

    # Notifications
    context['notifications'] = Notification.objects.filter(
        recipient=user, 
        is_read=False
    ).order_by('-created_at')

    # Birthdays
    context['employees_with_birthday'] = Employee.objects.filter(
        company=company,
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    )

    # Stats for HR/Manager/Admin
    if user.role in ['HR', 'Manager'] or user.is_superuser:
        context.update({
            'total_employees': Employee.objects.filter(company=company).count(),
            'todays_clockins': TimeEntry.objects.filter(
                user__employee__company=company,
                clock_in_time__date=localdate()
            ).count(),
            'approved_leaves_today': LeaveRequest.objects.filter(
                employee__company=company,
                status='Approved',
                start_date__lte=localdate(),
                end_date__gte=localdate()
            ).count(),
        })

    # ✅ Add tasks for logged-in user (fix: use assigned_to instead of assignee)
    context['tasks'] = Task.objects.filter(
        assigned_to=user,
        completed=False
    ).order_by('due_date')

    return render(request, 'dashboard.html', context)




# ---------------------- Clear Tips ----------------------
from django.views.decorators.http import require_POST
@require_POST
@login_required
def clear_tips(request):
    request.session.pop('show_tips', None)
    return JsonResponse({'status': 'cleared'})
 
#------------------------------------------------------------- Employee requests - Notifications  #
from app.models import (
    Muster, LeaveRequest, ExpenseClaim, LoanRequest, TimeEntry,
    CustomUser, Employee, Notification, ResignationRequest
)


@login_required(login_url='/')
@staff_member_required
def employee_requests(request):
    user = request.user
    company = user.company
    employee = Employee.objects.get(employee_id=user.employee_id)
    today = localdate()
    
    # Base querysets - all company data for today by default
    users_qs = CustomUser.objects.filter(company=company)
    
    muster_requests = Muster.objects.filter(user__company=company, date__date=today)
    leave_requests = LeaveRequest.objects.filter(employee__company=company, created_at__date=today)
    expense_claims = ExpenseClaim.objects.filter(employee__company=company, date=today)
    loan_requests = LoanRequest.objects.filter(employee__company=company, date_requested__date=today)
    time_entries = TimeEntry.objects.filter(user__company=company, clock_in_time__date=today)
    resignation_requests = ResignationRequest.objects.filter(
    employee__company=company,
    submitted_at__date=today
)
  # No date filter by default
    
    employees = users_qs

    if request.method == 'POST':
        employee_id_input = request.POST.get('employee_id')
        request_type = request.POST.get('request_type')
        month_filter = request.POST.get('month')
        specific_date = request.POST.get('specific_date')

        # Filter by employee ID if given
        if employee_id_input:
            try:
                filtered_user = users_qs.get(employee_id=employee_id_input)
                users_qs = users_qs.filter(id=filtered_user.id)

                muster_requests = muster_requests.filter(user=filtered_user)
                leave_requests = leave_requests.filter(employee=filtered_user)
                expense_claims = expense_claims.filter(employee=filtered_user)
                loan_requests = loan_requests.filter(employee=filtered_user)
                time_entries = time_entries.filter(user=filtered_user)
                resignation_requests = resignation_requests.filter(employee=filtered_user)
            except CustomUser.DoesNotExist:
                messages.error(request, "Employee not found")
                # Clear all results if invalid filter
                muster_requests = Muster.objects.none()
                leave_requests = LeaveRequest.objects.none()
                expense_claims = ExpenseClaim.objects.none()
                loan_requests = LoanRequest.objects.none()
                time_entries = TimeEntry.objects.none()
                resignation_requests = ResignationRequest.objects.none()

        # Filter by month if given
        if month_filter:
            try:
                year, month = map(int, month_filter.split('-'))
                base_users = users_qs

                muster_requests = Muster.objects.filter(
                    user__in=base_users, date__year=year, date__month=month)
                leave_requests = LeaveRequest.objects.filter(
                    employee__in=base_users, start_date__year=year, start_date__month=month)
                expense_claims = ExpenseClaim.objects.filter(
                    employee__in=base_users, date__year=year, date__month=month)
                loan_requests = LoanRequest.objects.filter(
                    employee__in=base_users, date_requested__year=year, date_requested__month=month)
                time_entries = TimeEntry.objects.filter(
                    user__in=base_users, clock_in_time__year=year, clock_in_time__month=month)
                resignation_requests = ResignationRequest.objects.filter(
                    employee__in=base_users, submitted_at__year=year, submitted_at__month=month)
            except ValueError:
                pass

        # Filter by specific date if given
        elif specific_date:
            try:
                date_obj = datetime.strptime(specific_date, '%Y-%m-%d').date()
                base_users = users_qs

                muster_requests = Muster.objects.filter(
                    user__in=base_users, date__date=date_obj)
                leave_requests = LeaveRequest.objects.filter(
                    employee__in=base_users, start_date=date_obj)
                expense_claims = ExpenseClaim.objects.filter(
                    employee__in=base_users, date=date_obj)
                loan_requests = LoanRequest.objects.filter(
                    employee__in=base_users, date_requested__date=date_obj)
                time_entries = TimeEntry.objects.filter(
                    user__in=base_users, clock_in_time__date=date_obj)
                resignation_requests = ResignationRequest.objects.filter(
                    employee__in=base_users, submitted_at__date=date_obj)
            except ValueError:
                pass

        # Apply request_type filter - empty other querysets except chosen one
        if request_type:
            if request_type == 'muster':
                leave_requests = []
                expense_claims = []
                loan_requests = []
                time_entries = []
                resignation_requests = []
            elif request_type == 'leave':
                muster_requests = []
                expense_claims = []
                loan_requests = []
                time_entries = []
                resignation_requests = []
            elif request_type == 'expense':
                muster_requests = []
                leave_requests = []
                loan_requests = []
                time_entries = []
                resignation_requests = []
            elif request_type == 'loan':
                muster_requests = []
                leave_requests = []
                expense_claims = []
                time_entries = []
                resignation_requests = []
            elif request_type == 'time_entry':
                muster_requests = []
                leave_requests = []
                expense_claims = []
                loan_requests = []
                resignation_requests = []
            elif request_type == 'resignation':
                muster_requests = []
                leave_requests = []
                expense_claims = []
                loan_requests = []
                time_entries = []

    # Notifications
    notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')

    return render(request, 'employee_data.html', {
        'employee': employee,
        'employees': employees,
        'muster_requests': muster_requests,
        'leave_requests': leave_requests,
        'expense_claims': expense_claims,
        'loan_requests': loan_requests,
        'time_entries': time_entries,
        'resignations': resignation_requests,
        'notifications': notifications,
    })

 
#------------------------------------------------------------- Mark as read -- Notifications  #
from app.models import (
    Employee, CustomUser, Muster, LeaveRequest,
    ExpenseClaim, LoanRequest, ResignationRequest,
    Notification
)

@login_required(login_url='/')
@staff_member_required
def staff_notifications(request):
    user = request.user
    company = user.company
    employee = Employee.objects.get(employee_id=user.employee_id)
    today = localdate()
    
    # Base querysets
    users_qs = CustomUser.objects.filter(company=company)
    musters = Muster.objects.filter(user__company=company, date__date=today)
    leaves = LeaveRequest.objects.filter(employee__company=company, created_at__date=today)
    expenses = ExpenseClaim.objects.filter(employee__company=company, date=today)
    pendings_loan = LoanRequest.objects.filter(employee__company=company, date_requested__date=today)

    # Resignations: Fetch **all relevant statuses** for HR and Manager role
    if user.role in ['HR', 'Manager']:
        resignations = ResignationRequest.objects.filter(
            employee__company=company,
            submitted_at__date=today,  # include all statuses here
        )
    else:
        resignations = ResignationRequest.objects.none()  # No resignations for other users

    if request.method == 'POST':
        employee_id_input = request.POST.get('employee_id')
        request_type = request.POST.get('request_type')
        month_filter = request.POST.get('month')
        specific_date = request.POST.get('specific_date')

        # Apply employee filter if provided
        if employee_id_input:
            try:
                filtered_user = CustomUser.objects.get(employee_id=employee_id_input, company=company)
                users_qs = users_qs.filter(id=filtered_user.id)
                musters = musters.filter(user=filtered_user)
                leaves = leaves.filter(employee=filtered_user)
                expenses = expenses.filter(employee=filtered_user)
                pendings_loan = pendings_loan.filter(employee=filtered_user)
                resignations = resignations.filter(employee=filtered_user)
            except CustomUser.DoesNotExist:
                messages.error(request, "Employee not found")
                musters = musters.none()
                leaves = leaves.none()
                expenses = expenses.none()
                pendings_loan = pendings_loan.none()
                resignations = resignations.none()

        # Apply month filter
        if month_filter:
            year, month = map(int, month_filter.split('-'))
            musters = Muster.objects.filter(user__in=users_qs, date__year=year, date__month=month)
            leaves = LeaveRequest.objects.filter(employee__in=users_qs, start_date__year=year, start_date__month=month)
            expenses = ExpenseClaim.objects.filter(employee__in=users_qs, date__year=year, date__month=month)
            pendings_loan = LoanRequest.objects.filter(employee__in=users_qs, date_requested__year=year, date_requested__month=month)
            resignations = ResignationRequest.objects.filter(
                employee__in=users_qs,
                submitted_at__year=year,
                submitted_at__month=month,  # include all statuses here too
            )

        # Apply specific date filter
        elif specific_date:
            try:
                date_obj = datetime.strptime(specific_date, '%Y-%m-%d').date()
                musters = Muster.objects.filter(user__in=users_qs, date__date=date_obj)
                leaves = LeaveRequest.objects.filter(employee__in=users_qs, start_date=date_obj)
                expenses = ExpenseClaim.objects.filter(employee__in=users_qs, date=date_obj)
                pendings_loan = LoanRequest.objects.filter(employee__in=users_qs, date_requested__date=date_obj)
                resignations = ResignationRequest.objects.filter(
                    employee__in=users_qs,
                    submitted_at__date=date_obj,
                    # and here
                )
            except ValueError:
                pass

        # Apply request type filter: Clear other categories except the one selected
        if request_type:
            if request_type == 'muster':
                leaves = []
                expenses = []
                pendings_loan = []
                resignations = []
            elif request_type == 'leave':
                musters = []
                expenses = []
                pendings_loan = []
                resignations = []
            elif request_type == 'expense':
                musters = []
                leaves = []
                pendings_loan = []
                resignations = []
            elif request_type == 'loan':
                musters = []
                leaves = []
                expenses = []
                resignations = []
            elif request_type == 'resignation':
                musters = []
                leaves = []
                expenses = []
                pendings_loan = []

    # Notifications for header
    notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')

    return render(request, 'staff_notifications.html', {
        'employee': employee,
        'musters': musters,
        'leaves': leaves,
        'expenses': expenses,
        'pendings_loan': pendings_loan,
        'resignations': resignations,
        'notifications': notifications,
        'user': user,  # Pass user so template can check role
    })

 
#------------------------------------------------------------- clock In #

@login_required(login_url='/')
def clock_in(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        if latitude and longitude:
            if TimeEntry.objects.filter(user=request.user, clock_out_time__isnull=True).exists():
                messages.warning(request, "You have already clocked in.")
            else:
                clock_in_time = timezone.now()

                # ✅ Get company from Employee profile
                try:
                    employee = Employee.objects.get(user=request.user)
                    company = employee.company
                except Employee.DoesNotExist:
                    company = None  # Or handle error appropriately

                # ✅ Save company into TimeEntry
                time_entry = TimeEntry.objects.create(
                    user=request.user,
                    clock_in_time=clock_in_time,
                    clock_in_latitude=latitude,
                    clock_in_longitude=longitude,
                    company=company
                )

                messages.success(request, "Clocked in successfully.")
        else:
            messages.error(request, "Unable to capture your location. Please try again.")

    return redirect('dashboard')

   
 
#------------------------------------------------------------- clock Out #
 
@login_required(login_url='/')
def clock_out(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
 
        try:
            if latitude == '':
                latitude = None
            else:
                latitude = float(latitude)
        except ValueError:
            latitude = None
       
        try:
            if longitude == '':
                longitude = None
            else:
                longitude = float(longitude)
        except ValueError:
            longitude = None
 
        time_entry = TimeEntry.objects.filter(user=request.user, clock_out_time__isnull=True).first()
 
        if not time_entry:
            messages.warning(request, "You haven't clocked in yet.")
        else:
            clock_in_time = timezone.localtime(time_entry.clock_in_time)
            current_time = timezone.localtime(timezone.now())
            time_difference = current_time - clock_in_time
 
            if time_difference >= timedelta(hours=9):
                time_entry.clock_out_time = current_time
                time_entry.clock_out_latitude = latitude
                time_entry.clock_out_longitude = longitude
                time_entry.save()
                messages.success(request, "Clocked out successfully.")
            else:
                messages.warning(request, "You can only clock out after 9 hours.")
 
    return redirect('dashboard')
 
 
#------------------------------------------------------------- Muster #
 
@login_required(login_url='/')
def muster(request):
    user = request.user
    today_date = timezone.localtime(timezone.now()).date()
    today_date_str = today_date.strftime('%Y-%m-%d')
    clock_in_time = None
    time_entry = TimeEntry.objects.filter(user=user, clock_in_time__date=today_date).first()
 
    if time_entry:
        clock_in_time = timezone.localtime(time_entry.clock_in_time)
    else:
        print(f"No TimeEntry found for user {user} on {today_date}")
 
    if request.method == "POST":
        user = request.user
        employee_id = request.POST['employee_id']
        date_str = request.POST['date']
        clock_in_time = request.POST['clock_in_time']
        clock_out_time = request.POST['clock_out_time']
        reason = request.POST['reason']
        notes = request.POST['notes']
 
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
 
        muster_entry = Muster.objects.create(user=request.user,employee_id=employee_id,date=date_obj,clock_in_time=clock_in_time,clock_out_time=clock_out_time,reason=reason,notes=notes,status="Pending")
 
        notification_message = f"Your Muster request of {reason}, {date_obj} - {clock_in_time} & {clock_out_time} has been submitted successfully."
        Notification.objects.create(recipient=muster_entry.user, message=notification_message)
 
        muster_entry.save()
 
        return redirect('muster')
   
    user = request.user
    muster_entry = Muster.objects.filter(employee_id=user.employee_id)
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request,'muster.html', {
        'employee': employee,
        'employee_id': user.employee_id,
        "muster_entry": muster_entry,
        'today_date': today_date_str,
        'clock_in_time': clock_in_time,
        'notifications': notifications,
        }
    )
 
 
@login_required(login_url='/')
def muster_status(request):
    user = request.user
 
    time_entries = TimeEntry.objects.filter(user=user)
 
    entries = []
    for entry in time_entries:
        if entry.clock_in_time and entry.clock_out_time:
            time_difference = entry.clock_out_time - entry.clock_in_time
 
            if time_difference > timedelta(hours=12):
                continue
 
            status = "Regular" if time_difference >= timedelta(hours=9) else "Pending"
        else:
            status = "Pending"
 
        entries.append({
            "employee_id": entry.user.employee_id,
            "date": entry.clock_in_time.date() if entry.clock_in_time else None,
            "clock_in_time": entry.clock_in_time if entry.clock_in_time else None,
            "clock_out_time": entry.clock_out_time if entry.clock_out_time else None,
            "status": status,
        })
 
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, "muster_status.html", {
        "entries": entries,
        "employee": employee,
        'notifications': notifications,
        }
    )
 
 
#------------------------------------------------------------- Leave Request #
@login_required(login_url='/')
def leave_balance(request):
    user = request.user
    leave_request = LeaveRequest.objects.filter(employee=user)

    try:
        leave = Leave.objects.get(employee=user)
    except Leave.DoesNotExist:
        leave = None  # No leave record found

    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')

    leave_messages = []
    no_leave_message = None

    if leave:
        # If all three are 0 -> show HR contact message
        if (
            leave.advance_privilege_leave == 0 and
            leave.sick_leave == 0 and
            leave.casual_leave == 0
        ):
            no_leave_message = "You currently have no leave record. Please contact your Manager or HR."
        else:
            # Otherwise show per-type messages
            if leave.advance_privilege_leave == 0:
                leave_messages.append("Your Advance Privilege Leaves are completed.")
            if leave.sick_leave == 0:
                leave_messages.append("Your Sick Leaves are completed.")
            if leave.casual_leave == 0:
                leave_messages.append("Your Casual Leaves are completed.")
    else:
        # No Leave object at all
        no_leave_message = "You currently have no leave record. Please contact your Manager or HR."

    return render(
        request,
        'leave_balance.html',
        {
            'leave': leave,
            'leave_request': leave_request,
            'employee': employee,
            'notifications': notifications,
            'leave_messages': leave_messages,
            'no_leave_message': no_leave_message
        }
    )

@login_required(login_url='/')
def leave_request(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')

    try:
        leave = Leave.objects.get(employee=user)
    except Leave.DoesNotExist:
        leave = None

    if request.method == 'POST':
        leave_type = request.POST['leave_type']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        reason = request.POST['reason']

        # Block if no balance at all
        if not leave or (
            leave.advance_privilege_leave == 0 and
            leave.sick_leave == 0 and
            leave.casual_leave == 0
        ):
            messages.error(request, "You currently have no leave record. Please contact your Manager or HR.")
            return redirect('leave_balance')

        # Block if chosen leave type has 0 balance
        if (leave_type == "advance_privilege" and leave.advance_privilege_leave == 0):
            messages.error(request, "You have no Advance Privilege Leave balance left. Cannot submit request.")
            return redirect('leave_balance')

        if (leave_type == "sick" and leave.sick_leave == 0):
            messages.error(request, "You have no Sick Leave balance left. Cannot submit request.")
            return redirect('leave_balance')

        if (leave_type == "casual" and leave.casual_leave == 0):
            messages.error(request, "You have no Casual Leave balance left. Cannot submit request.")
            return redirect('leave_balance')

        # Calculate weekdays requested
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        weekdays_requested = 0
        current_day = start_date
        while current_day <= end_date:
            if current_day.weekday() < 5:
                weekdays_requested += 1
            current_day += timedelta(days=1)

        # ✅ NEW: Prevent applying more leave days than balance
        if leave_type == "advance_privilege" and weekdays_requested > leave.advance_privilege_leave:
            messages.error(request, f"You only have {leave.advance_privilege_leave} Advance Privilege Leave days left, but you requested {weekdays_requested}.")
            return redirect('leave_balance')

        if leave_type == "sick" and weekdays_requested > leave.sick_leave:
            messages.error(request, f"You only have {leave.sick_leave} Sick Leave days left, but you requested {weekdays_requested}.")
            return redirect('leave_balance')

        if leave_type == "casual" and weekdays_requested > leave.casual_leave:
            messages.error(request, f"You only have {leave.casual_leave} Casual Leave days left, but you requested {weekdays_requested}.")
            return redirect('leave_balance')

        # Save leave request
        leave_request = LeaveRequest(
            employee=request.user,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            days_requested=weekdays_requested,
            status='pending'
        )
        leave_request.save()

        notification_message = f"Your Leave Request of {leave_type} from {start_date} to {end_date} has been submitted successfully."
        Notification.objects.create(recipient=leave_request.employee, message=notification_message)

        messages.success(request, notification_message)
        return redirect('leave_balance')

    return render(request, 'leave_request.html', {"employee": employee, 'notifications': notifications})

 
#------------------------------------------------------------- Holidays #
 
@login_required(login_url='/')
def holidays(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    holidays = Holiday.objects.filter(company=employee.company)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')

 
    return render(request, 'holidays.html', {
        'h': holidays,
        'employee': employee,
        'notifications': notifications,
    })
 
#------------------------------------------------------------- Salary details #
@login_required(login_url='/')
def salary_details(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    from_month = request.GET.get('from_month')
    to_month = request.GET.get('to_month')
 
    if not from_month and not to_month:
        latest_payslip = Salary.objects.filter(employee=employee).order_by('-month').first()
 
        if latest_payslip:
            from_month = latest_payslip.month.strftime('%Y-%m')
            to_month = latest_payslip.month.strftime('%Y-%m')
 
    if from_month:
        from_month = f"{from_month}-01"
 
    if to_month:
        to_month_date = datetime.strptime(f"{to_month}-01", '%Y-%m-%d')
        last_day_of_month = calendar.monthrange(to_month_date.year, to_month_date.month)[1]
        to_month = f"{to_month}-{last_day_of_month}"
 
    if from_month and to_month:
        payslips = Salary.objects.filter(
            employee=employee,
            month__gte=from_month,
            month__lte=to_month
        ).order_by('-month')
    else:
        payslips = Salary.objects.filter(employee=employee).order_by('-month')[:1]
 
    logo_url = request.build_absolute_uri(static('Lora.jpg'))
 
    return render(request, 'salary_details.html', {
        'employee': employee,
        'payslips': payslips,
        'logo_url': logo_url,
        'from_month': from_month[:7] if from_month else None,
        'to_month': to_month[:7] if to_month else None,
    })
   
@login_required(login_url='/')
def generate_payslip_pdf(request, employee_id):
    user = request.user
    employee = get_object_or_404(Employee, employee_id=user.employee_id)
    company = employee.company  # restrict to logged-in user's company

    from_month = request.GET.get('from_month')
    to_month = request.GET.get('to_month')

    if not from_month and not to_month:
        latest_payslip = Salary.objects.filter(
            employee=employee, employee__company=company
        ).order_by('-month').first()
        if latest_payslip:
            from_month = latest_payslip.month.strftime('%Y-%m')
            to_month = latest_payslip.month.strftime('%Y-%m')

    if from_month:
        from_month = f"{from_month}-01"

    if to_month:
        to_month_date = datetime.strptime(f"{to_month}-01", '%Y-%m-%d')
        last_day = calendar.monthrange(to_month_date.year, to_month_date.month)[1]
        to_month = f"{to_month}-{last_day}"

    if from_month and to_month:
        payslips = Salary.objects.filter(
            employee=employee,
            employee__company=company,
            month__gte=from_month,
            month__lte=to_month
        ).order_by('-month')
    else:
        payslips = Salary.objects.filter(
            employee=employee,
            employee__company=company
        ).order_by('-month')[:1]

    # ✅ FIXED: remove fallback logo, only use uploaded one
    logo_url = request.build_absolute_uri(company.logo.url) if company.logo else None

    html_string = render_to_string('all_payslips.html', {
        'employee': employee,
        'payslips': payslips,
        'logo_url': logo_url,   # watermark
        'company': company,
    })

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{employee.user.username}_payslips.pdf"'

    return response


 
#------------------------------------------------------------- Tax Deduction #
 
@login_required(login_url='/')
def tax_deduction(request):
    user = request.user
    td = LoanRequest.objects.filter(employee=user)
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'tax_deduction.html', {
        'user': user,
        'td': td,
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
#------------------------------------------------------------- Forgot Password #
 
User = get_user_model()
 
def generate_otp():
    """Generate a 6-digit OTP"""
    return random.randint(100000, 999999)
 
def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                messages.error(request, "Email address not found.")
                return redirect('forgot_password')
 
            otp = generate_otp()
 
            india_tz = zoneinfo.ZoneInfo('Asia/Kolkata')
            current_time = datetime.now(india_tz)
 
            request.session['otp'] = str(otp)
            request.session['otp_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S%z')
            request.session['user_email'] = email
 
            send_mail(
                'Password Reset OTP',
                f'Your OTP for password reset is {otp}. It is valid for 10 minutes.',
                'your-email@gmail.com',
                [email],
                fail_silently=False,
            )
 
            messages.success(request, "OTP sent to your email address.")
            return redirect('verify_otp')
    else:
        form = ForgotPasswordForm()
 
    return render(request, 'forgot_password.html', {'form': form})
 
def verify_otp(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        stored_otp_time_str = request.session.get('otp_time')
        user_email = request.session.get('user_email')
 
        if not all([stored_otp, stored_otp_time_str, user_email]):
            messages.error(request, "Session expired. Please request a new OTP.")
            return redirect('forgot_password')
 
        try:
            india_tz = zoneinfo.ZoneInfo('Asia/Kolkata')
            stored_time = datetime.strptime(stored_otp_time_str, '%Y-%m-%d %H:%M:%S%z')
            current_time = datetime.now(india_tz)
 
            time_diff = (current_time - stored_time).total_seconds() / 60
 
            if time_diff > 10:
                messages.error(request, "OTP has expired. Please request a new one.")
 
                for key in ['otp', 'otp_time', 'user_email']:
                    request.session.pop(key, None)
                return redirect('forgot_password')
 
            if otp_input == stored_otp:
                messages.success(request, "OTP verified successfully.")
                return redirect('reset_password_with_otp')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect('verify_otp')
 
        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            return redirect('forgot_password')
 
    return render(request, 'verify_otp.html')
 
def reset_password_with_otp(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user_email = request.session.get('user_email')
 
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match. Please try again.")
            return redirect('reset_password_with_otp')
 
        password_regex = r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
 
        if not re.match(password_regex, new_password):
            messages.error(request, (
                "Password must be at least 8 characters long, contain at least one uppercase letter, "
                "one special character, and one number."
            ))
            return redirect('reset_password_with_otp')
 
        try:
            user = get_user_model().objects.get(email=user_email)
            user.password = make_password(new_password)
            user.password_last_changed = now()
            user.save()
 
            for key in ['otp', 'otp_time', 'user_email']:
                request.session.pop(key, None)
 
            messages.success(request, "Password reset successful. You can now log in with your new password.")
            return redirect('index')
        except get_user_model().DoesNotExist:
            messages.error(request, "No user found with this email address.")
            return redirect('forgot_password')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('forgot_password')
 
    return render(request, 'reset_password_with_otp.html')
 
 
#------------------------------------------------------------- Reset Password #
 
from django.contrib.auth import update_session_auth_hash
 
def reset_password(request):
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
 
            try:
                user = CustomUser.objects.get(employee_id=employee_id)
                if user.check_password(old_password):
                    user.set_password(new_password)
                    user.password_last_changed = timezone.now()
 
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, "Your password has been updated successfully.")
                    return redirect('index')
                else:
                    messages.error(request, "Old password is incorrect.")
            except CustomUser.DoesNotExist:
                messages.error(request, "User with this employee ID does not exist.")
    else:
        form = ResetPasswordForm()
 
    return render(request, 'reset_password.html', {'form': form})
 
   
#------------------------------------------------------------- Profile #
 
@login_required
def profile(request):
    user = request.user
    employee = Employee.objects.filter(user=user).first()
    employee_media = EmployeeMedia.objects.filter(employee=employee).first()
   
    return render(request, 'profile.html', {
        'employee': employee,
        'employee_media': employee_media,
        'user': user,
    })
 
 
@login_required(login_url='/')
def edit_personal_info(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
 
    # Change this line from employee_user to employee
    if request.user.employee != employee:
        messages.error(request, "You don't have permission to edit this profile.")
        return redirect('profile')
   
    if request.method == 'POST':
        form = PersonalInfoForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Personal information updated successfully!')
            return render(request, 'edit_personal_info.html', {
                'form': PersonalInfoForm(instance=employee),
                'employee': employee
            })
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PersonalInfoForm(instance=employee)
   
    return render(request, 'edit_personal_info.html', {
        'form': form,
        'employee': employee
    })
 
 
@login_required(login_url='/')
def edit_professional_info(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=request.user.employee_id)
   
    if request.method == 'POST':
        form = ProfessionalInfoForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfessionalInfoForm(instance=employee)
   
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'edit_professional_info.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
 
 
@login_required(login_url='/')
def edit_banking_info(request, employee_id):
    employee = get_object_or_404(Employee, employee_id=request.user.employee_id)
   
    if request.method == 'POST':
        form = BankingInfoForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = BankingInfoForm(instance=employee)
   
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'edit_banking_info.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
 
 
 
#------------------------------------------------------------- Task Management #
@login_required(login_url='/')
def task_management(request):
    user = request.user
    try:
        employee = Employee.objects.get(employee_id=user.employee_id)
        company = employee.company
    except Employee.DoesNotExist:
        return HttpResponse("Employee record not found", status=404)

    # Get notifications
    notifications = Notification.objects.filter(
        recipient=request.user, 
        is_read=False
    ).order_by('-created_at')

    # Get teams for dropdown - both created by or containing current company members
    teams = Team.objects.filter(members=user, company=company).distinct()

    # Base task query
    assigned_tasks = Task.objects.filter(
        created_by=user
    ).order_by('-created_at')



    # Apply filters if present
    employee_id = request.GET.get('employee_id', '')
    if employee_id:
        try:
            employee_filter = CustomUser.objects.get(
                employee_id=employee_id,
                employee__company=company
            )
            assigned_tasks = assigned_tasks.filter(assigned_to=employee_filter)
        except CustomUser.DoesNotExist:
            assigned_tasks = Task.objects.none()

    month = request.GET.get('month', '')
    if month:
        try:
            month_start = datetime.strptime(month, '%Y-%m').date()
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            assigned_tasks = assigned_tasks.filter(due_date__range=[month_start, month_end])
        except ValueError:
            pass

    # Remove duplicates
    seen = set()
    unique_tasks = []
    for task in assigned_tasks:
        key = (task.name, task.due_date)
        if key not in seen:
            seen.add(key)
            unique_tasks.append(task)

    # Prepare months for filter
    months = [
        {'num': f"{i:02d}", 'name': datetime(2025, i, 1).strftime('%B')}
        for i in range(1, 13)
    ]

    return render(request, 'task_management.html', {
        'employee_id': user.employee_id,
        'employee': employee,
        'notifications': notifications,
        'assigned_tasks': unique_tasks,
        'teams': teams,  # Now included!
        'months': months,
        'current_month': datetime.now().strftime('%Y-%m'),
        'debug_info': {  # For template debugging
            'company_id': company.id,
            'teams_count': teams.count(),
            'user_email': user.email
        }
    })

def staff_required(view_func):
    """
    Decorator that checks if user is staff member
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_staff,
        login_url='/',
        redirect_field_name=None
    )
    return actual_decorator(view_func)

@login_required(login_url='/')
@staff_member_required
@require_http_methods(["GET", "POST"])
def assign_task(request):
    user = request.user
    try:
        employee = Employee.objects.get(employee_id=user.employee_id)
        company = employee.company
        teams = Team.objects.filter(members=request.user, company=company).distinct()
    except Employee.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Employee record not found'}, status=400)
    
    # === POST: Task assignment ===
    if request.method == 'POST':
        with transaction.atomic():
            try:
                task_name = request.POST.get('task_name', '').strip()
                start_date_str = request.POST.get('start_date', '').strip()
                due_date_str = request.POST.get('due_date', '').strip()
                employee_input = request.POST.get('employee_emails', '').strip()
                team_id = request.POST.get('team_id', '').strip()

                if not task_name:
                    return JsonResponse({'status': 'error', 'message': 'Task name is required'}, status=400)
                if not start_date_str or not due_date_str:
                    return JsonResponse({'status': 'error', 'message': 'Both start date and deadline are required'}, status=400)

                try:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    
                    if start_date > due_date:
                        return JsonResponse({'status': 'error', 'message': 'Deadline cannot be before start date'}, status=400)
                        
                    if due_date < datetime.now().date():
                        return JsonResponse({'status': 'error', 'message': 'Deadline cannot be in the past'}, status=400)
                        
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Invalid date format. Use YYYY-MM-DD'}, status=400)

                if not team_id and not employee_input:
                    return JsonResponse({'status': 'error', 'message': 'Please assign to either a team or individuals'}, status=400)
                if team_id and employee_input:
                    return JsonResponse({'status': 'error', 'message': 'Please use either team OR individual assignment'}, status=400)

                # === Create the task ===
                task = Task.objects.create(
                    name=task_name,
                    start_date=start_date,
                    due_date=due_date,
                    created_by=user,
                    company=company
                )

                users = []

                # === Team Assignment ===
                if team_id:
                    team = Team.objects.filter(id=team_id, company=company).first()
                    if not team:
                        return JsonResponse({'status': 'error', 'message': 'Team not found in your company'}, status=404)

                    task.assigned_team = team
                    users = list(team.members.filter(employee__company=company))
                    task.assigned_to.set(users)

                # === Individual Assignment ===
                else:
                    employee_input_list = [i.strip() for i in employee_input.split(",") if i.strip()]
                    users = CustomUser.objects.filter(
                        (Q(email__in=employee_input_list) | Q(employee_id__in=employee_input_list)),
                        employee__company=company
                    ).distinct()

                    if not users.exists():
                        return JsonResponse({'status': 'error', 'message': 'No valid employees found in your company'}, status=404)

                    task.assigned_to.set(users)

                # === Notify all assigned users ===
                for user_obj in users:
                    Notification.objects.create(
                        recipient=user_obj,
                        message=f"You have been assigned a task: '{task_name}', starting on {start_date} with deadline on {due_date}.",
                        company=company
                    )

                task.save()

                return JsonResponse({
                    'status': 'success',
                    'message': f"Task '{task_name}' assigned successfully!",
                    'task_id': task.id,
                    'assignment_type': 'team' if team_id else 'individual'
                })

            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # === GET: Show tasks ===
    today = timezone.now().date()
    all_tasks = Task.objects.filter(
        created_by=user,
        created_by__employee__company=company
    ).order_by('-created_at')

    # === Apply filters ===
    employee_id = request.GET.get('employee_id', '')
    month = request.GET.get('month', '')

    if employee_id:
        try:
            filtered_user = CustomUser.objects.get(employee_id=employee_id, employee__company=company)
            all_tasks = all_tasks.filter(assigned_to=filtered_user)
        except CustomUser.DoesNotExist:
            all_tasks = Task.objects.none()

    if month:
        try:
            month_start = datetime.strptime(month, '%Y-%m').date()
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            all_tasks = all_tasks.filter(created_at__range=[month_start, month_end])
        except ValueError:
            pass

    # === Default: Show today's tasks ===
    if not employee_id and not month:
        all_tasks = all_tasks.filter(created_at__date=today)

    # === Remove duplicates ===
    seen = set()
    unique_tasks = []
    for task in all_tasks:
        key = (task.name, task.start_date, task.due_date, 
            tuple(u.id for u in task.assigned_to.all()), 
            task.assigned_team.id if task.assigned_team else None)
        if key not in seen:
            seen.add(key)
            unique_tasks.append(task)

    # === Month dropdown ===
    months = [
        {'num': f"{i:02d}", 'name': datetime(2025, i, 1).strftime('%B')}
        for i in range(1, 13)
    ]

    return render(request, 'task_management.html', {
        'employee': employee,
        'assigned_tasks': unique_tasks,
        'months': months,
        'current_month': datetime.now().strftime('%Y-%m'),
        'teams': teams,
        'today': today.strftime('%Y-%m-%d'),
        'filter_employee_id': employee_id,
        'filter_month': month
    })

@login_required
def tasks_by_date(request):
    if request.method == 'GET':
        date_str = request.GET.get('date')
        
        try:
            date = parse_date(date_str)
            if not date:
                return JsonResponse({'error': 'Invalid date format'}, status=400)
            
            # Get tasks that should be visible on this date:
            # - Start date is before or on this date
            # - Due date is after or on this date
            # - Assigned to current user (directly or via team)
            tasks = Task.objects.filter(
                Q(start_date__lte=date) & Q(due_date__gte=date),
                Q(assigned_to=request.user) | Q(assigned_team__members=request.user),
                completed=False
            ).distinct().order_by('due_date')
            
            tasks_data = [
                {
                    'id': task.id,
                    'name': task.name,
                    'start_date': task.start_date.strftime('%Y-%m-%d'),
                    'due_date': task.due_date.strftime('%Y-%m-%d'),
                    'completed': task.completed,
                    'assigned_by': task.created_by.get_full_name(),
                    'assigned_to': [user.get_full_name() for user in task.assigned_to.all()],
                    'is_team_task': bool(task.assigned_team),
                    'team_name': task.assigned_team.name if task.assigned_team else None
                }
                for task in tasks
            ]
            
            return JsonResponse({
                'tasks': tasks_data,
                'date': date.strftime('%Y-%m-%d')
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def mark_task_complete(request, task_id):
    try:
        task = Task.objects.get(
           Q(id=task_id) &
            (Q(assigned_to=request.user) | Q(assigned_team__members=request.user))
        )
        task.completed = True
        task.completed_at = timezone.now()
        task.save()
        
        # Add notification if needed
        Notification.objects.create(
            recipient=task.created_by,
            message=f"Task '{task.name}' was completed by {request.user.get_full_name()}",
            company=request.user.employee.company
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Task marked as completed',
            'completed_at': task.completed_at.strftime('%Y-%m-%d %H:%M:%S')
        })
   
    except Task.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Task not found or you are not authorized'
        }, status=404)


logger = logging.getLogger(__name__)

@require_GET
@login_required
def my_tasks(request):
    try:
        user = request.user
        current_date = timezone.now().date()  # Using timezone-aware now()
        
        # Get all tasks assigned to user (directly or via team membership)
        tasks = Task.objects.filter(
            Q(assigned_to=user) |  # Direct assignment
            Q(assigned_team__members=user)  # Team assignment
        ).distinct().select_related('created_by', 'assigned_team').prefetch_related('assigned_to')
        
        # Filter tasks based on dates and status
        active_tasks = tasks.filter(
            start_date__lte=current_date,
            due_date__gte=current_date,
            completed=False
        )
        
        upcoming_tasks = tasks.filter(
            start_date__gt=current_date,
            completed=False
        )
        
        completed_tasks = tasks.filter(completed=True)
        overdue_tasks = tasks.filter(
            due_date__lt=current_date,
            completed=False
        )

        # For AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            tasks_data = [{
                'id': task.id,
                'name': task.name,
                'start_date': task.start_date.strftime('%Y-%m-%d'),
                'due_date': task.due_date.strftime('%Y-%m-%d'),
                'status': get_task_status(task, current_date),
                'assigned_by': task.created_by.get_full_name(),
                'assigned_to': [u.get_full_name() for u in task.assigned_to.all()],
                'is_team_task': bool(task.assigned_team),
                'team_name': task.assigned_team.name if task.assigned_team else None
            } for task in tasks]
            
            return JsonResponse({
                'tasks': tasks_data,
                'current_date': current_date.strftime('%Y-%m-%d')
            })
        
        # For normal requests
        return render(request, 'task_management.html', {
            'active_tasks': active_tasks.order_by('due_date'),
            'upcoming_tasks': upcoming_tasks.order_by('start_date'),
            'completed_tasks': completed_tasks.order_by('-due_date'),
            'overdue_tasks': overdue_tasks.order_by('due_date'),
            'current_date': current_date,
            'show_my_tasks': True
        })

    except Exception as e:
        logger.error(f"Error in my_tasks view: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=500)
        return render(request, 'error.html', {'error': str(e)})
def get_task_status(task, current_date):
    """Helper function to determine task status"""
    if task.completed:
        return 'completed'
    elif task.due_date < current_date:
        return 'overdue'
    elif task.start_date > current_date:
        return 'upcoming'
    else:
        return 'active'


#------------------------------------------------------------- Expense claim #
@login_required(login_url='/')
def submit_expense_claim(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        date = request.POST.get('date')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        bill_no = request.POST.get('bill_no')
        receipt = request.FILES.get('receipt')

        # Create the expense claim
        expense_claiming = ExpenseClaim.objects.create(
            employee=request.user,
            category=category,
            date=date,
            description=description,
            amount=amount,
            bill_no=bill_no,
            receipt=receipt,
            status='pending'
        )

        # Create notification
        notification_message = (
            f"Your Expense Claim for '{category}' dated {date}, "
            f"amount ₹{amount}, Bill No: {bill_no} has been submitted successfully."
        )
        Notification.objects.create(
            recipient=request.user,
            message=notification_message
        )

        messages.success(request, "Expense claim submitted successfully!")
        return redirect('expense_claims')

    return JsonResponse({'success': False, 'error': "Invalid request."})

 
@login_required(login_url='/')
def expense_claims(request):
    user = request.user
    claims = ExpenseClaim.objects.filter(employee=user)
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'expense_claims.html', {
        'claims': claims,
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
#------------------------------------------------------------- Loan Requests #
 
@login_required(login_url='/')
def loan_requests(request):
    user = request.user
    loans = LoanRequest.objects.filter(employee=user)
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'loan_requests.html', {
        'loans': loans,
        'employee': employee,
        'notifications': notifications,
 
        }
    )
 
 
@login_required(login_url='/')
def submit_loan_request(request):
    employee = request.user
    if request.method == 'POST':
        loan_type = request.POST.get('loan_type')
        loan_amount = request.POST.get('loan_amount')
        repayment_duration = request.POST.get('repayment_duration')
        interest_rate = request.POST.get('interest_rate')
 
        # Validate loan amount: must be less than 10 digits before decimal
        try:
            # Remove commas and spaces if any
            loan_amount_clean = str(loan_amount).replace(',', '').replace(' ', '')
            if len(loan_amount_clean.split('.')[0]) > 9:
                messages.error(request, "Please enter a loan amount less than 10 digits.")
                return redirect('loan_requests')
        except Exception:
            messages.error(request, "Invalid loan amount format.")
            return redirect('loan_requests')
 
        loan_request = LoanRequest(
            employee=request.user,
            loan_type=loan_type,
            loan_amount=loan_amount,
            repayment_duration=repayment_duration,
            interest_rate=interest_rate,
            status='pending',
            date_requested=timezone.now()
        )
        notification_message = f"Your Loan request of {loan_type}, amount {loan_amount}, Duration {repayment_duration} with {interest_rate} % has been submitted successfully."
        Notification.objects.create(recipient=loan_request.employee, message=notification_message)
        loan_request.save()
 
        return redirect('loan_requests')
# ...existing code...
 
#------------------------------------------------------------- Reviews-Page #
 
@login_required(login_url='/')
@staff_member_required
def review_muster(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to view this page.")
   
    musters = Muster.objects.all()
    if request.method == 'POST':
        muster_id = request.POST.get('muster_id')
        status = request.POST.get('status')
        try:
            muster = Muster.objects.get(id=muster_id)
            muster.status = status
            muster.save()
        except Muster.DoesNotExist:
            pass
        return redirect('staff_notifications')
 
    musters = Muster.objects.all()
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'staff_notifications.html', {
        'musters': musters,
        'notifications': notifications,
        }
    )
 
#------------------------------------------------------------- Reviews - Leave Requests #
@login_required(login_url='/')
@staff_member_required
def review_leave(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to view this page.")
   
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        status = request.POST.get('status')
        try:
            leave_request = LeaveRequest.objects.get(id=leave_id)
            leave_balance = Leave.objects.get(employee=leave_request.employee)

            # ✅ Approve case
            if status == "Approved":
                if leave_request.status != "Approved":  # avoid double deduction
                    requested_leave_days = leave_balance.update_balance(
                        leave_request.leave_type,
                        leave_request.days_requested,
                        leave_request.start_date,
                        leave_request.end_date
                    )

                    if requested_leave_days > 0:
                        leave_request.days_requested = requested_leave_days

                leave_request.status = "Approved"
                leave_request.save()

                Notification.objects.create(
                    recipient=leave_request.employee,
                    message=f"Your Leave request from {leave_request.start_date} to {leave_request.end_date} has been approved."
                )

            # ✅ Reject case
            elif status == "Rejected":
                # If previously approved → restore balance
                if leave_request.status == "Approved":
                    if leave_request.leave_type == "advance_privilege":
                        leave_balance.advance_privilege_leave += leave_request.days_requested
                    elif leave_request.leave_type == "sick":
                        leave_balance.sick_leave += leave_request.days_requested
                    elif leave_request.leave_type == "casual":
                        leave_balance.casual_leave += leave_request.days_requested
                    leave_balance.save()

                leave_request.status = "Rejected"
                leave_request.save()

                Notification.objects.create(
                    recipient=leave_request.employee,
                    message=f"Your Leave request from {leave_request.start_date} to {leave_request.end_date} has been rejected."
                )

        except LeaveRequest.DoesNotExist:
            messages.error(request, "Leave request not found.")
        except Leave.DoesNotExist:
            messages.error(request, "Leave balance record not found for this employee.")

        return redirect('staff_notifications')

    # GET flow
    leaves = LeaveRequest.objects.all()
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')

    return render(request, 'staff_notifications.html', {
        'leaves': leaves,
        'notifications': notifications,
    })

#------------------------------------------------------------- Reviews - Expense Claims #
@login_required(login_url='/')
@staff_member_required
def review_expense(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to view this page.")
   
    expenses = ExpenseClaim.objects.all()
    if request.method == 'POST':
        expense_id = request.POST.get('expense_id')
        status = request.POST.get('status')
        try:
            expense = ExpenseClaim.objects.get(id=expense_id)
            expense.status = status
            expense.save()
        except ExpenseClaim.DoesNotExist:
            pass
        return redirect('staff_notifications')
 
    expenses = ExpenseClaim.objects.all()
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'staff_notifications.html', {
        'expenses': expenses,
        'notifications': notifications,
        }
    )
 
#------------------------------------------------------------- Reviews - Loan Requests #
@login_required(login_url='/')
@staff_member_required
def review_loan(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not authorized to view this page.")
   
    loans = LoanRequest.objects.all()
    if request.method == 'POST':
        loan_id = request.POST.get('loan_id')
        status = request.POST.get('status')
        try:
            loan = LoanRequest.objects.get(id=loan_id)
            loan.status = status
            loan.save()
        except LoanRequest.DoesNotExist:
            pass
        return redirect('staff_notifications')
 
    loans = LoanRequest.objects.all()
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'staff_notifications.html', {
        'loans': loans,
        'notifications': notifications,
        }
    )

#------------------------------------------------------------- Reviews - Notification Bar #
 
@login_required(login_url='/')
@staff_member_required
def review_muster_notifications(request, muster_id, action):
    muster_request = get_object_or_404(Muster, id=muster_id)
 
    if action == 'Approve':
        muster_request.status = 'Approved'
        muster_request.save()
        message = f"Your muster from {muster_request.clock_in_time} to {muster_request.clock_out_time} has been approved."
        Notification.objects.create(recipient=muster_request.user, message=message)
 
    elif action == 'Reject':
        muster_request.status = 'Rejected'
        muster_request.save()
        message = f"Your muster from {muster_request.clock_in_time} to {muster_request.clock_out_time} has been rejected."
        Notification.objects.create(recipient=muster_request.user, message=message)
 
    return redirect('dashboard')

#------------------------------------------------------------- Reviews - Leave Requests - Notification Bar # 
@login_required(login_url='/')
@staff_member_required
def review_leaves_notifications(request, leaves_id, action):
    leave_request = get_object_or_404(LeaveRequest, id=leaves_id)
    leave_balance = Leave.objects.get(employee=leave_request.employee)
 
    if action == 'Approve':
        leave_request.status = 'Approved'
        leave_request.save()
        message = f"Your Leave request from {leave_request.start_date} to {leave_request.end_date} has been approved."
        Notification.objects.create(recipient=leave_request.employee, message=message)
 
        requested_leave_days = leave_balance.update_balance(
            leave_request.leave_type,
            leave_request.days_requested,
            leave_request.start_date,
            leave_request.end_date
        )
 
        if requested_leave_days > 0:
            leave_request.days_requested = requested_leave_days
            leave_request.save()
 
    elif action == 'Reject':
        leave_request.status = 'Rejected'
        leave_request.save()
        message = f"Your Leave request from {leave_request.start_date} to {leave_request.end_date} has been rejected."
        Notification.objects.create(recipient=leave_request.employee, message=message)
 
    return redirect('dashboard')

#------------------------------------------------------------- Reviews - Expense Claims - Notification Bar #
@login_required(login_url='/')
@staff_member_required
def review_expense_notifications(request, expense_id, action):
    expense_claim = get_object_or_404(ExpenseClaim, id=expense_id)
 
    if action == 'Approve':
        expense_claim.status = 'Approved'
        expense_claim.save()
        message = f"Your Expense claim {expense_claim.amount} , {expense_claim.bill_no} has been approved."
        Notification.objects.create(recipient=expense_claim.employee, message=message)
 
    elif action == 'Reject':
        expense_claim.status = 'Rejected'
        expense_claim.save()
        message = f"Your Expense claim {expense_claim.amount} , {expense_claim.bill_no} has been rejected."
        Notification.objects.create(recipient=expense_claim.employee, message=message)
 
    return redirect('dashboard')

#------------------------------------------------------------- Reviews - Loan Requests - Notification Bar #
@login_required(login_url='/')
@staff_member_required
def review_loan_notifications(request, loan_id, action):
    loan_request = get_object_or_404(LoanRequest, id=loan_id)
 
    if action == 'Approve':
        loan_request.status = 'Approved'
        loan_request.save()
        message = f"Your loan request {loan_request.loan_type} to {loan_request.loan_amount} has been approved."
        Notification.objects.create(recipient=loan_request.employee, message=message)
 
    elif action == 'Reject':
        loan_request.status = 'Rejected'
        loan_request.save()
        message = f"Your loan request {loan_request.loan_type} to {loan_request.loan_amount} has been rejected."
        Notification.objects.create(recipient=loan_request.employee, message=message)
 
    return redirect('dashboard')
 
 
#------------------------------------------------------------- Reviews-notification bar # 
@login_required(login_url='/')
@staff_member_required
def user_list(request):
    employee_id_filter = request.GET.get('employee_id')
    user = request.user
 
    try:
        employee = Employee.objects.get(employee_id=user.employee_id)
        company = employee.company
    except Employee.DoesNotExist:
        company = None
 
    # Filter users by company
    user_query = CustomUser.objects.filter(company=company) if company else CustomUser.objects.none()
 
    if employee_id_filter:
        user_query = user_query.filter(employee_id=employee_id_filter)
 
    notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'user_list.html', {
        'users': user_query,
        'employee': employee,
        'notifications': notifications,
        'employee_id_filter': employee_id_filter,
    })
 
#------------------------------------------------------------- Add/Edit Users by Staff #
@login_required(login_url='/')
@staff_member_required
def user_create(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    company = employee.company
 
    if request.method == 'POST':
        form = FrontendUserForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.company = company  # Assign company
            new_user.save()
            messages.success(request, "User created successfully!")
            return redirect('user_list')
    else:
        form = FrontendUserForm()
 
    notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'user_form.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications,
    })
 
 
#------------------------------------------------------------- Edit Users by Staff #
@login_required(login_url='/')
@staff_member_required
def user_edit(request, pk):
    current_employee = Employee.objects.get(employee_id=request.user.employee_id)
    company = current_employee.company

    # Secure access
    user_to_edit = get_object_or_404(CustomUser, pk=pk, company=company)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_to_edit)
        if form.is_valid():
            user = form.save(commit=False)

            # If password provided, set it properly
            password = form.cleaned_data.get('password')
            if password:
                user.set_password(password)

            user.save()
            messages.success(request, "User updated successfully!")
            return redirect('user_list')
    else:
        form = UserEditForm(instance=user_to_edit)

    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')

    return render(request, 'user_form.html', {
        'form': form,
        'employee': current_employee,
        'notifications': notifications,
    })

 
#------------------------------------------------------------- Delete Users by Staff #
@login_required(login_url='/')
@staff_member_required
def user_confirm_delete(request, pk):
    current_employee = Employee.objects.get(employee_id=request.user.employee_id)
    company = current_employee.company
 
    # Secure delete
    user_to_delete = get_object_or_404(CustomUser, pk=pk, company=company)
 
    if request.method == 'POST':
        user_to_delete.delete()
        messages.success(request, 'User deleted successfully!')
        return redirect('user_list')
 
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'user_confirm_delete.html', {
        'emp': user_to_delete,
        'current_employee': current_employee,
        'notifications': notifications
    })
 
#------------------------------------------------------------- Policies #
 
@login_required(login_url='/')
def policy(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'policy.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
@login_required(login_url='/')
def data_retention_policy(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'data_retention_policy.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
@login_required(login_url='/')
def acceptable_use_policy(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'acceptable_use_policy.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
@login_required(login_url='/')
def cookie_policy(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'cookie_policy.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
@login_required(login_url='/')
def refund_cancellation_policy(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'refund_cancellation_policy.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
@login_required(login_url='/')
def terms_of_service(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'terms_of_service.html' , {
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
#------------------------------------------------------------- Add salaries by Staff #
 
@login_required(login_url='/')
@staff_member_required
def create_salary(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    company = user.company  # Get the logged-in user's company
 
    employee_id_filter = request.GET.get('employee_id', '')
    month_filter = request.GET.get('month', '')
    filtered_employee = None
 
    if month_filter:
        try:
            month_filter = datetime.strptime(month_filter, '%Y-%m')
        except ValueError:
            month_filter = None
 
    # Only allow filtering by employee in same company
    if employee_id_filter:
        filtered_employee = Employee.objects.filter(employee_id=employee_id_filter, company=company).first()
        if not filtered_employee:
            messages.error(request, "No employee found with that ID in your company.")
            return redirect('create_salary')
 
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            salary_instance = form.save(commit=False)
 
            # Ensure the employee belongs to the same company before saving
            if salary_instance.employee.company != company:
                messages.error(request, "You cannot assign salary for an employee outside your company.")
                return redirect('create_salary')
 
            salary_instance.save()
            messages.success(request, "Salary created successfully.")
            return redirect('salary_list')
    else:
        form = SalaryForm()
 
    notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')
 
    return render(request, 'create_salary.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications,
        'employee_id_filter': employee_id_filter,
        'month_filter': month_filter,
    })
 
#------------------------------------------------------------- View/Edit/Delete Salaries by Staff #
@login_required(login_url='/')
@staff_member_required
def view_salary(request, salary_id):
    salary = get_object_or_404(Salary, id=salary_id)
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'view_salary.html', {
        'salary': salary,
        'employee': employee,
        'notifications': notifications,
        }
    )
 
 
@login_required(login_url='/')
@staff_member_required
def edit_salary(request, salary_id):
    salary = get_object_or_404(Salary, id=salary_id)
 
    if request.method == 'POST':
        form = SalaryForm(request.POST, instance=salary)
        if form.is_valid():
            form.save()
            return redirect('salary_list')
    else:
        form = SalaryForm(instance=salary)
 
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'edit_salary.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications,
        }
    )
 
@login_required(login_url='/')
@staff_member_required
def delete_salary(request, salary_id):
    salary = get_object_or_404(Salary, id=salary_id)
 
    if request.method == 'POST':
        salary.delete()
        return redirect('salary_list')
    return render(request, 'delete_salary.html')
 
 
@login_required(login_url='/')
@staff_member_required
def salary_list(request):
    user = request.user
 
    # Get the current user's company from CustomUser model
    user_company = user.company
 
    # Get the associated employee record (if needed for context)
    try:
        employee = Employee.objects.get(employee_id=user.employee_id)
    except Employee.DoesNotExist:
        employee = None
 
    # Filters
    employee_id_filter = request.GET.get('employee_id')
    month_filter = request.GET.get('month')
 
    # Start salary query limited to this user's company
    salary_query = Salary.objects.filter(employee__company=user_company)
 
    # Filter by employee ID (within the same company)
    if employee_id_filter:
        salary_query = salary_query.filter(employee__employee_id=employee_id_filter)
 
    # Filter by month (safe parsing)
    if month_filter:
        try:
            month_date = datetime.strptime(month_filter, '%Y-%m')
            salary_query = salary_query.filter(
                month__year=month_date.year,
                month__month=month_date.month
            )
        except ValueError:
            salary_query = Salary.objects.none()  # Invalid month format
 
    # Get unread notifications (only from this user's company if needed)
    notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).order_by('-created_at')
 
    return render(request, 'salary_list.html', {
        'salaries': salary_query,
        'employee': employee,
        'notifications': notifications,
        'employee_id_filter': employee_id_filter,
        'month_filter': month_filter,
    })
 
 
#------------------------------------------------------------- Performance #
 
'''@login_required(login_url='/')
@staff_member_required
def performance_entry(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'performance_entry.html', {
        'employee': employee,
        'notifications': notifications
        })
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
 
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_performance(request):
    employee_id = request.data.get('employee_id')
    performance_score = request.data.get('performance_score')
 
    if not employee_id or performance_score is None:
        return Response({'error': 'Missing fields'}, status=400)
 
    try:
        # Get the employee that is being submitted
        employee_id = Employee.objects.get(employee_id=employee_id)
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=404)
 
    try:
        # Get the logged-in user’s employee instance
        logged_in_employee = Employee.objects.get(employee_id=request.user.employee_id)
    except Employee.DoesNotExist:
        return Response({'error': 'Unauthorized access'}, status=403)
 
    # Check if both employees belong to the same company
    if employee_id.company != logged_in_employee.company:
        return Response({'error': 'You can only submit performance for employees in your company'}, status=403)
 
    Performance.objects.create(employee=employee_id, performance_score=performance_score)
    return Response({'message': 'Performance submitted successfully'})
 
 
 
@api_view(['GET'])
def top_daily_performers(request):
    today = now().date()
    top_performers = Performance.objects.filter(date=today).order_by('-performance_score')[:5]
    serializer = PerformanceSerializer(top_performers, many=True)
    return Response(serializer.data)
 
 
@api_view(['GET'])
def best_monthly_performer(request):
    first_day = now().replace(day=1)
    last_day = first_day + timedelta(days=30)
    top_performer = Performance.objects.filter(date__range=[first_day, last_day]).order_by('-performance_score').first()
    if top_performer:
        serializer = PerformanceSerializer(top_performer)
        return Response(serializer.data)
    return Response({'message': 'No data available'}, status=404)
 
 
@login_required(login_url='/')
def performance_page(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
   
    # Filter only performances in user's company
    performance_data = Performance.objects.filter(employee__company=employee.company)
 
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:5]
 
    return render(request, 'performance_page.html', {
        'performance_data': performance_data,
        'employee': employee,
        'notifications': notifications,
    })'''
 
 
 
#------------------------------------------------------------- Working days #
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import F, ExpressionWrapper, DurationField

  # Mon–Fri only
@login_required
def working_days(request):
    selected_month = request.GET.get('month')
    selected_emp_id = request.GET.get('employee_id')

    now = timezone.now()
    if selected_month:
        year = int(selected_month.split('-')[0])
        month = int(selected_month.split('-')[1])
    else:
        year = now.year
        month = now.month


    # 🔐 Filter users by logged-in user's company
    current_company = request.user.company
    users = CustomUser.objects.filter(company=current_company)

    if selected_emp_id:
        users = users.filter(employee_id__icontains=selected_emp_id)

    employee_data = []

    for user in users:
        name = f"{user.first_name} {user.last_name}"
        emp_id = user.employee_id

        # Regular days
        regular_count = TimeEntry.objects.filter(
            user=user,
            clock_in_time__month=month,
            clock_in_time__year=year
        ).filter(
            clock_in_time__isnull=False,
            clock_out_time__isnull=False
        ).annotate(
            duration=ExpressionWrapper(
                F('clock_out_time') - F('clock_in_time'),
                output_field=DurationField()
            )
        ).filter(
            duration__gte=timedelta(hours=9)
        ).count()

        # Approved muster
        approved_muster_count = Muster.objects.filter(
            user=user,
            status="Approved",
            date__month=month,
            date__year=year
        ).count()

        # Leaves (optional logic)
        leaves_taken = Muster.objects.filter(
            user=user,
            status="Approved",
            date__month=month,
            date__year=year,
            reason__in=['On-site', 'Work From Home', 'Forgot Login/out', 'Forgot Logout', 'Network Issue']
        ).count()

        total_present_days = regular_count + approved_muster_count
        total_working_days = regular_count+ approved_muster_count-leaves_taken

        employee_data.append({
            'employee_id': emp_id,
            'name': name,
            'working_days': total_present_days,
            'leaves': leaves_taken,
            'total_days': total_working_days,
        })

    # Month filter dropdown
    month_years = Muster.objects.annotate(
        year=ExtractYear('date'),
        month=ExtractMonth('date')
    ).values_list('year', 'month').distinct().order_by('-year', '-month')

    month_options = [
        {
            'value': f"{y}-{str(m).zfill(2)}",
            'label': f"{calendar.month_name[m]} {y}"
        }
        for y, m in month_years
    ]

    return render(request, 'working_days.html', {
        'employee_data': employee_data,
        'month_options': month_options,
        'selected_month': f"{year}-{str(month).zfill(2)}",
        'selected_emp_id': selected_emp_id or '',
    })


   
#------------------------------------------------------------- Company adding by staff #
 
@login_required(login_url='/')
@staff_member_required
def company_list(request):
    companies = Company_check.objects.all()
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'company_list.html', {'companies': companies,'employee': employee,'notifications': notifications})
 
@login_required(login_url='/')
@staff_member_required
def company_create(request):
    if request.method == 'POST':
        form = Company_checkForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = Company_checkForm()
   
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'company_form.html', {'form': form,'employee': employee,'notifications': notifications})
 
@login_required(login_url='/')
@staff_member_required
def company_edit(request, pk):
    company = get_object_or_404(Company_check, pk=pk)
    if request.method == 'POST':
        form = Company_checkForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = Company_checkForm(instance=company)
   
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'company_form.html', {'form': form,'employee': employee,'notifications': notifications})
 
@login_required(login_url='/')
@staff_member_required
def company_delete(request, pk):
    company = get_object_or_404(Company_check, pk=pk)
    if request.method == 'POST':
        company.delete()
        return redirect('company_list')
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'company_delete.html', {'company': company,'employee': employee,'notifications': notifications})
 
 
#------------------------------------------------------------- Task list by staff #
from django.db.models import Prefetch
 
@login_required(login_url='/')
@staff_member_required
def task_list(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    company = employee.company  # ✅ Logged-in user's company
 
    # ✅ Filter tasks strictly inside same company (creator + assignee)
    tasks = Task.objects.filter(
        Q(created_by__employee__company=company) &
        Q(assigned_to__employee__company=company)
    ).prefetch_related('assigned_to').order_by('-created_at')
 
    # Filters
    employee_id = request.GET.get('employee_id', '')
    month = request.GET.get('month', '')
 
    if employee_id:
        try:
            employee_filter = CustomUser.objects.get(employee_id=employee_id)
            tasks = tasks.filter(assigned_to=employee_filter)
        except CustomUser.DoesNotExist:
            tasks = Task.objects.none()
 
    if month:
        try:
            month_start = datetime.strptime(month, '%Y-%m').date()
            month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            tasks = tasks.filter(due_date__range=[month_start, month_end])
        except ValueError:
            pass
 
    # ✅ Remove duplicates manually
    seen = set()
    unique_tasks = []
    for task in tasks:
        key = (task.name, task.due_date, task.created_by_id)
        if key not in seen:
            seen.add(key)
            unique_tasks.append(task)
 
    months = [
        {'num': f"{i:02d}", 'name': datetime(2025, i, 1).strftime('%B')}
        for i in range(1, 13)
    ]
 
    notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')
 
    return render(request, 'task_list.html', {
        'tasks': unique_tasks,
        'months': months,
        'employee': employee,
        'notifications': notifications,
        'current_month': datetime.now().strftime('%Y-%m')
    })
 
#------------------------------------------------------------- Company adding by staff #
 
'''from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Performance, Employee, Notification
 
@login_required(login_url='/')
@staff_member_required
def performance_list(request):
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    last_day_of_month = first_day_of_month + timedelta(days=31)
    last_day_of_month = last_day_of_month.replace(day=1) - timedelta(days=1)
 
    # Get current logged-in employee's company
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    company = employee.company
 
    # Filter performance data by current month AND company
    performance_data = Performance.objects.filter(
        date__range=[first_day_of_month, last_day_of_month],
        employee__company=company
    )
 
    # Filters (by employee_id and month) while respecting the company
    employee_id = request.GET.get('employee_id')
    month = request.GET.get('month')
 
    if employee_id:
        performance_data = performance_data.filter(employee__employee_id=employee_id, employee__company=company)
 
    if month:
        month_start = timezone.datetime.strptime(month, '%Y-%m').date()
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        performance_data = performance_data.filter(date__range=[month_start, month_end], employee__company=company)
 
    # Get employees of that company only
    employees = Employee.objects.filter(company=company)
 
    months = [
        (timezone.datetime(today.year, m, 1).strftime('%Y-%m'),
         timezone.datetime(today.year, m, 1).strftime('%B'))
        for m in range(1, 13)
    ]
 
    # Notifications
    notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
 
    return render(request, 'performance_list.html', {
        'performance_data': performance_data,
        'employees': employees,
        'current_month': today.month,
        'current_year': today.year,
        'months': months,
        'employee': employee,
        'notifications': notifications
    })'''
 
 
 
#------------------------------------------------------------- Company adding by staff #
 
@login_required(login_url='/')
@staff_member_required
def employee_list(request):
    user = request.user
    employee_id_filter = request.GET.get('employee_id')
 
    try:
        current_employee = Employee.objects.get(employee_id=user.employee_id)
        company = current_employee.company
    except Employee.DoesNotExist:
        company = None
 
    # Default to empty list if company not found
    employee_query = Employee.objects.none()
 
    if company:
        employee_query = Employee.objects.filter(company=company)
 
        # Apply employee_id filter if provided
        if employee_id_filter:
            employee_query = employee_query.filter(employee_id=employee_id_filter)
 
    notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'employee_list.html', {
        'employee_query': employee_query,
        'employee': current_employee if company else None,
        'notifications': notifications,
        'employee_id_filter': employee_id_filter,
    })

@login_required(login_url='/')
@staff_member_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST, request.FILES)
        media_form = EmployeeMediaForm(request.POST, request.FILES)

        if form.is_valid() and media_form.is_valid():
            employee_id = form.cleaned_data['employee_id']
            try:
                user = CustomUser.objects.get(employee_id=employee_id)
                if not user.company:
                    messages.error(request, "This user has no company assigned.")
                else:
                    employee = form.save(commit=False)
                    employee.user = user
                    employee.company = user.company
                    employee.save()
                    
                    media = media_form.save(commit=False)
                    media.employee = employee
                    media.save()
                    
                    messages.success(request, 'Employee created successfully!')
                    return redirect('employee_list')
            except CustomUser.DoesNotExist:
                form.add_error('employee_id', 'User not found')
    else:
        form = EmployeeProfileForm()
        media_form = EmployeeMediaForm()

    return render(request, 'employee_create.html', {
        'form': form,
        'media_form': media_form,
        'notifications': Notification.objects.filter(recipient=request.user, is_read=False)
    })


@login_required
def upload_employee_media(request):
    employee = Employee.objects.get(user=request.user)
    media, _ = EmployeeMedia.objects.get_or_create(employee=employee)
 
    if request.method == 'POST':
        form = EmployeeMediaForm(request.POST, request.FILES, instance=media)
        if form.is_valid():
            form.save()
            messages.success(request, "Images updated!")
            return redirect('profile')  # Or wherever you go
    else:
        form = EmployeeMediaForm(instance=media)
 
    return render(request, 'upload_media.html', {'form': form})
 
# --- Edit Profile Picture ---
@login_required(login_url='/')
def edit_profile_picture(request):
    try:
        employee = Employee.objects.get(user=request.user)
        employee_media, _ = EmployeeMedia.objects.get_or_create(employee=employee)
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('profile')
 
 
 
    if request.method == 'POST':
        form = EmployeeMediaForm(request.POST, request.FILES, instance=employee_media)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile picture updated successfully!")
            return redirect('profile')
    else:
        form = EmployeeMediaForm(instance=employee_media)
 
    return render(request, 'profile.html', {'form': form})
 
 
# --- Edit Cover Picture ---
@login_required(login_url='/')
def edit_cover_picture(request):
    try:
        employee = Employee.objects.get(user=request.user)
        employee_media, _ = EmployeeMedia.objects.get_or_create(employee=employee)
    except Employee.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('profile')
   
 
    if request.method == 'POST':
        form = EmployeeMediaForm(request.POST, request.FILES, instance=employee_media)
        if form.is_valid():
            form.save()
            messages.success(request, "Cover picture updated successfully!")
            return redirect('profile')
    else:
        form = EmployeeMediaForm(instance=employee_media)
 
    return render(request, 'profile.html', {'form': form})


@login_required(login_url='/')
@staff_member_required
def employee_edit(request, pk):
    user = request.user
    current_employee = Employee.objects.get(employee_id=user.employee_id)
    employee = get_object_or_404(Employee, pk=pk, company=current_employee.company)

    # Get or create related media
    employee_media, _ = EmployeeMedia.objects.get_or_create(employee=employee)

    if request.method == 'POST':
        form = EmployeeProfileForm(request.POST, request.FILES, instance=employee)
        media_form = EmployeeMediaForm(request.POST, request.FILES, instance=employee_media)

        if form.is_valid() and media_form.is_valid():
            form.save()
            media_form.save()
            messages.success(request, 'Employee updated successfully!')
            return redirect('employee_list')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = EmployeeProfileForm(instance=employee)
        media_form = EmployeeMediaForm(instance=employee_media)

    return render(request, 'employee_create.html', {
        'form': form,
        'media_form': media_form,
        'employee': employee,
        'notifications': Notification.objects.filter(
            recipient=request.user, is_read=False
        ).order_by('-created_at'),
        'edit_mode': True
    })


@login_required(login_url='/')
@staff_member_required
def employee_delete(request, pk):
    user = request.user
    current_employee = Employee.objects.get(employee_id=user.employee_id)
 
    # Only allow deleting if same company
    employee = get_object_or_404(Employee, pk=pk, company=current_employee.company)
 
    if request.method == 'POST':
        employee.delete()
        messages.success(request, 'Employee deleted successfully!')
        return redirect('employee_list')
 
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
 
    return render(request, 'employee_delete.html', {
        'employee': employee,
        'current_employee': current_employee,
        'notifications': notifications
    })
 
#------------------------------------------------------------- Holidays adding by staff #
 
@staff_member_required
def holidays_list(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    holidays = Holiday.objects.filter(company=employee.company).order_by('date')  # ✅ Filter here
 
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'holidays_list.html', {
        'holidays': holidays,
        'employee': employee,
        'notifications': notifications
})
 
 
@login_required(login_url='/')
@staff_member_required
def holiday_create(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    if request.method == 'POST':
        form = HolidaysForm(request.POST)
        if form.is_valid():
            holiday = form.save(commit=False)
            holiday.company = employee.company  # ✅ Set current company
            holiday.save()
            return redirect('holidays_list')
    else:
        form = HolidaysForm()
 
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'holiday_form.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications
    })
 
 
@login_required(login_url='/')
@staff_member_required
def holiday_view(request, pk):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    # Secure: Only access holidays from the same company
    holiday = get_object_or_404(Holiday, pk=pk, company=employee.company)
 
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'holiday_view.html', {'holiday': holiday, 'employee': employee, 'notifications': notifications})
 
 
@login_required(login_url='/')
@staff_member_required
def holiday_edit(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        form = HolidaysForm(request.POST, instance=holiday)
        if form.is_valid():
            form.save()
            return redirect('holidays_list')
    else:
        form = HolidaysForm(instance=holiday)
   
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'holiday_form.html', {'form': form,'employee': employee,'notifications': notifications})
 
@login_required(login_url='/')
@staff_member_required
def holiday_delete(request, pk):
    holiday = get_object_or_404(Holiday, pk=pk)
    if request.method == 'POST':
        holiday.delete()
        return redirect('holidays_list')
   
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    return render(request, 'holiday_delete.html', {'holiday': holiday,'employee': employee,'notifications': notifications})
 
 
#------------------------------------------------------------- Leave balance adding by staff #
 
@login_required(login_url='/')
@staff_member_required
def leave_list(request):
    employee_id_filter = request.GET.get('employee_id')
 
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    # Filter leaves only for this company
    leave_query = Leave.objects.filter(company=employee.company)
 
    if employee_id_filter:
        leave_query = leave_query.filter(employee__employee_id=employee_id_filter)
 
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'leave_list.html', {
        'leaves': leave_query,
        'employee': employee,
        'notifications': notifications,
        'employee_id_filter': employee_id_filter,
    })
 
 
 
@login_required(login_url='/')
@staff_member_required
def leave_create(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    if request.method == 'POST':
        form = LeaveForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.company = employee.company  # ✅ Assign company
            leave.save()
            return redirect('leave_list')
    else:
        form = LeaveForm()
        # Optional: Filter employees by company
        form.fields['employee'].queryset = CustomUser.objects.filter(company=employee.company)
 
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'leave_create.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications
    })
 
 
@login_required(login_url='/')
@staff_member_required
def leave_detail(request, pk):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    # Ensure only leaves for that company are fetched
    leave = get_object_or_404(Leave, pk=pk, company=employee.company)
 
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')

 
    return render(request, 'leave_detail.html', {
        'leave': leave,
        'employee': employee,
        'notifications': notifications
    })
 
@login_required(login_url='/')
@staff_member_required
def leave_edit(request, pk):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    leave = get_object_or_404(Leave, pk=pk, company=employee.company)
 
    if request.method == 'POST':
        form = LeaveForm(request.POST, instance=leave)
        if form.is_valid():
            form.save()
            return redirect('leave_list')
    else:
        form = LeaveForm(instance=leave)
 
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'leave_edit.html', {
        'form': form,
        'employee': employee,
        'notifications': notifications
    })
 
@login_required(login_url='/')
@staff_member_required
def leave_delete(request, pk):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
 
    leave = get_object_or_404(Leave, pk=pk, company=employee.company)
 
    if request.method == "POST":
        leave.delete()
        return redirect('leave_list')
 
    notifications = Notification.objects.filter(
        recipient=request.user, is_read=False
    ).order_by('-created_at')
 
    return render(request, 'leave_delete.html', {
        'leave': leave,
        'employee': employee,
        'notifications': notifications
    })
 
# ----------------------------------------------Main views  HR4U content
@login_required
def hr_services_page(request):
    user = request.user
    employee = Employee.objects.get(employee_id=user.employee_id)
    company = employee.company

    form = HRContactForm(request.POST or None, company=company)

    if request.method == 'POST':
        if form.is_valid():
            instance = form.save(commit=False)

            # Prevent assigning duplicate role to same employee
            existing = HRContact.objects.filter(
                employee=instance.employee,
            ).exclude(pk=instance.pk).first()

            if existing:
                form.add_error('employee', 'This employee already has an assigned role.')
            else:
                instance.save()
                return redirect('hr_services')

    contacts = HRContact.objects.filter(employee__company=company).order_by('role')
    return render(request, 'hr_services.html', {
        'form': form,
        'contacts': contacts,
    })

@login_required
def edit_hr_contact(request, pk):
    contact = get_object_or_404(HRContact, pk=pk)

    employee = Employee.objects.get(employee_id=request.user.employee_id)
    company = employee.company

    if request.method == 'POST':
        form = HRContactForm(request.POST, instance=contact, company=company)
        if form.is_valid():
            instance = form.save(commit=False)

            # Check for duplication (except self)
            existing = HRContact.objects.filter(
                employee=instance.employee
            ).exclude(pk=contact.pk).first()

            if existing:
                form.add_error('employee', 'This employee is already assigned a role.')
            else:
                instance.save()
                return redirect('hr_services')
    else:
        form = HRContactForm(instance=contact, company=company)

    contacts = HRContact.objects.filter(employee__company=company).order_by('role')
    return render(request, 'hr_services.html', {
        'form': form,
        'contacts': contacts
    })


@login_required
def delete_hr_contact(request, pk):
    contact = get_object_or_404(HRContact, pk=pk)
    contact.delete()
    return redirect('hr_services')


def assign_manager(ticket, company):
    manager_contact = HRContact.objects.filter(role='MG').first()
    if manager_contact:
        try:
            ticket.manager = User.objects.get(email=manager_contact.email, employee__company=company)
        except User.DoesNotExist:
            ticket.manager = None

@login_required
def hr4u_dashboard(request):
    """Main HR4U dashboard view"""
    return render(request, 'HR4U.html')


from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def help_desk_page(request):
    user = request.user
    user_employee = Employee.objects.get(employee_id=user.employee_id)
    company = user_employee.company
    current_time = now()

    notifications = Notification.objects.filter(recipient=user, is_read=False).order_by('-created_at')

    # Get HRContact entries for this company
    tl_contacts = HRContact.objects.filter(role='TL', employee__company=company)
    hr_contacts = HRContact.objects.filter(role='HR', employee__company=company)
    mg_contacts = HRContact.objects.filter(role='MG', employee__company=company)

    # Get User QuerySets from contacts for form choices
    team_leader_qs = User.objects.filter(id__in=tl_contacts.values_list('employee__user_id', flat=True))
    hr_qs = User.objects.filter(id__in=hr_contacts.values_list('employee__user_id', flat=True))
    manager_qs = User.objects.filter(id__in=mg_contacts.values_list('employee__user_id', flat=True))

    # Prepare forms
    hr_form = HelpDeskTicketForm(prefix='hr', category='HR', company=company)
    it_form = HelpDeskTicketForm(prefix='it', category='IT', company=company)
    asset_form = HelpDeskTicketForm(prefix='as', category='AS', company=company)

    for form in [hr_form, it_form, asset_form]:
        form.fields['team_leader'].queryset = team_leader_qs
        form.fields['hr'].queryset = hr_qs
        form.fields['manager'].queryset = manager_qs

    def send_ticket_email(ticket, to_user, subject_prefix):
        if to_user and to_user.email:
            send_mail(
                subject=f"[{subject_prefix}] Help Desk Ticket #{ticket.id}",
                message=(
                    f"Dear {to_user.get_full_name() or to_user.username},\n\n"
                    f"A new ticket has been raised by {ticket.employee}.\n\n"
                    f"Category: {ticket.get_category_display()}\n"
                    f"Issue Type: {ticket.issue_type}\n\n"
                    f"Description:\n{ticket.description}"
                ),
                from_email=None,
                recipient_list=[to_user.email],
                fail_silently=False
            )

    # Handle POST actions: close, mark seen by TL or HR, or submit ticket forms
    if request.method == 'POST':
        if 'close_ticket_id' in request.POST:
            ticket_id = request.POST.get('close_ticket_id')
            try:
                ticket = HelpDeskTicket.objects.get(id=ticket_id, employee=user)
                ticket.status = 'closed'
                ticket.save()
            except HelpDeskTicket.DoesNotExist:
                pass
            return redirect('help_desk')

        if 'mark_seen_tl' in request.POST:
            ticket_id = request.POST.get('ticket_id')
            HelpDeskTicket.objects.filter(id=ticket_id, assigned_to=user).update(viewed_by_tl=True)
            return redirect('help_desk')

        if 'mark_seen_hr' in request.POST:
            ticket_id = request.POST.get('ticket_id')
            HelpDeskTicket.objects.filter(id=ticket_id, escalate_to_hr=user).update(viewed_by_hr=True)
            return redirect('help_desk')

        # Ticket submission forms
        submitted_category = None
        if 'hr-submit' in request.POST:
            hr_form = HelpDeskTicketForm(request.POST, prefix='hr', category='HR', company=company)
            submitted_category = 'HR'
        elif 'it-submit' in request.POST:
            it_form = HelpDeskTicketForm(request.POST, prefix='it', category='IT', company=company)
            submitted_category = 'IT'
        elif 'as-submit' in request.POST:
            asset_form = HelpDeskTicketForm(request.POST, prefix='as', category='AS', company=company)
            submitted_category = 'AS'

        selected_form = {
            'HR': hr_form,
            'IT': it_form,
            'AS': asset_form
        }.get(submitted_category)

        if selected_form and selected_form.is_valid():
            ticket = selected_form.save(commit=False)
            ticket.employee = user
            ticket.category = submitted_category
            ticket.assigned_to = selected_form.cleaned_data['team_leader']
            ticket.escalate_to_hr = selected_form.cleaned_data['hr']
            ticket.manager = selected_form.cleaned_data['manager']
            ticket.save()
            send_ticket_email(ticket, ticket.assigned_to, f"{submitted_category} Support")
            return redirect('help_desk')

    # Filters from GET (optional)
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')  # YYYY-MM-DD format

    # Tickets raised by user
    tickets = HelpDeskTicket.objects.filter(employee=user).order_by('-created_at')
    if category_filter:
        tickets = tickets.filter(category=category_filter)
    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if date_filter:
        tickets = tickets.filter(created_at__date=date_filter)

    # Determine roles of current user
    user_role_qs = HRContact.objects.filter(employee=user_employee)
    user_roles = set(user_role_qs.values_list('role', flat=True))

    # Tickets assigned to this user as TL and not yet seen by TL
    tl_pending_tickets = HelpDeskTicket.objects.none()
    if 'TL' in user_roles:
        tl_pending_tickets = HelpDeskTicket.objects.filter(
            assigned_to=user,
            viewed_by_tl=False,
            status='open'
        ).order_by('-created_at')

    # Tickets escalated to HR if TL not seen in 2+ hours
    hr_escalated_tickets = HelpDeskTicket.objects.none()
    if 'HR' in user_roles:
        hr_escalated_tickets = HelpDeskTicket.objects.filter(
            escalate_to_hr=user,
            viewed_by_tl=False,
            viewed_by_hr=False,
            status='open',
            created_at__lte=current_time - timedelta(hours=2)
        ).order_by('-created_at')

    # Tickets escalated to Manager if HR not seen in 4+ hours
    manager_escalated_tickets = HelpDeskTicket.objects.none()
    if 'MG' in user_roles:
        manager_escalated_tickets = HelpDeskTicket.objects.filter(
            manager=user,
            viewed_by_hr=False,
            viewed_by_tl=False,
            status='open',
            created_at__lte=current_time - timedelta(hours=4)
        ).order_by('-created_at')

    return render(request, 'help_desk.html', {
        'hr_form': hr_form,
        'it_form': it_form,
        'asset_form': asset_form,
        'tickets': tickets,
        'notifications': notifications,
        'employee': user_employee,
        'tl_pending_tickets': tl_pending_tickets,
        'hr_escalated_tickets': hr_escalated_tickets,
        'manager_escalated_tickets': manager_escalated_tickets,
        'current_time': current_time,
        'team_leader_qs': team_leader_qs,
        'hr_qs': hr_qs,
        'manager_qs': manager_qs,
    })

#---------------------------- Employee Self Service #
@login_required(login_url='/')
def employee_self_service(request):
    employee = get_object_or_404(Employee, employee_id=request.user.employee_id)
    user = request.user  # CustomUser

    if request.method == 'POST':
        if 'personal_submit' in request.POST:
            personal_form = PersonalInfoForm(request.POST, instance=employee)
            professional_form = ProfessionalInfoForm(instance=employee)

            if personal_form.is_valid():
                if personal_form.has_changed():
                    changed_fields = personal_form.changed_data
                    personal_form.save()

                    # 🔹 Sync with CustomUser
                    user.first_name = employee.first_name
                    user.last_name = employee.last_name
                    user.email = personal_form.cleaned_data.get("email", user.email)  # if email is part of the form
                    user.company = employee.company
                    user.save()

                    messages.success(request, "Updated personal info: " + ", ".join(changed_fields))
                else:
                    messages.info(request, "No changes detected in personal information.")

        elif 'professional_submit' in request.POST:
            professional_form = ProfessionalInfoForm(request.POST, instance=employee)
            personal_form = PersonalInfoForm(instance=employee)

            if professional_form.is_valid():
                if professional_form.has_changed():
                    changed_fields = professional_form.changed_data
                    professional_form.save()
                    # (optional: sync any overlapping fields here too)
                    messages.success(request, "Updated professional info: " + ", ".join(changed_fields))
                else:
                    messages.info(request, "No changes detected in professional information.")

    else:
        personal_form = PersonalInfoForm(instance=employee)
        professional_form = ProfessionalInfoForm(instance=employee)

    return render(request, 'employee_self_service.html', {
        'employee': employee,
        'user': request.user,
        'personal_form': personal_form,
        'professional_form': professional_form,
    })

@login_required
def benefits_compensation(request):
    employee = get_object_or_404(EmployeeProfile, user=request.user)
    payrolls = Payroll.objects.filter(employee=employee).order_by('-period_end')
    benefits = Benefit.objects.filter(employee=employee)
   
    context = {
        'payrolls': payrolls,
        'benefits': benefits
    }
   
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'hr/partials/benefits_compensation.html', context)
    return render(request, 'hr/benefits_compensation.html', context)
 

'''@login_required(login_url='/')
def clear_single_notification(request, notification_id):
    Notification.objects.filter(id=notification_id, recipient=request.user).delete()
    messages.success(request, "Notification cleared successfully.")
    return redirect('dashboard')'''

@login_required(login_url='/')
@require_POST
def clear_all_notifications(request):
    Notification.objects.filter(recipient=request.user).delete()
    messages.success(request, "All notifications cleared successfully.")
    return redirect('dashboard')

@login_required
def list_teams(request):
    user = request.user

    # Teams created by the user
    teams_created = Team.objects.filter(created_by=user)

    # Teams user is a member of (excluding ones they created)
    teams_part_of = Team.objects.filter(members=user)

    return render(request, 'list_teams.html', {
        'teams_created': teams_created,
        'teams_part_of': teams_part_of
    })

@login_required
def create_team(request):
    current_user = request.user
    company = current_user.employee.company
    
    # All employees from the same company (excluding current user)
    employees = CustomUser.objects.filter(employee__company=company)

    if request.method == 'POST':
        team_name = request.POST.get('team_name')
        description = request.POST.get('description', '')
        member_ids = request.POST.getlist('members', [])

        if not team_name:
            messages.error(request, 'Team name is required')
            return render(request, 'create_team.html', {
                'employees': employees,
                'team_name': team_name,
                'description': description
            })

        try:
            with transaction.atomic():
                # Create the team
                team = Team.objects.create(
                    name=team_name,
                    description=description,
                    created_by=current_user,
                    company=company
                )

                # Only add explicitly selected members (don't auto-add creator)
                unique_member_ids = list(set(member_ids))  # remove duplicates

                # Fetch CustomUser objects for valid employee members in the same company
                members = CustomUser.objects.filter(
                    id__in=unique_member_ids,
                    employee__company=company
                )

                # Add members to team
                team.members.set(members)

                messages.success(request, f'Team "{team_name}" created successfully!')
                return redirect('list_teams')

        except Exception as e:
            messages.error(request, f'Error creating team: {str(e)}')
            return render(request, 'create_team.html', {
                'employees': employees,
                'team_name': team_name,
                'description': description
            })

    # GET request
    return render(request, 'create_team.html', {
        'employees': employees
    })

@login_required
def edit_team(request, team_id):
    team = get_object_or_404(Team, id=team_id, created_by=request.user)
    employees = CustomUser.objects.filter(employee__company=request.user.employee.company)
    
    if request.method == 'POST':
        team.name = request.POST.get('team_name')
        team.description = request.POST.get('description', '')
        team.save()
        
        # Update members
        selected_members = request.POST.getlist('members')
        team.members.set(selected_members)
        
        messages.success(request, 'Team updated successfully!')
        return redirect('list_teams')
    
    return render(request, 'edit_team.html', {
        'team': team,
        'employees': employees
    })

@login_required
def delete_team(request, team_id):
    team = get_object_or_404(Team, id=team_id, created_by=request.user)
    
    if request.method == 'POST':
        team.delete()
        messages.success(request, 'Team deleted successfully!')
        return redirect('list_teams')
    
    return render(request, 'delete_team.html', {'team': team})

@login_required
def team_detail(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    members = team.members.all()
    return render(request, 'team_detail.html', {
        'team': team,
        'members': members
    })

#------------------------------------------------------------- Training#
# Check if user is HR or Manager
def is_hr_or_manager(user):
    return hasattr(user, 'role') and user.role in ['HR', 'Manager']

# Create training topic
@login_required
@user_passes_test(is_hr_or_manager)
def create_training(request):
    if request.method == 'POST':
        form = TrainingTopicForm(request.POST, request.FILES)
        if form.is_valid():
            training = form.save(commit=False)
            training.created_by = request.user
            training.company = request.user.company  # 🔒 Assign user's company
            training.save()
            return redirect('training')
        else:
            print("Form errors:", form.errors)
    else:
        form = TrainingTopicForm()
    return render(request, 'create_training.html', {'form': form})

# List training topics

@login_required
def training(request):
    search_query = request.GET.get('search', '')

    topics = TrainingTopic.objects.filter(company=request.user.company)

    if search_query:
        topics = topics.filter(
            Q(title__icontains=search_query)
        )

    topics = topics.order_by('-created_at')
    return render(request, 'training.html', {'topics': topics})

# Edit training topic
@login_required
@user_passes_test(is_hr_or_manager)
def edit_training(request, pk):
    training = get_object_or_404(TrainingTopic, pk=pk)

    if training.company != request.user.company:
        return HttpResponseForbidden("You are not allowed to edit this training module.")

    if training.created_by != request.user and request.user.role not in ['HR', 'Manager']:
        return HttpResponseForbidden("You are not allowed to edit this training module.")

    if request.method == 'POST':
        form = TrainingTopicForm(request.POST, request.FILES, instance=training)
        if form.is_valid():
            form.save()
            messages.success(request, "Training topic updated successfully.")  # ✅ success message
            return redirect('training')
    else:
        form = TrainingTopicForm(instance=training)

    return render(request, 'edit_training.html', {'form': form, 'training': training})


# Delete training topic 
@login_required
@user_passes_test(is_hr_or_manager)
def delete_training(request, pk):
    training = get_object_or_404(TrainingTopic, pk=pk)

    if training.company != request.user.company:
        return HttpResponseForbidden("You are not allowed to delete this training module.")

    if training.created_by != request.user and request.user.role not in ['HR', 'Manager']:
        return HttpResponseForbidden("You are not allowed to delete this training module.")

    if request.method == 'POST':
        training.delete()
        return redirect('training')

    return render(request, 'delete_training.html', {'training': training})

#------------------------------------------------------------- Login Logs #

@login_required(login_url='/')
@staff_member_required
def hr_login_logs(request):
    user = request.user
    employee_id_filter = request.GET.get('employee_id')

    try:
        current_employee = Employee.objects.get(employee_id=user.employee_id)
        company = current_employee.company
    except Employee.DoesNotExist:
        company = None

    # Default to empty if no company found
    login_logs = LoginLog.objects.none()

    if company:
        login_logs = LoginLog.objects.select_related('user__company') \
            .filter(user__company=company) \
            .order_by('-login_time')

        # Optional filter by employee ID (if you want to filter)
        if employee_id_filter:
            login_logs = login_logs.filter(user__employee__employee_id=employee_id_filter)

    notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).order_by('-created_at')

    return render(request, 'login_logs.html', {
        'login_logs': login_logs,
        'employee': current_employee if company else None,
        'today': timezone.now(),
        'employee_id_filter': employee_id_filter,
    })


#------------------------------------------------------------- Resignation Request #
import base64
from django.core.files.base import ContentFile

@login_required
def resignation_request_view(request):
    user = request.user
    user_requests = ResignationRequest.objects.filter(employee=user).order_by('-submitted_at')

    if request.method == 'POST':
        # ✅ Check the last resignation request status
        last_request = user_requests.first()
        if last_request and last_request.status in ['pending', 'accepted']:
            messages.error(request, "You cannot submit a new resignation request until your previous one is rejected.")
            return redirect('resignation_request')

        resignation_date = request.POST.get('resignation_date')
        last_working_day = request.POST.get('last_working_day')
        resignation_reason = request.POST.get('resignation_reason')
        other_reason = request.POST.get('other_reason', '')
        notes = request.POST.get('notes', '')
        signature_data = request.POST.get('signature_data', '')
        agreement = request.POST.get('agreement') == 'on'
        letter_file = request.FILES.get('resignation_letter')

        if not agreement:
            messages.error(request, "You must accept the agreement to submit.")
            return redirect('resignation_request')

        if not (resignation_date and last_working_day and resignation_reason and signature_data):
            messages.error(request, "Please fill all required fields before submitting.")
            return redirect('resignation_request')

        # ✅ Create new resignation request
        resignation = ResignationRequest(
            employee=user,
            resignation_date=resignation_date,
            last_working_day=last_working_day,
            resignation_reason=resignation_reason,
            other_reason=other_reason,
            notes=notes,
            signature_data=signature_data,
            agreement=agreement,
            status='pending',
            submitted_at=timezone.now()
        )

        if letter_file:
            resignation.resignation_letter = letter_file

        resignation.save()

        # ✅ Notify employee
        Notification.objects.create(
            recipient=user,
            message=(
                f"Your resignation request dated {resignation.resignation_date} "
                f"with last working day {resignation.last_working_day} has been submitted successfully."
            )
        )

        # ✅ Notify HR and Managers
        from django.contrib.auth import get_user_model
        User = get_user_model()
        hr_managers = User.objects.filter(role__in=['HR', 'Manager'], is_active=True, company=user.company)
        notification_text = (
            f"{user.get_full_name() or user.username} submitted a resignation request effective {resignation.last_working_day}."
        )
        for hrm in hr_managers:
            Notification.objects.create(
                recipient=hrm,
                message=notification_text
            )

        messages.success(request, "Resignation letter submitted successfully.")
        return redirect('resignation_request')

    return render(request, 'resignation.html', {'requests': user_requests})

@login_required(login_url='/')
@staff_member_required
def review_resignation_request(request, resignation_id, action):
    resignation = get_object_or_404(ResignationRequest, id=resignation_id)

    action_lower = action.lower()

    if action_lower == 'approve':
        resignation.status = 'Approved'
        resignation.save()
        Notification.objects.create(
            recipient=resignation.employee,
            message=(
                f"Your resignation submitted on {resignation.submitted_at.strftime('%Y-%m-%d')} "
                f"has been approved."
            )
        )
        messages.success(request, "Resignation approved successfully.")

    elif action_lower == 'reject':
        resignation.status = 'Rejected'
        resignation.save()
        Notification.objects.create(
            recipient=resignation.employee,
            message=(
                f"Your resignation submitted on {resignation.submitted_at.strftime('%Y-%m-%d')} "
                f"has been rejected."
            )
        )
        messages.success(request, "Resignation rejected successfully.")

    else:
        messages.error(request, "Invalid action specified.")

    return redirect('staff_notifications')  # Redirect to a suitable page after action


#------------------------------------------------------------- Career development #
@login_required(login_url='/')
def career_development(request):
    categories = SkillCategory.objects.all()
    resources = CareerResource.objects.filter(company=request.user.company)
    can_edit = request.user.role in ['HR', 'Manager']
 
    resource_form = CareerResourceForm()
    category_form = SkillCategoryForm()
 
    if request.method == 'POST' and can_edit:
        if 'add_resource' in request.POST:
            resource_form = CareerResourceForm(request.POST, request.FILES)
            if resource_form.is_valid():
                resource = resource_form.save(commit=False)
                resource.company = request.user.company
                resource.save()
                return redirect('career_development')

 
        elif 'add_category' in request.POST:
            category_form = SkillCategoryForm(request.POST)
            if category_form.is_valid():
                category_form.save()
                return redirect('career_development')
 
    return render(request, 'career_development.html', {
        'categories': categories,
        'resources': resources,
        'form': resource_form,
        'category_form': category_form,
        'can_edit': can_edit,
    })
 
 
@login_required
def delete_category(request, id):
    if request.user.role not in ['HR', 'Manager']:
        return redirect('career_development')
   
    category = get_object_or_404(SkillCategory, id=id)
    if not category.careerresource_set.exists():  
        category.delete()
    return redirect('career_development')
 
 
@login_required
def delete_resource(request, slug):
    if request.user.role not in ['HR', 'Manager']:
        return redirect('career_development')
 
    resource = get_object_or_404(CareerResource, slug=slug)
    resource.delete()
    return redirect('career_development')
 
 
 
def resource_detail(request, slug):
    resource = get_object_or_404(CareerResource, slug=slug)
    return render(request, 'resource_detail.html', {'resource': resource})


@login_required
def edit_resource(request, slug):
    if request.user.role not in ['HR', 'Manager']:
        return redirect('career_development')

    resource = get_object_or_404(CareerResource, slug=slug)

    if request.method == 'POST':
        form = CareerResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            return redirect('career_development')
    else:
        form = CareerResourceForm(instance=resource)

    return render(request, 'edit_resource.html', {
        'form': form,
        'resource': resource
    })

@login_required
def manage_logo(request):
    company = request.user.company  # ✅ Get logged-in user’s company
    if not company:
        return render(request, "no_company.html")  # If user not assigned to any company

    if request.method == "POST":
        form = CompanyLogoForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            return redirect("manage_logo")  # Refresh after saving
    else:
        form = CompanyLogoForm(instance=company)

    return render(request, "manage_logo.html", {"form": form, "company": company})
# views.py
@login_required
def delete_logo(request):
    company = request.user.company
    if company and company.logo:
        company.logo.delete(save=True)  # Delete from storage and DB
    return redirect("manage_logo")
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, CharField, Value
from django.db.models.functions import Concat
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import CustomUser, Message

@login_required
def chat_view(request):
    return render(request, "etalks.html")

@login_required
def users_list(request):
    company = request.user.company
    users = CustomUser.objects.filter(company=company).exclude(id=request.user.id)
    results = [
        {"id": u.id, "employee_id": u.employee_id,
         "name": f"{u.first_name} {u.last_name}".strip(),
         "email": u.email}
        for u in users
    ]
    return JsonResponse({"results": results})

@login_required
def search_users(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        company = request.user.company
        users = CustomUser.objects.filter(company=company).exclude(id=request.user.id)
        users = users.annotate(
            full_name=Concat("first_name", Value(" "), "last_name", output_field=CharField())
        ).filter(
            Q(full_name__icontains=query)
            | Q(employee_id__icontains=query)
            | Q(email__icontains=query)
        )[:10]
        results = [{"id": u.id, "employee_id": u.employee_id,
                    "name": u.full_name, "email": u.email} for u in users]
    return JsonResponse({"results": results})

@login_required
def recent_chats(request):
    user = request.user
    messages = Message.objects.filter(Q(sender=user) | Q(receiver=user)).order_by("-timestamp")
    seen = set()
    results = []
    for msg in messages:
        other = msg.receiver if msg.sender == user else msg.sender
        if other.id in seen:
            continue
        seen.add(other.id)
        unread_count = Message.objects.filter(sender=other, receiver=user, is_read=False).count()
        results.append({
            "id": other.id,
            "name": f"{other.first_name} {other.last_name}".strip(),
            "employee_id": other.employee_id,
            "email": other.email,
            "last_message": msg.content,
            "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M"),
            "unread": unread_count,
        })
    return JsonResponse({"results": results})
@login_required
def get_messages(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) | Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')

    data = [{"sender": m.sender.username, "message": m.content, "timestamp": m.timestamp} for m in messages]
    return JsonResponse(data, safe=False)

@csrf_exempt
@login_required
def send_message(request, user_id):
    if request.method == "POST":
        user = request.user
        other = CustomUser.objects.get(id=user_id)
        message_text = request.POST.get("message")
        msg = Message.objects.create(sender=user, receiver=other, content=message_text, timestamp=timezone.now())
        return JsonResponse({
            "id": msg.id,
            "sender": msg.sender.id,
            "receiver": msg.receiver.id,
            "message": msg.content,
            "timestamp": msg.timestamp.strftime("%H:%M"),
        })


@login_required
def call_history(request):
    """Return call history of logged-in user."""
    calls = Call.objects.filter(Q(caller=request.user) | Q(receiver=request.user))

    data = []
    for c in calls:
        data.append({
            "caller": c.caller.username,
            "receiver": c.receiver.username,
            "type": c.call_type,
            "status": c.status,
            "started": c.started_at,
        })

    return JsonResponse(data, safe=False)