import json
import os
from functools import wraps

from django.conf import settings
from django.test import Client, TestCase

from tasks.models import Task


def tc(test_case_id):
    """Décorateur pour ajouter un ID de test case"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.test_case_id = test_case_id
        return wrapper
    return decorator


class TaskViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(
            title="Test Task",
            complete=False
        )

    @tc("TC001")
    def test_index_page_loads(self):
        """Test that the index page loads successfully"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/list.html")

    @tc("TC002")
    def test_index_page_contains_tasks(self):
        """Test that tasks appear on the index page"""
        response = self.client.get("/")
        self.assertContains(response, self.task.title)

    @tc("TC003")
    def test_index_page_contains_form(self):
        """Test that the form is present on the index page"""
        response = self.client.get("/")
        self.assertIn("form", response.context)

    @tc("TC004")
    def test_create_task_post(self):
        """Test creating a new task via POST"""
        response = self.client.post("/", {"title": "New Task"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title="New Task").exists())

    @tc("TC006")
    def test_update_task_page_loads(self):
        """Test that the update task page loads"""
        response = self.client.get(f"/update_task/{self.task.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/update_task.html")

    @tc("TC007")
    def test_update_task_post(self):
        """Test updating a task"""
        response = self.client.post(
            f"/update_task/{self.task.id}/",
            {"title": "Updated Task", "complete": True}
        )
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Updated Task")
        self.assertTrue(self.task.complete)

    @tc("TC008")
    def test_update_task_invalid_post(self):
        """Test updating a task with invalid data"""
        response = self.client.post(
            f"/update_task/{self.task.id}/",
            {}
        )
        self.assertEqual(response.status_code, 200)

    @tc("TC009")
    def test_delete_task_page_loads(self):
        """Test that the delete task page loads"""
        response = self.client.get(f"/delete_task/{self.task.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/delete.html")

    @tc("TC010")
    def test_delete_task_post(self):
        """Test deleting a task"""
        task_id = self.task.id
        response = self.client.post(f"/delete_task/{task_id}/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    @tc("TC012")
    def test_app_version_in_context(self):
        """Test that APP_VERSION is present in context"""
        response = self.client.get("/")
        self.assertIn("APP_VERSION", response.context)


class DatasetImportTests(TestCase):
    def setUp(self):
        """Load dataset.json from root for each test"""
        dataset_path = os.path.join(settings.BASE_DIR, "dataset.json")
        with open(dataset_path, "r") as f:
            data = json.load(f)

        # Import tasks from dataset
        for item in data:
            if item["model"] == "tasks.task":
                Task.objects.create(
                    id=item["pk"],
                    title=item["fields"]["title"],
                    complete=item["fields"]["complete"]
                )

    @tc("TC011")
    def test_dataset_loads_correctly(self):
        """Test that dataset.json loads all tasks"""
        tasks = Task.objects.all()
        self.assertEqual(tasks.count(), 5)

    @tc("TC011")
    def test_dataset_contains_expected_tasks(self):
        """Test that specific tasks are in the dataset"""
        self.assertTrue(Task.objects.filter(title="Buy groceries").exists())
        self.assertTrue(
            Task.objects.filter(title="Finish project documentation").exists()
        )
        self.assertTrue(Task.objects.filter(title="Review pull requests").exists())

    @tc("TC011")
    def test_dataset_task_completion_status(self):
        """Test that task completion status is correct"""
        buy_groceries = Task.objects.get(title="Buy groceries")
        self.assertFalse(buy_groceries.complete)

        finished_task = Task.objects.get(title="Finish project documentation")
        self.assertTrue(finished_task.complete)

    @tc("TC011")
    def test_dataset_task_count_by_status(self):
        """Test the count of completed vs incomplete tasks"""
        completed = Task.objects.filter(complete=True).count()
        incomplete = Task.objects.filter(complete=False).count()

        self.assertEqual(completed, 2)
        self.assertEqual(incomplete, 3)
