"""
Selenium End-to-End Test for To-Do List Application
Tests the complete CRUD cycle: Create 10 tasks, then delete them all
Runs against a live instance at http://127.0.0.1:8000

Generates a JSON report: result_test_selenium.json
"""
import json
import os
import time
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


class TodoE2ETest:
    """End-to-end test for Todo application using Selenium"""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.driver = None
        self.test_results = {
            'test_case_id': 'TC016',
            'test_name': 'CRUD Complete Cycle - E2E',
            'test_class': 'TodoE2ETest',
            'status': 'PENDING',
            'message': '',
            'error': None,
            'steps': [],
            'metrics': {
                'initial_count': 0,
                'after_creation_count': 0,
                'final_count': 0,
                'tasks_created': 0,
                'tasks_deleted': 0,
                'duration_seconds': 0
            },
            'timestamp': datetime.now().isoformat()
        }

    def setup(self):
        """Setup the Chrome WebDriver with automatic driver management"""
        options = webdriver.ChromeOptions()
        # Uncomment the next line to run in headless mode (no GUI)
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        # Automatically download and use the correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        print("✅ WebDriver initialized")

    def log_step(self, step_name, status, message=""):
        """Log a test step"""
        step = {
            'step': step_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results['steps'].append(step)

    def teardown(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("✅ WebDriver closed")

    def get_task_count(self):
        """Count the number of tasks displayed on the page"""
        try:
            tasks = self.driver.find_elements(By.CSS_SELECTOR, "form[action*='delete_task']")
            count = len(tasks)
            print(f"📊 Current task count: {count}")
            return count
        except Exception as e:
            print(f"❌ Error counting tasks: {e}")
            return 0

    def create_task(self, task_title):
        """Create a new task"""
        try:
            input_field = self.driver.find_element(By.NAME, "title")
            input_field.clear()
            input_field.send_keys(task_title)

            try:
                submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            except NoSuchElementException:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
                except NoSuchElementException:
                    submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit'] | //input[@type='submit']")

            submit_button.click()

            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located((By.NAME, "title"))
            )

            print(f"✅ Created task: {task_title}")
            return True
        except Exception as e:
            print(f"❌ Error creating task '{task_title}': {e}")
            return False

    def delete_first_task(self):
        """Delete the first task in the list"""
        try:
            delete_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='delete_task']")

            if not delete_links:
                print("⚠️  No tasks to delete")
                return False

            delete_links[0].click()

            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located((By.XPATH, "//input[@type='submit'] | //button[@type='submit']"))
            )

            try:
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            except NoSuchElementException:
                try:
                    confirm_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                except NoSuchElementException:
                    confirm_button = self.driver.find_element(By.XPATH, "//input[@type='submit'] | //button[@type='submit']")

            confirm_button.click()

            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located((By.NAME, "title"))
            )

            print("✅ Deleted one task")
            return True
        except Exception as e:
            print(f"❌ Error deleting task: {e}")
            return False

    def save_json_report(self):
        """Save test results to JSON file"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(current_dir) == 'tasks':
            project_root = os.path.dirname(current_dir)
        else:
            project_root = current_dir

        output_path = os.path.join(project_root, 'result_test_selenium.json')

        report = {
            'summary': {
                'total': 1,
                'passed': 1 if self.test_results['status'] == 'PASS' else 0,
                'failed': 1 if self.test_results['status'] == 'FAIL' else 0,
                'errors': 1 if self.test_results['status'] == 'ERROR' else 0,
                'skipped': 0,
                'success_rate': '100.00%' if self.test_results['status'] == 'PASS' else '0.00%',
                'duration_seconds': self.test_results['metrics']['duration_seconds']
            },
            'tests': [self.test_results]
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Test report saved to: {output_path}")
        except Exception as e:
            print(f"\n⚠️  Failed to save JSON report: {e}")

    def run_test(self):
        """Run the complete end-to-end test"""
        print("\n" + "="*70)
        print("Starting End-to-End Test: TC016 - CRUD Complete Cycle")
        print("="*70)

        start_time = time.time()

        try:
            self.setup()
            self.log_step("Setup", "PASS", "WebDriver initialized")

            print(f"\n📍 Navigating to {self.base_url}...")
            self.driver.get(self.base_url)
            print("✅ Page loaded")
            self.log_step("Navigation", "PASS", f"Loaded {self.base_url}")

            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.NAME, "title"))
            )

            print("\n📋 Step 1: Counting initial tasks...")
            initial_count = self.get_task_count()
            self.test_results['metrics']['initial_count'] = initial_count
            self.log_step("Count Initial Tasks", "PASS", f"Found {initial_count} tasks")

            print("\n📋 Step 2: Creating 10 new tasks...")
            created_count = 0
            for i in range(1, 11):
                task_title = f"E2E Test Task {i}"
                if self.create_task(task_title):
                    created_count += 1

            print(f"✅ Successfully created {created_count}/10 tasks")
            self.test_results['metrics']['tasks_created'] = created_count
            self.log_step("Create Tasks", "PASS" if created_count == 10 else "WARN",
                         f"Created {created_count}/10 tasks")

            print("\n📋 Step 3: Verifying task count...")
            after_creation_count = self.get_task_count()
            self.test_results['metrics']['after_creation_count'] = after_creation_count
            expected_count = initial_count + created_count

            if after_creation_count == expected_count:
                print(f"✅ Task count correct: {after_creation_count}")
                self.log_step("Verify Count After Creation", "PASS",
                             f"Count is {after_creation_count} as expected")
            else:
                print(f"⚠️  Task count mismatch: {after_creation_count} (expected {expected_count})")
                self.log_step("Verify Count After Creation", "WARN",
                             f"Expected {expected_count}, got {after_creation_count}")

            print(f"\n📋 Step 4: Deleting the {created_count} created tasks...")
            deleted_count = 0
            for i in range(created_count):
                if self.delete_first_task():
                    deleted_count += 1
                else:
                    self.driver.get(self.base_url)
                    time.sleep(1)

            print(f"✅ Successfully deleted {deleted_count}/{created_count} tasks")
            self.test_results['metrics']['tasks_deleted'] = deleted_count
            self.log_step("Delete Tasks", "PASS" if deleted_count == created_count else "WARN",
                         f"Deleted {deleted_count}/{created_count} tasks")

            print("\n📋 Step 5: Verifying final task count...")
            final_count = self.get_task_count()
            self.test_results['metrics']['final_count'] = final_count

            print("\n" + "="*70)
            print("TEST RESULTS")
            print("="*70)
            print(f"Initial count:  {initial_count}")
            print(f"After creation: {after_creation_count}")
            print(f"Final count:    {final_count}")
            print("="*70)

            creation_success = (created_count == 10)
            deletion_success = (deleted_count == created_count)
            final_count_match = (final_count == initial_count)

            if creation_success and deletion_success and final_count_match:
                print("✅ TEST PASSED")
                self.test_results['status'] = 'PASS'
                self.test_results['message'] = 'All operations completed successfully'
                result = True
            else:
                errors = []
                if not creation_success:
                    errors.append(f"Created {created_count}/10")
                if not deletion_success:
                    errors.append(f"Deleted {deleted_count}/{created_count}")
                if not final_count_match:
                    errors.append(f"Final count {final_count} != {initial_count}")

                self.test_results['status'] = 'FAIL'
                self.test_results['message'] = "; ".join(errors)
                print(f"❌ TEST FAILED: {self.test_results['message']}")
                result = False

            end_time = time.time()
            self.test_results['metrics']['duration_seconds'] = round(end_time - start_time, 2)
            return result

        except Exception as e:
            print(f"\n❌ TEST ERROR: {e}")
            import traceback
            error_trace = traceback.format_exc()
            print(error_trace)

            self.test_results['status'] = 'ERROR'
            self.test_results['message'] = str(e)
            self.test_results['error'] = error_trace

            end_time = time.time()
            self.test_results['metrics']['duration_seconds'] = round(end_time - start_time, 2)

            try:
                self.driver.save_screenshot("test_error.png")
                print("📸 Screenshot saved to test_error.png")
            except Exception:
                pass
            return False

        finally:
            print("\n🧹 Cleaning up...")
            self.teardown()
            self.save_json_report()


def main():
    """Main entry point for the test"""
    test = TodoE2ETest()
    success = test.run_test()

    if success:
        print("\n🎉 All E2E tests passed!")
        exit(0)
    else:
        print("\n❌ E2E tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
