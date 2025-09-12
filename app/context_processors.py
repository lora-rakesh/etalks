# from .models import Muster, LeaveRequest, ExpenseClaim, LoanRequest

# def pending_requests(request):
#     if request.user.role == 'HR' or request.user.role == 'Manager' or request.user.is_superuser:
#         pending_musters = Muster.objects.filter(status='Pending')
#         pending_leave_requests = LeaveRequest.objects.filter(status='pending')
#         pending_expenses = ExpenseClaim.objects.filter(status='pending')
#         pending_loans = LoanRequest.objects.filter(status='pending')
#     else:
#         pending_musters = pending_leave_requests = pending_expenses = pending_loans = None
    
#     return {
#         'pending_musters': pending_musters,
#         'pending_leave_requests': pending_leave_requests,
#         'pending_expenses': pending_expenses,
#         'pending_loans': pending_loans,
#     }

# context_processors.py
from .models import Muster, LeaveRequest, ExpenseClaim, LoanRequest, ResignationRequest

def common_data(request):
    pending_musters = Muster.objects.filter(status='Pending')
    pending_leave_request = LeaveRequest.objects.filter(status='pending')
    pending_expense = ExpenseClaim.objects.filter(status='pending')
    pending_loan = LoanRequest.objects.filter(status='pending')
    pending_resignations = ResignationRequest.objects.filter(status='pending')  # Assuming you might want to add this later

    return {
        'pending_musters': pending_musters,
        'pending_leave_request': pending_leave_request,
        'pending_expense': pending_expense,
        'pending_loan': pending_loan,
        'pending_resignations': pending_resignations
    }
from .models import Notification

def notifications_count(request):
    if request.user.is_authenticated:
        return {
            'notifications': Notification.objects.filter(recipient=request.user, is_read=False)
        }
    return {'notifications': []}
