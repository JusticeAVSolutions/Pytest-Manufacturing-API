# conftest.py

import os
import tempfile
import pytest
import requests
import re
import json

# Global list to map test nodeids to unit_ids
test_unit_mapping = {}

def pytest_addoption(parser):
    parser.addoption(
        "--manufacturing-api-url",
        action="store",
        default="http://192.168.114.187:8000/",
        help="Manufacturing API URL"
    )
    parser.addoption(
        "--use-manufacturing-api",
        action="store_true",
        default=False,
        help="Utilize manufacturing API for serial numbering and logging test results"
    )
    
    # Create a temporary file for the JSON report
    temp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    temp_json_path = temp_json.name
    temp_json.close()  # Close the file so pytest-json-report can write to it

    # Add pytest-json-report options
    parser.addini("json_report", "Enable JSON report generation", type="bool", default=True)
    parser.addini("json_report_file", "Path to JSON report file", type="str", default=temp_json_path)

    parser.addoption(
        "--json-report", action="store_true", help="Generate a JSON report."
    )
    parser.addoption(
        "--json-report-file",
        action="store",
        default=temp_json_path,
        help=f"Path to JSON report file. Defaults to a temporary file: {temp_json_path}",
    )

@pytest.fixture(scope="session", autouse=True)
def enforce_json_report(pytestconfig):
    """
    Enforce the usage of pytest-json-report by setting the necessary options.
    """
    # Check if --json-report is already specified
    if not pytestconfig.getoption("--json-report"):
        # Inject --json-report and --json-report-file options
        pytestconfig.option.json_report = True
        # Use the defined json_report_file
        pytestconfig.option.json_report_file = pytestconfig.getini("json_report_file")

@pytest.fixture(scope='session')
def unit_id(request):
    # Initialize unit_id with a default value (or None)
    request.config.unit_id = None
    return request.config

def pytest_sessionfinish(session, exitstatus):
    """
    After the test session finishes, upload JSON test results, and delete the temp file.
    """

    unit_id = session.config.unit_id
    if unit_id:
        # Do something with the unit_id at the end of the session
        print(f"Unit ID: {unit_id}")
    else:
        print("No unit ID was set.")
        
    json_report_file = session.config.getoption("--json-report-file")
    
    if not json_report_file or not os.path.exists(json_report_file):
        print("JSON report file not found. Skipping upload.")
        return
    
    try:
        with open(json_report_file, 'r') as f:
            report_data = json.load(f)
        
            
        # Define the upload URL
        api_url = session.config.getoption("--manufacturing-api-url").rstrip('/')
        upload_url = f"{api_url}/units/{unit_id}/test_results/add_json"
            
        # Upload the test result
        response = requests.post(
            upload_url,
            json=report_data,  # Assuming the API expects JSON
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print(f"Logged test_result for Unit ID {unit_id}.")
        else:
            print(f"Failed to upload JSON report for Unit ID {unit_id}. Status Code: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"An error occurred while processing the JSON report: {e}")
    
    finally:
        # Delete the temporary JSON report file
        try:
            os.remove(json_report_file)
            print("Temporary JSON report file deleted.")
        except Exception as e:
            print(f"Failed to delete temporary JSON report file: {e}")
    
@pytest.fixture(scope='session')
def api_client(request):
    """Provides an API client for interacting with the REST API."""
    use_api = request.config.getoption("--use-manufacturing-api")
    api_url = request.config.getoption("--manufacturing-api-url")

    if not use_api:
        pytest.skip("Manufacturing API not enabled. Use --use-manufacturing-api to enable.")

    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url.rstrip('/')  # Ensure no trailing slash
            self.session = requests.Session()

        def create_product(self, name, uses_serial=False, uses_mac=False, serial_number_prefix=None):
            url = f'{self.base_url}/products/create'
            data = {
                'name': name,
                'uses_serial': str(uses_serial).lower(),
                'uses_mac': str(uses_mac).lower(),
                'serial_number_prefix': serial_number_prefix
            }
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()

        def create_serial_number(self, product_id, serial_number):
            url = f'{self.base_url}/serial_numbers/create'
            data = {
                'product_id': product_id,
                'serial_number': serial_number
            }
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()

        def create_mac_address(self, product_id, mac_address):
            url = f'{self.base_url}/mac_addresses/create'
            data = {
                'product_id': product_id,
                'mac_address': mac_address
            }
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()

        def create_unit(self, product_id, serial_number_id=None, mac_address_id=None):
            url = f'{self.base_url}/units/create'
            data = {'product_id': product_id}
            if serial_number_id is not None:
                data['serial_number_id'] = serial_number_id
            if mac_address_id is not None:
                data['mac_address_id'] = mac_address_id
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()

        def log_test_result(self, unit_id, test_result, details):
            url = f'{self.base_url}/units/{unit_id}/test_results/add_json'
            data = {
                "test_result": test_result,
                "details": details
            }
            response = self.session.post(url, json=data)
            response.raise_for_status()
            return response.json()

        def get_unit(self, unit_id):
            url = f'{self.base_url}/units/{unit_id}/json'
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        # Add more methods as needed for other endpoints

    return APIClient(api_url)
