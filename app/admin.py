from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

# -------------------------------
# Basic Models
# -------------------------------
admin.site.register(Company_check)
admin.site.register(Muster)
admin.site.register(Team)
admin.site.register(LoginLog)
admin.site.register(LoggedInUser)
admin.site.register(HRContact)
admin.site.register(FAQ)
admin.site.register(Salary)
admin.site.register(TimeEntry)
admin.site.register(Notification)
admin.site.register(Task)
admin.site.register(Leave)
admin.site.register(LeaveRequest)
admin.site.register(ExpenseClaim)
admin.site.register(LoanRequest)
admin.site.register(Holiday)
admin.site.register(HelpDeskTicket)

# -------------------------------
# CustomUser Admin
# -------------------------------
from .forms import UserCreationForm  # ensure you have this form

class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm
    list_display = (
        'employee_id', 'email', 'first_name', 'last_name',
        'role', 'company', 'is_superuser', 'is_staff', 'is_active'
    )
    ordering = ('employee_id',)
    fieldsets = (
        (None, {
            'fields': (
                'employee_id', 'email', 'password', 'first_name', 'last_name',
                'role', 'company', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'
            )
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('employee_id', 'email', 'first_name', 'last_name', 'role', 'company', 'password'),
        }),
    )
    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(CustomUser, CustomUserAdmin)

# -------------------------------
# Employee Admin
# -------------------------------
class EmployeeMediaInline(admin.StackedInline):
    model = EmployeeMedia
    extra = 0

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    inlines = [EmployeeMediaInline]

admin.site.register(EmployeeMedia)

# -------------------------------
# TrainingTopic Admin
# -------------------------------
@admin.register(TrainingTopic)
class TrainingTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'company', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    list_filter = ('company', 'created_at')
    readonly_fields = ('created_by', 'company', 'created_at')
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
            obj.company = request.user.company
        super().save_model(request, obj, form, change)

# -------------------------------
# ResignationRequest Admin
# -------------------------------
@admin.register(ResignationRequest)
class ResignationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'resignation_date', 'last_working_day', 'status', 'submitted_at')
    list_filter = ('status', 'resignation_date', 'last_working_day')
    search_fields = ('employee__username', 'employee__employee_id', 'employee__first_name', 'employee__last_name', 'resignation_reason', 'other_reason', 'notes')
    date_hierarchy = 'resignation_date'
    readonly_fields = ('submitted_at', 'signature_data')

# -------------------------------
# SkillCategory & CareerResource
# -------------------------------
@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(CareerResource)
class CareerResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'company']
    search_fields = ['title', 'description']
    list_filter = ['category', 'company']
    prepopulated_fields = {'slug': ('title',)}

# -------------------------------
# Message & RecentChat
# -------------------------------
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'receiver', 'content', 'timestamp')
    search_fields = ('sender__username', 'receiver__username', 'content')
    list_filter = ('timestamp',)
    readonly_fields = ('timestamp',)

@admin.register(RecentChat)
class RecentChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'other_user', 'last_message', 'updated_at')
    search_fields = ('user__username', 'other_user__username', 'last_message')
    list_filter = ('updated_at',)
    readonly_fields = ('updated_at',)
