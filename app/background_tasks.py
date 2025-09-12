import threading
import time
from django.core.management import call_command

def start_background_tasks():
    def run_tasks():
        while True:
            try:
                print("🧹 Running clearsessions...")
                call_command('clearsessions')

                print("📈 Running escalate_tickets...")
                call_command('escalate_tickets')

                print("🗑️ Cleaning old login logs...")
                call_command('delete_old_loginlogs')

            except Exception as e:
                print(f"❌ Background task error: {e}")

            time.sleep(30)

    threading.Thread(target=run_tasks, daemon=True).start()
