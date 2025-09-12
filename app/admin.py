from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from app.models import *
from app.forms import *

# Register your models here.

admin.site.register(Company_check)
admin.site.register(Muster)
admin.site.register(Team)
# app/admin.py

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
#admin.site.register(Performance)
admin.site.register(HelpDeskTicket)

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    add_form = UserCreationForm # create if not existing, else use default

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
            'fields': (
                'employee_id', 'email', 'first_name', 'last_name',
                'role', 'company', 'password',  # recommended password confirmation fields
            )
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')



admin.site.register(CustomUser, CustomUserAdmin)

from django.contrib import admin
from .models import Employee, EmployeeMedia

class EmployeeMediaInline(admin.StackedInline):
    model = EmployeeMedia
    extra = 0

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    inlines = [EmployeeMediaInline]


admin.site.register(EmployeeMedia)


#------------------------------------------------------------- Training #
from .models import TrainingTopic

@admin.register(TrainingTopic)
class TrainingTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'company', 'created_at')
    search_fields = ('title', 'description', 'created_by__username')
    list_filter = ('company', 'created_at')
    readonly_fields = ('created_by', 'company', 'created_at')
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only set created_by and company on creation
            obj.created_by = request.user
            obj.company = request.user.company
        super().save_model(request, obj, form, change)


from django.contrib import admin
from .models import ResignationRequest

class ResignationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'employee',
        'resignation_date',
        'last_working_day',
        'status',
        'submitted_at',
    )
    list_filter = ('status', 'resignation_date', 'last_working_day')
    search_fields = (
        'employee__username',
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
        'resignation_reason',
        'other_reason',
        'notes',
    )
    date_hierarchy = 'resignation_date'
    readonly_fields = (
        'submitted_at',
        'signature_data',
    )

admin.site.register(ResignationRequest, ResignationRequestAdmin)
 
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



from django.contrib import admin
from .models import Message, CallLog


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "room", "sender", "receiver", "short_text", "created_at")
    list_filter = ("room", "created_at")
    search_fields = ("text", "sender__username", "receiver__username")
    ordering = ("-created_at",)

    def short_text(self, obj):
        return obj.text[:50] + ("..." if len(obj.text) > 50 else "")
    short_text.short_description = "Message"


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "caller",
        "callee",
        "call_type",
        "status",
        "started_at",
        "ended_at",
    )
    list_filter = ("call_type", "status", "started_at")
    search_fields = ("caller__username", "callee__username")
    ordering = ("-started_at",)
