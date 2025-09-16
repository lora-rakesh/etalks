from app import views
from django.urls import path
from django.contrib.auth import views as auth_views

urlpatterns = [

    #  Welcome url #
    path('',views.indexview,name='index'),
    path('login/',views.loginview,name='login'),
    path('company_check/', views.company_check, name='company_check'),
    path('autocomplete/', views.company_autocomplete, name='company_autocomplete'),
    path('company/<int:company_id>/', views.company_detail, name='company_detail'),
    path('base', views.base, name='base'),
    path('chat_bot', views.chat_bot, name='chat_bot'),
    path('training', views.training, name='training'),
    path('login_logs', views.hr_login_logs, name='hr_login_logs'),
    path('request_sent/', views.request_sent, name='request_sent'),
    path("unlock_requests/", views.unlock_requests_view, name="unlock_requests"),
    path("unlock_user/<int:request_id>/", views.unlock_user, name="unlock_user"),
    path('send-unlock-request/<int:user_id>/', views.send_unlock_request, name='send_unlock_request'),

   

    #  Login/Logout url #
    path('login', views.loginview, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path("etalks/", views.chat_view, name="chat_view"),
    path("users/", views.users_list, name="users_list"),
    path("search-users/", views.search_users, name="search_users"),
    path("call-history/", views.call_history, name="call_history"),
    path("recent-chats/", views.recent_chats, name="recent_chats"),
    path('messages/<int:user_id>/', views.get_messages, name='get_messages'),
    path("send-message/", views.send_message, name="send_message"),

    #  Dashboard #
    path('dashboard', views.dashboard, name='dashboard'),
    path('search/', views.search_results, name='search_results'),
    path('faq', views.faq, name='faq'),
    path('contact_us', views.contact_us, name='contact_us'),
    path('employee_requests/', views.employee_requests, name='employee_requests'),
    path('staff_notifications/', views.staff_notifications, name='staff_notifications'),
    path('profile/', views.profile, name='profile'),  
    path('edit_profile_picture/', views.edit_profile_picture, name='edit_profile_picture'),
    path('edit_cover_picture/', views.edit_cover_picture, name='edit_cover_picture'),
    



    #  Muster #
    path('muster',views.muster,name='muster'),
    path('muster_status',views.muster_status,name='muster_status'),
    path('review_muster/<int:muster_id>/<str:action>/', views.review_muster, name='review_muster'),
    path('clock_in', views.clock_in, name='clock_in'),
    path('clock_out', views.clock_out, name='clock_out'),
    path('holidays',views.holidays,name='holidays'),
    


    #  Leaves #
    path('leave_balance', views.leave_balance, name='leave_balance'),
    path('leave_request', views.leave_request, name='leave_request'),
    

    #  Verify OTP #
    path("reset_password", views.reset_password, name="reset_password"),
    path("reset_password_with_otp", views.reset_password_with_otp, name="reset_password_with_otp"),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    

    #  Profile #
#   path('profile', views.profile_view, name='profile'),
    path('edit_personal_info/<int:employee_id>', views.edit_personal_info, name='edit_personal_info'),
    path('edit_professional_info/<int:employee_id>', views.edit_professional_info, name='edit_professional_info'),
    path('edit_banking_info/<int:employee_id>', views.edit_banking_info, name='edit_banking_info'),
    path('upload_employee_media/', views.upload_employee_media, name='upload_employee_media'),


    #  Task #
    path('task_management/', views.task_management, name='task_management'),
    path('assign_task/', views.assign_task, name='assign_task'),
    path('mark-task-complete/<int:task_id>/', views.mark_task_complete, name='mark_task_complete'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('tasks-by-date/', views.tasks_by_date, name='tasks_by_date'),
    


    #  Salaries #
    path('salary_details/', views.salary_details, name='salary_details'),
    path('generate_payslip_pdf/<int:employee_id>/', views.generate_payslip_pdf, name='generate_payslip_pdf'),


    #  Financial #
    path('expense_claims', views.expense_claims, name='expense_claims'),
    path('submit_expense_claim', views.submit_expense_claim, name='submit_expense_claim'),
    path('tax_deduction', views.tax_deduction, name='tax_deduction'),
    path('loan_requests', views.loan_requests, name='loan_requests'),
    path('submit_loan_request', views.submit_loan_request, name='submit_loan_request'),


    #  Review's  #
    path('review/muster/', views.review_muster, name='review_muster'),
    path('review/leave/', views.review_leave, name='review_leave'),
    path('review/expense/', views.review_expense, name='review_expense'),
    path('review/loan/', views.review_loan, name='review_loan'),


    #  Review's notifications #
    path('review_muster_notifications/<int:muster_id>/<str:action>/', views.review_muster_notifications, name='review_muster_notifications'),
    path('review_leaves_notifications/<int:leaves_id>/<str:action>/', views.review_leaves_notifications, name='review_leaves_notifications'),
    path('review_expense_notifications/<int:expense_id>/<str:action>/', views.review_expense_notifications, name='review_expense_notifications'),
    path('review_loan_notifications/<int:loan_id>/<str:action>/', views.review_loan_notifications, name='review_loan_notifications'),


    #  User data for Staff #
    path('user_list/', views.user_list, name='user_list'),
    path('user_create/', views.user_create, name='user_create'),
    path('user_edit/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('user_confirm_delete/<int:pk>/', views.user_confirm_delete, name='user_confirm_delete'),


    #  Policies #
    path("policy", views.policy, name="policy"),
    path("data_retention_policy", views.data_retention_policy, name="data_retention_policy"),
    path("acceptable_use_policy", views.acceptable_use_policy, name="acceptable_use_policy"),
    path("cookie_policy", views.cookie_policy, name="cookie_policy"),
    path("refund_cancellation_policy", views.refund_cancellation_policy, name="refund_cancellation_policy"),
    path("terms_of_service", views.terms_of_service, name="terms_of_service"),


    #  Salary data for Staff #
    path('create_salary/', views.create_salary, name='create_salary'),
    path('view_salary/<int:salary_id>/', views.view_salary, name='view_salary'),
    path('edit_salary/<int:salary_id>/', views.edit_salary, name='edit_salary'),
    path('delete_salary/<int:salary_id>/', views.delete_salary, name='delete_salary'),
    path('salary_list', views.salary_list, name='salary_list'),


    #  Performance #
   # path('performance-entry/', views.performance_entry, name='performance_entry'),
    #path('performance-page/', views.performance_page, name='performance_page'),
    
    #path('api/submit-performance/', views.submit_performance, name='submit_performance'),
   # path('api/top-daily-performers/', views.top_daily_performers, name='top_daily_performers'),    
   # path('api/best-employee-month/', views.best_monthly_performer, name='best_monthly_performer'),


    #  Company for Staff #
    path('company_list', views.company_list, name='company_list'),
    path('company_create', views.company_create, name='company_create'),
    path('company_edit/<int:pk>', views.company_edit, name='company_edit'),
    path('company_delete/<int:pk>', views.company_delete, name='company_delete'),

    path('working_days/', views.working_days, name='working_days'),

    path('task_list', views.task_list, name='task_list'),

    #path('performance_list', views.performance_list, name='performance_list'),


    #  Employee for Staff #
    path('employee_list', views.employee_list, name='employee_list'),
    path('employee_create', views.employee_create, name='employee_create'),
    path('employee_edit/<int:pk>', views.employee_edit, name='employee_edit'),
    path('employee_delete/<int:pk>', views.employee_delete, name='employee_delete'),


    #  Holidays for Staff #
    path('holidays_list', views.holidays_list, name='holidays_list'),
    path('holiday_create', views.holiday_create, name='holiday_create'),
    path('holiday_view/<int:pk>', views.holiday_view, name='holiday_view'),
    path('holiday_edit/<int:pk>', views.holiday_edit, name='holiday_edit'),
    path('holiday_delete/<int:pk>', views.holiday_delete, name='holiday_delete'),


    #  Leave for Staff #
    path('leave_list', views.leave_list, name='leave_list'),
    path('leave_create', views.leave_create, name='leave_create'),
    path('leave_detail/<int:pk>', views.leave_detail, name='leave_detail'),
    path('leave_edit/<int:pk>', views.leave_edit, name='leave_edit'),
    path('leave_delete/<int:pk>', views.leave_delete, name='leave_delete'),


    #  HR4U #
    path('HR4U/', views.hr4u_dashboard, name='hr_dashboard'),
    path('resignation/', views.resignation_request_view, name='resignation_request'),
    path('review_resignation_request/<int:resignation_id>/<str:action>/',views.review_resignation_request,name='review_resignation_request'),
    path('hr_services/', views.hr_services_page, name='hr_services'),
    path('hr_services/edit/<int:pk>/', views.edit_hr_contact, name='edit_hr_contact'),
    path('hr_services/delete/<int:pk>/', views.delete_hr_contact, name='delete_hr_contact'),
    path('employee_self_service/', views.employee_self_service, name='employee_self_service'),
    path('benefits_compensation', views.benefits_compensation, name='benefits_compensation'),
    path('career_development', views.career_development, name='career_development'),
    path('career_development/edit/<slug:slug>/', views.edit_resource, name='edit_resource'),
    path('help_desk', views.help_desk_page, name='help_desk'),
    path('career_development', views.career_development, name='career_development'),
    path('delete_resource/<slug:slug>/', views.delete_resource, name='delete_resource'),
    path('delete_category/<int:id>/', views.delete_category, name='delete_category'),
    path('resource/<slug:slug>/', views.resource_detail, name='resource_detail'),
    # clear notifications
    path('clear-all-notifications/', views.clear_all_notifications, name='clear_all_notifications'),
    # path('clear_single_notification/<int:notification_id>', views.clear_single_notification, name='clear_single_notification'),
   #  Team Management 
    path('teams/', views.list_teams, name='list_teams'),
    path('teams/create/', views.create_team, name='create_team'),
    path('teams/<int:team_id>/edit/', views.edit_team, name='edit_team'),
    path('teams/<int:team_id>/delete/', views.delete_team, name='delete_team'),
    path('team/<int:team_id>/', views.team_detail, name='team_detail'),

    
    #  Training #
    path('training/', views.training, name='training'),
    path('training/create/', views.create_training, name='create_training_topic'),
    path('training/<int:pk>/edit/', views.edit_training, name='edit_training'),
    path('training/<int:pk>/delete/', views.delete_training, name='delete_training'),
    
    path('clear-tips/', views.clear_tips, name='clear_tips'),
    path('manage_logo/', views.manage_logo, name='manage_logo'),
   
    path('delete-logo/', views.delete_logo, name='delete_logo'),
]
