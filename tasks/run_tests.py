import json
import os
import sys
import unittest

# Get the parent directory (project root) to import Django modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'todo.settings')

import django  # noqa: E402

django.setup()

from django.test.runner import DiscoverRunner  # noqa: E402


class StreamWrapper:
    """Wrapper for stream to add writeln method"""

    def __init__(self, stream):
        self.stream = stream

    def write(self, text):
        self.stream.write(text)

    def writeln(self, text=''):
        self.stream.write(text + '\n')

    def flush(self):
        self.stream.flush()


class JSONTestResult(unittest.TextTestResult):
    """Custom test result class that captures all test results"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results = []

    def startTest(self, test):  # noqa: N802
        super().startTest(test)
        # Store reference to current test
        self.current_test = test

    def addSuccess(self, test):  # noqa: N802
        super().addSuccess(test)
        # Get test_case_id from the test method
        test_method = getattr(test, test._testMethodName, None)
        test_case_id = getattr(test_method, 'test_case_id', 'N/A')

        self.test_results.append({
            'test_case_id': test_case_id,
            'test_name': test._testMethodName,
            'test_class': test.__class__.__name__,
            'status': 'PASS',
            'message': '',
            'error': None
        })

    def addError(self, test, err):  # noqa: N802
        super().addError(test, err)
        # Get test_case_id from the test method
        test_method = getattr(test, test._testMethodName, None)
        test_case_id = getattr(test_method, 'test_case_id', 'N/A')

        self.test_results.append({
            'test_case_id': test_case_id,
            'test_name': test._testMethodName,
            'test_class': test.__class__.__name__,
            'status': 'ERROR',
            'message': str(err[1]),
            'error': self._exc_info_to_string(err, test)
        })

    def addFailure(self, test, err):  # noqa: N802
        super().addFailure(test, err)
        # Get test_case_id from the test method
        test_method = getattr(test, test._testMethodName, None)
        test_case_id = getattr(test_method, 'test_case_id', 'N/A')

        self.test_results.append({
            'test_case_id': test_case_id,
            'test_name': test._testMethodName,
            'test_class': test.__class__.__name__,
            'status': 'FAIL',
            'message': str(err[1]),
            'error': self._exc_info_to_string(err, test)
        })

    def addSkip(self, test, reason):  # noqa: N802
        super().addSkip(test, reason)
        # Get test_case_id from the test method
        test_method = getattr(test, test._testMethodName, None)
        test_case_id = getattr(test_method, 'test_case_id', 'N/A')

        self.test_results.append({
            'test_case_id': test_case_id,
            'test_name': test._testMethodName,
            'test_class': test.__class__.__name__,
            'status': 'SKIP',
            'message': reason,
            'error': None
        })


class JSONTestRunner(DiscoverRunner):
    """Custom Django test runner that uses JSONTestResult"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.json_result = None

    def get_resultclass(self):
        return JSONTestResult

    def run_suite(self, suite, **kwargs):
        """Override to use custom result class"""
        resultclass = self.get_resultclass()
        result = resultclass(
            stream=StreamWrapper(sys.stderr),
            descriptions=True,
            verbosity=self.verbosity
        )

        # Run the test suite
        suite(result)

        # Store the result for later access
        self.json_result = result

        return result


def run_tests():
    """Run all tests and generate JSON report"""

    # Create custom test runner
    runner = JSONTestRunner(verbosity=2, interactive=False, keepdb=False)

    # Run tests for the tasks app
    failures = runner.run_tests(['tasks'])

    # Get results from the runner
    if runner.json_result and hasattr(runner.json_result, 'test_results'):
        test_results = runner.json_result.test_results
    else:
        test_results = []

    # Prepare summary
    total_tests = len(test_results)
    passed = len([t for t in test_results if t['status'] == 'PASS'])
    failed = len([t for t in test_results if t['status'] == 'FAIL'])
    errors = len([t for t in test_results if t['status'] == 'ERROR'])
    skipped = len([t for t in test_results if t['status'] == 'SKIP'])

    # Create output structure
    output = {
        'summary': {
            'total': total_tests,
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'skipped': skipped,
            'success_rate': f"{(passed / total_tests * 100) if total_tests > 0 else 0:.2f}%"
        },
        'tests': test_results
    }

    # Write results to JSON file at project root
    output_path = os.path.join(project_root, 'result_test_auto.json')

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print(f"Test results saved to: {output_path}")
    print(f"{'='*70}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Skipped: {skipped}")
    print(f"Success rate: {output['summary']['success_rate']}")
    print(f"{'='*70}\n")

    # Return exit code (0 = success, non-zero = failure)
    return failures


if __name__ == '__main__':
    sys.exit(run_tests())
