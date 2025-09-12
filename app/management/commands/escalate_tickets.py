from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.core.mail import send_mail
from datetime import timedelta
from app.models import HelpDeskTicket

class Command(BaseCommand):
    help = "Escalate tickets to HR and Manager if unseen within 2 hours."

    HR_ISSUE_DISPLAY = {
        'attendance': 'Attendance Issue',
        'payroll': 'Payroll Issue',
        'leave': 'Leave Request',
        'policy': 'Policy Clarification',
        'other': 'Other HR Issue',
    }

    IT_ISSUE_DISPLAY = {
        'login': 'Login Problem',
        'hardware': 'Hardware Issue',
        'software': 'Software Problem',
        'network': 'Network Issue',
        'other': 'Other IT Issue',
    }

    AS_ISSUE_DISPLAY = {
        'laptop': 'Laptop Not Working',
        'mouse': 'Mouse Not Working',
        'keyboard': 'Need New Equipment',
        'return': 'Return Asset Request',
        'other': 'Other Asset Issue',
    }

    def get_issue_display(self, ticket):
        issue_type = ticket.issue_type
        if ticket.category == 'HR':
            return self.HR_ISSUE_DISPLAY.get(issue_type, issue_type)
        elif ticket.category == 'IT':
            return self.IT_ISSUE_DISPLAY.get(issue_type, issue_type)
        elif ticket.category == 'AS':
            return self.AS_ISSUE_DISPLAY.get(issue_type, issue_type)
        return issue_type

    def handle(self, *args, **kwargs):
        now_time = now()

        # Escalate to HR after 2 hours if TL hasn't seen
        tl_tickets = HelpDeskTicket.objects.filter(
            viewed_by_tl=False,
            escalated_to_hr_at__isnull=True,
            created_at__lte=now_time - timedelta(hours=2)
        )

        for ticket in tl_tickets:
            ticket.escalated_to_hr_at = now_time
            ticket.save()

            issue_display = self.get_issue_display(ticket)

            if ticket.escalate_to_hr and ticket.escalate_to_hr.email:
                send_mail(
                    subject=f"[Escalated to HR] Ticket #{ticket.id}",
                    message=(
                        f"The ticket from {ticket.employee} has been escalated to you.\n\n"
                        f"Issue Type: {issue_display}\n"
                        f"Description: {ticket.description}"
                    ),
                    from_email=None,
                    recipient_list=[ticket.escalate_to_hr.email],
                    fail_silently=False,
                )
            self.stdout.write(self.style.WARNING(f"Escalated to HR: Ticket #{ticket.id}"))

        # Escalate to Manager after 2 more hours (4 total) if HR hasn't seen
        hr_tickets = HelpDeskTicket.objects.filter(
            viewed_by_hr=False,
            escalated_to_hr_at__isnull=False,
            escalated_to_manager_at__isnull=True,
            escalated_to_hr_at__lte=now_time - timedelta(hours=2)
        )

        for ticket in hr_tickets:
            ticket.escalated_to_manager_at = now_time
            ticket.save()

            issue_display = self.get_issue_display(ticket)

            if ticket.manager and ticket.manager.email:
                send_mail(
                    subject=f"[Escalated to Manager] Ticket #{ticket.id}",
                    message=(
                        f"The ticket from {ticket.employee} has now been escalated to you.\n\n"
                        f"Issue Type: {issue_display}\n"
                        f"Description: {ticket.description}"
                    ),
                    from_email=None,
                    recipient_list=[ticket.manager.email],
                    fail_silently=False,
                )
            self.stdout.write(self.style.ERROR(f"Escalated to Manager: Ticket #{ticket.id}"))

        self.stdout.write(self.style.SUCCESS("Escalation process completed."))