"""
Selenium End-to-End Test - Cross Impact Verification (TC017)
Tests that deleting one task doesn't affect other tasks
Creates 2 tasks, deletes the second one, verifies the first still exists

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


class TodoCrossImpactTest:
    """Test for cross-impact verification in Todo application"""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.driver = None
        self.test_results = {
            'test_case_id': 'TC017',
            'test_name': 'Cross Impact Verification - E2E',
            'test_class': 'TodoCrossImpactTest',
            'status': 'PENDING',
            'message': '',
            'error': None,
            'steps': [],
            'metrics': {
                'first_task_title': '',
                'first_task_id': '',
                'second_task_title': '',
                'second_task_id': '',
                'first_task_still_exists': False,
                'duration_seconds': 0
            },
            'timestamp': datetime.now().isoformat()
        }

    def setup(self):
        """Setup the Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        # Uncomment for headless mode
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

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

    def create_task_and_get_id(self, task_title):
        """Create a task and return its ID"""
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
                    submit_button = self.driver.find_element(
                        By.XPATH, "//button[@type='submit'] | //input[@type='submit']"
                    )

            submit_button.click()

            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located((By.NAME, "title"))
            )

            time.sleep(0.5)

            # Get all delete links and find the one for our task
            delete_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='delete_task']")
            for link in delete_links:
                # Check if this link is near our task title
                try:
                    parent = link.find_element(By.XPATH, "./ancestor::*[contains(., '" + task_title + "')]")
                    if parent:
                        task_id = link.get_attribute('href').split('/')[-2]
                        print(f"✅ Created task '{task_title}' with ID: {task_id}")
                        return task_id
                except NoSuchElementException:
                    continue

            # Fallback: assume first link is newest task
            if delete_links:
                task_id = delete_links[0].get_attribute('href').split('/')[-2]
                print(f"✅ Created task '{task_title}' with ID: {task_id} (fallback)")
                return task_id

            return None

        except Exception as e:
            print(f"❌ Error creating task: {e}")
            return None

    def task_exists_by_id(self, task_id):
        """Check if task exists by ID"""
        try:
            self.driver.find_element(By.CSS_SELECTOR, f"a[href*='delete_task/{task_id}']")
            return True
        except NoSuchElementException:
            return False

    def task_exists_by_title(self, task_title):
        """Check if task exists by title"""
        try:
            elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{task_title}')]")
            return len(elements) > 0
        except NoSuchElementException:
            return False

    def delete_task_by_id(self, task_id):
        """Delete a task by its ID"""
        try:
            delete_link = self.driver.find_element(By.CSS_SELECTOR, f"a[href*='delete_task/{task_id}']")
            delete_link.click()

            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located(
                    (By.XPATH, "//input[@type='submit'] | //button[@type='submit']")
                )
            )

            try:
                confirm_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            except NoSuchElementException:
                try:
                    confirm_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                except NoSuchElementException:
                    confirm_button = self.driver.find_element(
                        By.XPATH, "//input[@type='submit'] | //button[@type='submit']"
                    )

            confirm_button.click()

            WebDriverWait(self.driver, 5).until(
                expected_conditions.presence_of_element_located((By.NAME, "title"))
            )

            print(f"✅ Deleted task with ID: {task_id}")
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

        # Load existing tests
        existing_tests = []
        try:
            with open(output_path, encoding='utf-8') as f:
                existing_data = json.load(f)
                existing_tests = existing_data.get('tests', [])
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        # Add current test
        all_tests = existing_tests + [self.test_results]

        # Calculate summary
        total = len(all_tests)
        passed = len([t for t in all_tests if t['status'] == 'PASS'])
        failed = len([t for t in all_tests if t['status'] == 'FAIL'])
        errors = len([t for t in all_tests if t['status'] == 'ERROR'])

        report = {
            'summary': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'skipped': 0,
                'success_rate': f"{(passed / total * 100) if total > 0 else 0:.2f}%",
                'duration_seconds': sum(t['metrics'].get('duration_seconds', 0) for t in all_tests)
            },
            'tests': all_tests
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📄 Test report saved to: {output_path}")
        except Exception as e:
            print(f"\n⚠️  Failed to save JSON report: {e}")

    def run_test(self):
        """Run the cross-impact verification test"""
        print("\n" + "="*70)
        print("Starting E2E Test: TC017 - Cross Impact Verification")
        print("="*70)

        start_time = time.time()

        try:
            self.setup()
            self.log_step("Setup", "PASS", "WebDriver initialized")

            print(f"\n📍 Navigating to {self.base_url}...")
            self.driver.get(self.base_url)
            self.log_step("Navigation", "PASS", f"Loaded {self.base_url}")

            WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.NAME, "title"))
            )

            # Create first task
            print("\n📋 Step 1: Creating first task...")
            first_task_title = f"Cross Impact Test - Task A - {int(time.time())}"
            first_task_id = self.create_task_and_get_id(first_task_title)

            if not first_task_id:
                raise Exception("Failed to create first task")

            self.test_results['metrics']['first_task_title'] = first_task_title
            self.test_results['metrics']['first_task_id'] = first_task_id
            self.log_step("Create First Task", "PASS", f"Task ID: {first_task_id}")

            # Create second task
            print("\n📋 Step 2: Creating second task...")
            second_task_title = f"Cross Impact Test - Task B - {int(time.time())}"
            second_task_id = self.create_task_and_get_id(second_task_title)

            if not second_task_id:
                raise Exception("Failed to create second task")

            self.test_results['metrics']['second_task_title'] = second_task_title
            self.test_results['metrics']['second_task_id'] = second_task_id
            self.log_step("Create Second Task", "PASS", f"Task ID: {second_task_id}")

            # Verify both exist
            print("\n📋 Step 3: Verifying both tasks exist...")
            first_exists_before = self.task_exists_by_id(first_task_id)
            second_exists_before = self.task_exists_by_id(second_task_id)

            if first_exists_before and second_exists_before:
                print("✅ Both tasks exist")
                self.log_step("Verify Tasks Before Deletion", "PASS", "Both tasks exist")

            # Delete second task
            print(f"\n📋 Step 4: Deleting second task (ID: {second_task_id})...")
            deletion_success = self.delete_task_by_id(second_task_id)

            if not deletion_success:
                raise Exception("Failed to delete second task")

            self.log_step("Delete Second Task", "PASS", f"Deleted task ID: {second_task_id}")

            # Verify first task still exists
            print("\n📋 Step 5: Verifying first task still exists...")
            time.sleep(0.5)

            first_exists_after = self.task_exists_by_id(first_task_id)
            if not first_exists_after:
                first_exists_after = self.task_exists_by_title(first_task_title)

            second_exists_after = self.task_exists_by_id(second_task_id)

            self.test_results['metrics']['first_task_still_exists'] = first_exists_after

            print("\n" + "="*70)
            print("TEST RESULTS")
            print("="*70)
            print(f"First task (ID: {first_task_id}): {first_task_title}")
            print(f"Second task (ID: {second_task_id}): {second_task_title}")
            print(f"First task exists after deletion: {first_exists_after}")
            print(f"Second task exists after deletion: {second_exists_after}")
            print("="*70)

            # Determine result
            if first_exists_after and not second_exists_after:
                print("✅ TEST PASSED")
                self.test_results['status'] = 'PASS'
                self.test_results['message'] = 'Cross-impact verification successful'
                result = True
            else:
                error_msg = []
                if not first_exists_after:
                    error_msg.append("First task was deleted")
                if second_exists_after:
                    error_msg.append("Second task still exists")

                print(f"❌ TEST FAILED: {'; '.join(error_msg)}")
                self.test_results['status'] = 'FAIL'
                self.test_results['message'] = '; '.join(error_msg)
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
                self.driver.save_screenshot("test_cross_impact_error.png")
                print("📸 Screenshot saved")
            except Exception:
                pass
            return False

        finally:
            print("\n🧹 Cleaning up...")
            self.teardown()
            self.save_json_report()


def main():
    """Main entry point"""
    test = TodoCrossImpactTest()
    success = test.run_test()

    if success:
        print("\n🎉 Cross-impact test passed!")
        exit(0)
    else:
        print("\n❌ Cross-impact test failed!")
        exit(1)


if __name__ == "__main__":
    main()
