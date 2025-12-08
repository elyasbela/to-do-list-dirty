import json
import os
import sys

import yaml

# Get the parent directory (project root)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)


def load_yaml_tests(yaml_path):
    """Load test definitions from YAML file"""
    try:
        with open(yaml_path, encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('tests', [])
    except FileNotFoundError:
        print(f"❌ Error: File not found: {yaml_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML: {e}")
        sys.exit(1)


def load_json_results(json_path):
    """Load test results from JSON file"""
    try:
        with open(json_path, encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        # Return empty results if file not found (not an error for optional files)
        return {'tests': []}
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Error parsing JSON {json_path}: {e}")
        return {'tests': []}


def find_test_result(test_case_id, json_results):
    """Find a test result by test_case_id in JSON results"""
    for test in json_results.get('tests', []):
        if test.get('test_case_id') == test_case_id:
            return test
    return None


def get_status_icon(test, json_results):
    """Determine the status icon for a test"""
    test_type = test.get('type', '')
    test_case_id = test.get('test_case_id', '')

    # Check if it's a manual test
    if test_type == 'manuel':
        return '🫱', 'Manual test needed'

    # For automated tests (including unittest and selenium), check JSON results
    result = find_test_result(test_case_id, json_results)

    if result is None:
        return '🕳️', 'Not found'

    status = result.get('status', '')
    if status == 'PASS':
        return '✅', 'Passed'
    elif status == 'FAIL':
        return '❌', 'Failed'
    elif status == 'ERROR':
        return '❌', 'Error'
    elif status == 'SKIP':
        return '⏭️', 'Skipped'
    else:
        return '❓', 'Unknown'


def generate_report():
    """Generate the test report"""
    # Paths
    yaml_path = os.path.join(project_root, 'test_list.yaml')
    json_auto_path = os.path.join(project_root, 'result_test_auto.json')
    json_selenium_path = os.path.join(project_root, 'result_test_selenium.json')

    # Load data
    print("Lecture des tests auto via result_test_auto.json… ", end='')
    json_auto_results = load_json_results(json_auto_path)
    auto_tests_count = len(json_auto_results.get('tests', []))
    print(f"OK ({auto_tests_count} tests)")

    print("Lecture des tests E2E via result_test_selenium.json… ", end='')
    json_selenium_results = load_json_results(json_selenium_path)
    selenium_tests_count = len(json_selenium_results.get('tests', []))
    print(f"OK ({selenium_tests_count} tests)\n")

    # Merge results from both sources
    json_results = {
        'tests': json_auto_results.get('tests', []) + json_selenium_results.get('tests', [])
    }

    # Load test definitions
    tests = load_yaml_tests(yaml_path)

    # Generate report
    for test in tests:
        test_case_id = test.get('test_case_id', 'N/A')
        test_type = test.get('type', 'unknown')
        icon, status_text = get_status_icon(test, json_results)

        print(f"{test_case_id} | {test_type:15s} | {icon} {status_text}")

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    total_tests = len(tests)
    manual_tests = len([t for t in tests if t.get('type') == 'manuel'])
    auto_unittest_tests = len([t for t in tests if t.get('type') == 'auto-unittest'])
    auto_selenium_tests = len([t for t in tests if t.get('type') == 'auto-selenium'])

    # Count automated test results
    passed = 0
    failed = 0
    not_found = 0

    for test in tests:
        if test.get('type') != 'manuel':
            icon, status = get_status_icon(test, json_results)
            if status == 'Passed':
                passed += 1
            elif status in ['Failed', 'Error']:
                failed += 1
            elif status == 'Not found':
                not_found += 1

    # Calculate percentages
    passed_pct = (passed / total_tests * 100) if total_tests > 0 else 0
    failed_pct = (failed / total_tests * 100) if total_tests > 0 else 0
    not_found_pct = (not_found / total_tests * 100) if total_tests > 0 else 0
    manual_pct = (manual_tests / total_tests * 100) if total_tests > 0 else 0
    passed_manual_pct = ((passed + manual_tests) / total_tests * 100) if total_tests > 0 else 0

    print(f"Number of tests: {total_tests}")
    print(f"  - Unit/Integration tests: {auto_unittest_tests}")
    print(f"  - E2E Selenium tests: {auto_selenium_tests}")
    print(f"  - Manual tests: {manual_tests}")
    print("")
    print(f"✅ Passed tests: {passed} ({passed_pct:.1f}%)")
    print(f"❌ Failed tests: {failed} ({failed_pct:.1f}%)")
    print(f"🕳️  Not found tests: {not_found} ({not_found_pct:.1f}%)")
    print(f"🫱 Test to pass manually: {manual_tests} ({manual_pct:.1f}%)")
    print(f"✅ Passed + 🫱 Manual: {passed + manual_tests} ({passed_manual_pct:.1f}%)")

    # Show detailed failures if any
    failures = []
    for test in tests:
        if test.get('type') != 'manuel':
            result = find_test_result(test.get('test_case_id'), json_results)
            if result and result.get('status') in ['FAIL', 'ERROR']:
                failures.append({
                    'test': test,
                    'result': result
                })

    if failures:
        print("\n" + "="*60)
        print("FAILED TESTS DETAILS")
        print("="*60)
        for item in failures:
            test = item['test']
            result = item['result']
            print(f"\n{test.get('test_case_id')} - {test.get('name')}")
            print(f"  Status: {result.get('status')}")
            print(f"  Test: {result.get('test_class')}.{result.get('test_name')}")
            if result.get('message'):
                print(f"  Message: {result.get('message')[:100]}")

            # Show metrics for Selenium tests
            if 'metrics' in result:
                metrics = result['metrics']
                print("  Metrics:")
                print(f"    - Initial count: {metrics.get('initial_count', 'N/A')}")
                print(f"    - Tasks created: {metrics.get('tasks_created', 'N/A')}")
                print(f"    - Tasks deleted: {metrics.get('tasks_deleted', 'N/A')}")
                print(f"    - Final count: {metrics.get('final_count', 'N/A')}")


if __name__ == '__main__':
    try:
        generate_report()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
