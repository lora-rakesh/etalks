# aihr4u
LORAHRMS
# HR4U - Human Resource Management System
A full-featured HRMS (Human Resource Management System) built using Django and Django REST Framework (DRF). This system manages key HR operations including employee onboarding, attendance tracking, payroll, task assignment, and internal notifications — providing an all-in-one platform for efficient human resource management.

## Features
- ✅ Role-based login system (Admin, HR, Manager, Employee)
- ✅ Employee CRUD operations
- ✅ Attendance (Muster) tracking
- ✅ Leave and loan requests
- ✅ Expense claims
- ✅ Task assignment
- ✅ Notification system
- ✅ Salary management
- ✅ File uploads with validation
- ✅ Excel/PDF export
- ✅ Real-time updates using WebSocket
- ✅ API integration with JWT authentication
- ✅ 404 & error pages
- ✅ Admin dashboard and employee dashboard

## Tech Stack
- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL      
- **Task Queue**: Celery with Redis             
- **Real-time Features**: WebSocket / socket.io          
- **Performance & Security**: Rate Limiting and Caching

## Installation and Setup Instructions
1. **Create Project Directory**
   ```bash
   mkdir HR4U
   cd HR4U
2. **Set Up a Virtual Environment**
   ```bash
   python -m venv env
   env\Scripts\activate  # On Windows
3. **Install all project dependencies**
   ```bash
   pip install \
   django \
   djangorestframework \
   djangorestframework-simplejwt \
   psycopg2-binary \
   python-decouple \
   python-dotenv \
   dj-database-url \
   celery \
   redis \
   channels \
   whitenoise \
   geoip2 \
   openpyxl \
   requests
4. **Create Django Project and App**
   ```bash
   django-admin startproject project
   cd project
   python manage.py startapp app
5. **Make changes in settings.py**
   - Add 'app', to the INSTALLED_APPS list.
   - Add 'rest_framework', 'rest_framework_simplejwt', 'crispy_forms', and 'crispy_bootstrap4' as well.
   - Configure Database in settings.py ( Used default Database)
6. **Apply Migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
7. **Final Setup and Run**
   ```bash
   python manage.py createsuperuser  # Create Superuser for admin panel
   python manage.py runserver   # Run the Development Server
   pip freeze > requirements.txt  # Create Requirements File

8. **Folder Structure**
   ```bash
   HR4U/
   ├── project/                      # Main Django project (settings and configuration)
   │   ├── __init__.py
   │   ├── settings.py               # Global settings
   │   ├── urls.py                   # Root URL configuration
   │   ├── wsgi.py                   # WSGI entry-point for deployment
   │   └── asgi.py                   # ASGI entry-point for async support
   │
   ├── app/                          # Core Django app (business logic)
   ├── __init__.py
   │   ├── admin.py                  # Admin panel configuration
   │   ├── apps.py
   │   ├── models.py                 # Models: User, Property, Booking, etc.
   │   ├── serializers.py            # Data validation & transformation
   │   ├── urls.py                   # App-level routing
   │   ├── utils.py                  # Utility functions (OTP, helper logic)
   │   └── views.py                  # Business logic & API views
   │
   ├── templates/                    # HTML templates
   │   ├── base.html
   │   ├── login.html
   │   ├── dashboard.html
   │   └── ...                       # Other HTML pages
   │
   ├── static/                       # CSS, JS, images
   │   └── ...
   │
   ├── media/                        # Uploaded files (images, PDFs, etc.)
   │
   ├── migrations/                   # Django model migrations
   │
   ├── .env                          # Environment variables (not committed)
   ├── .gitignore                    # Files/folders to exclude from Git
   ├── manage.py                     # Django management utility
   ├── requirements.txt              # Python dependencies
   └── README.md                     # Project documentation

## Development Workflow
**Create templates**
- This Django project includes the following templates located in the templates
1. **Core Pages:**
- 404.html – Custom 404 error page
- base.html – Base layout used by other templates
- index.html – Home or landing page
- login.html – User login page
- dashboard.html – User dashboard view
2. **Employee Management:**
- employee_create.html, employee_edit.html, employee_delete.html, employee_form.html, employee_list.html, employee_detail.html, view_employee.html
3. **Leave & Holiday Management:**
- leave_create.html, leave_edit.html, leave_list.html, leave_detail.html, leave_balance.html
- holiday_create.html, holiday_edit.html, holidays_list.html, holiday_view.html, holidays.html
4. **Performance & Salary:**
- performance_entry.html, performance_list.html, performance_page.html
- salary_details.html, salary_list.html, create_salary.html, edit_salary.html
- review_muster.html, muster_status.html, muster.html, working_days.html
5. **Forms & Policies:**
- company_form.html, company_create.html, company_edit.html, company_list.html, company_delete.html
- acceptable_use_policy.html, refund_cancellation_policy.html, cookie_policy.html, terms_of_service.html, policy.html, data_retention_policy.html
6. **User & Auth:**
- reset_password.html, reset_password_with_otp.html, forgot_password.html, verify_otp.html, user_form.html, user_list.html, user_confirm_delete.html
7. **User Features**
- faq.html, contact_us.html, chat_bot.html, profile.html, loan_requests.html, tax_deduction.html, task_list.html, task_management.html, staff_notifications.html, training.html, all_payslips.html, view_salary.html, expense_claims.html  
## Implementation
1. Define Models
Describe data structures for each feature (Employee, Leave, Salary, etc.).
2. Create Forms
Build Django forms (ModelForm) to handle user input for models.
3. Implement Views
Write function-based or class-based views to process data and render templates.
4. Set Up URLs
Map views to URLs in both app-level and project-level urls.py.
5. Connect Everything
Integrate models, views, forms, URLs, and templates to make features functional.



# HR4U - Human Resource Management System (v2.0) 
HR4U (AIHR4U LORAHRMS) is a full-featured Human Resource Management System (HRMS) built with Django and Django REST Framework (DRF).

- The Version 1 supported single-company use.
- With Version 2, HR4U now introduces Multi-Company (Multi-Tenant) Support, enhanced HR Contact modules, and improved security and compliance features — making it scalable for organizations of all sizes.

## New in Version 2.0
🏢 Multi-Company (Tenant-Aware) Authentication
HR4U v2.0 introduces a multi-company login system, allowing multiple organizations to use the platform securely under a single deployment.

## Login Flow

- **Company Selection**
   - Users must enter their company name (e.g., LoRa, Tech Solutions). The system matches company names in a case-sensitive manner. Auto-suggestions are available (typing L suggests LoRa, T suggests Tech Solutions).
- **Company Verification**
   - If the company name does not exist, access is denied with Error: Company not found
- **Employee Authentication (Per Company)**
   - Once the company is verified, the system prompts for Employee ID and Password.
- **Validation rules:**
   - If an invalid Employee ID is entered → Error: User not found
   - If an incorrect password is entered → Error: Incorrect Password
   - If a valid Employee ID & Password are entered but belong to another company → Error: You are unauthorized to access this company.
- **Successful Login:**
   - If the company, employee ID, and password are all correct, the user is granted role-based access (Admin / HR / Manager / Employee) within their company’s HRMS environment.

## Additional Security & Session Management Features 
- **Auto Logout on Inactivity:** Users are automatically logged out after 5 minutes of inactivity to enhance security and prevent unauthorized access on unattended devices.

- **Single Device & Browser Login Restriction:** Users cannot log in simultaneously on multiple sessions from the same device or browser, reducing risks of session sharing and unauthorized concurrent access.

- **Login History & Activity Tracking:** A dedicated Login History page tracks and displays employee login activity including:
  - Employee Name & ID
  - IP Address
  - Device Information
  - Login Timestamps: This enables auditing of login events and monitoring for unusual activity.
  - Session Timeout Implementation: Utilizes session expiry settings and middleware logic to monitor user activity time, automatically invalidating sessions after the idle timeout period.
- **Login History Auto-Cleanup**
  - Retention Rule: Login history records are auto-deleted every 18 hours.
  - Deduplication: If a user logs in multiple times on same device within a day → stored only once. If logged in from different devices within a day → each unique device is recorded
- **Account Lock & Unlock**  
  - Accounts are locked after 5 failed password attempts for the same Employee ID.  
  - Locked users see the message: “Contact your HR to Unlock.”  
  - An email notification is sent to all HRs, and any HR can approve the unlock via a one-click link.  
  - Once approved, the account enters a 15-minute cooldown period before it is automatically unlocked.  
  - During cooldown, login attempts remain blocked even with the correct password.
  - After HR approves the unlock, the user receives an email notification confirming: "Your account has been unlocked.

## Security Upgrades

- **Sensitive Data Encryption with Cryptography:**
  - HR4U v2.0 uses the Python cryptography library to encrypt sensitive employee fields such as:
   1. UAN Number
   2. PAN Number
   3. Aadhaar Number
   4. Bank Account Number

- **Implementation**
  - These fields are encrypted at rest in the database using field-level encryption via the django-cryptography package. Encryption keys are securely managed via environment variables. The encryption mechanism uses strong symmetric encryption algorithms (AES-256) ensuring confidentiality even if the database is compromised.

- **Installation**
  - Install the cryptography package with pip before running the project: 
  
  ```bash
  pip install cryptography

## Profile & Cover Picture Enhancements
   - Resolved issues related to profile picture uploads and display to ensure consistent user experience.
   - Introduced the EmployeeMedia model to manage profile and cover images efficiently.
   - New users receive default profile and cover pictures set to the AIHR4U logos, which can be updated by users anytime.
   - Improved media handling and storage ensuring reliable image upload, retrieval, and display across the platform.

## New Pages and Features Added

 **Extended HR4U Modules:**
- Resignation Request: Employees can submit resignations; only one active request is allowed. New submission permitted only if the previous one is rejected.
- Employee Self Service: Employees can view/update their Personal Info, Professional Details, and Banking/Financial Details securely.
- HR Contacts: HRs and Managers can manage HR contact details, accessible only with proper role permissions.
- Career Development: Provides a Career Hub for employees with skill categories, resources, and training materials; HR/Managers can add/edit resources.
- Help Desk: Multi-department ticket system for HR, IT, and Asset issues with escalation to Team Leaders, HR, and Managers, plus full ticket tracking.

 **Task Management Module:**
- Assign Tasks: HR and Managers can assign tasks to individual employees (via email/ID) or entire teams. Includes task details like start date, due date, and description.
- My Tasks: Employees can view their assigned tasks with status tracking and calendar views for deadlines and scheduling.
- Task Filtering: Supports filtering tasks by employee ID and month for easier task management oversight.
- Team Management: Provides interfaces to manage teams for bulk task assignment.
- Detailed Task Tracking: View task status (Pending/Completed), assignment dates, and assignees via a clear tabular dashboard.
- Interactive UI: Modals and alerts included for smooth task detail viewing and confirmations.

 **Training:**  Introduced a Training module to manage and access training resources.  
- HR and Managers can add, edit, or delete training topics  
- Employees can view and engage with available content  
- Organized for easy learning and tracking  

 **FAQ:**  Added a Frequently Asked Questions (FAQ) module for quick access to common queries.  
- Employees can browse FAQs for self-service support  
- Admins can add or update FAQs as needed  
- Improves efficiency by reducing repetitive queries  

 **Contact Us:** Implemented a Contact Us form for direct communication with HR.  
- Employees can submit messages with subject and details  
- Messages are delivered securely to HR for review and response  
- Streamlined internal communication channel  

 **Logo Management:** Introduced a dedicated Logo Management module, allowing companies to manage their branding directly within the platform.  
- Upload and preview company logos  
- Update or replace existing logos  
- Delete logos when needed  

 **Working Days:** Modified a Working Days module to track employee attendance and leave details.
- Displays Employee ID, Name, and monthly attendance summary
- Calculates working days = (regular muster count + approved muster requests)
- Shows leaves taken in the month and total working days
- Helps in accurate attendance tracking and payroll processing

**Dashboard Updates:** 

1. The dashboard now displays top-bar statistics, providing HR and Managers with a quick overview of daily workforce activity:
   - Total Employees, Clock-ins Today, and Today Leaves. 

2. Added Active Tasks Card on the user dashboard. Shows number of current active tasks:
   - If tasks exist → "You have X active tasks".
   - If no tasks exist → "No tasks in sight, you're all caught up".

3. Sidebar updated with quick links for better navigation, giving users easy access to:  
   - HR4U, Training, Task Management, Logo Management, Login History etc..

## Development Workflow

**Design Models:** Define database models for multi-company support, employee media, training, tasks, help desk tickets, and encrypted fields.

**Build Forms:** Create Django forms (ModelForms) to handle user input such as resignation requests, task assignments, self-service updates, and contact messages.

**Develop Views:** Implement function-based or class-based views to manage business logic including multi-company login, task management, HR Contacts, and session control.

**Configure URLs:** Map all views to appropriate URLs in both app-level and project-level urls.py to organize routing cleanly.

**Create Templates:** Develop responsive and interactive HTML templates for dashboards, login, training, FAQ, task lists, and help desk ticketing, etc.

**Integrate Security Features:** Add session timeout, single device login restriction, login history tracking, and field-level encryption using django-cryptography.

**Implement Sidebar & Navigation:** Update sidebar with links to new modules and pages such as Training, FAQ, Contact Us, and Task Management, etc for easy navigation.

**Update Dependencies:** Maintain and update requirements.txt with all installed libraries.   
      ```bash
      pip freeze > requirements.txt

## PWA & Offline Support in HR4U

The HR4U Project is now enhanced with Progressive Web App (PWA) features, making it installable on both desktop and mobile, and fully functional even when offline.

**Installable Application:** 
- HR4U can now be installed directly from the browser onto mobile or desktop devices.

**Offline Availability:**
- Cached pages, forms, and key data remain accessible even without an internet connection.