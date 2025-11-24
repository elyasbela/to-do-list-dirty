from django.test import Client, TestCase

from .models import Task


class TaskViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.task = Task.objects.create(
            title="Test Task",
            complete=False
        )

    def test_index_page_loads(self):
        """Test that the index page loads successfully"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/list.html")

    def test_index_page_contains_tasks(self):
        """Test that tasks appear on the index page"""
        response = self.client.get("/")
        self.assertContains(response, self.task.title)

    def test_index_page_contains_form(self):
        """Test that the form is present on the index page"""
        response = self.client.get("/")
        self.assertIn("form", response.context)

    def test_create_task_post(self):
        """Test creating a new task via POST"""
        response = self.client.post("/", {"title": "New Task"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title="New Task").exists())

    def test_update_task_page_loads(self):
        """Test that the update task page loads"""
        response = self.client.get(f"/update_task/{self.task.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/update_task.html")

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

    def test_delete_task_page_loads(self):
        """Test that the delete task page loads"""
        response = self.client.get(f"/delete_task/{self.task.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/delete.html")

    def test_delete_task_post(self):
        """Test deleting a task"""
        task_id = self.task.id
        response = self.client.post(f"/delete_task/{task_id}/")
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=task_id).exists())

    def test_app_version_in_context(self):
        """Test that APP_VERSION is present in context"""
        response = self.client.get("/")
        self.assertIn("APP_VERSION", response.context)

class DatasetImportTests(TestCase):
    fixtures = ["dataset.json"]

    def test_dataset_loads_correctly(self):
        """Test that dataset.json loads all tasks"""
        tasks = Task.objects.all()
        self.assertEqual(tasks.count(), 5)

    def test_dataset_contains_expected_tasks(self):
        """Test that specific tasks are in the dataset"""
        self.assertTrue(Task.objects.filter(title="Buy groceries").exists())
        self.assertTrue(
            Task.objects.filter(title="Finish project documentation").exists()
        )
        self.assertTrue(Task.objects.filter(title="Review pull requests").exists())

    def test_dataset_task_completion_status(self):
        """Test that task completion status is correct"""
        buy_groceries = Task.objects.get(title="Buy groceries")
        self.assertFalse(buy_groceries.complete)

        finished_task = Task.objects.get(title="Finish project documentation")
        self.assertTrue(finished_task.complete)

    def test_dataset_task_count_by_status(self):
        """Test the count of completed vs incomplete tasks"""
        completed = Task.objects.filter(complete=True).count()
        incomplete = Task.objects.filter(complete=False).count()

        self.assertEqual(completed, 2)
        self.assertEqual(incomplete, 3)
