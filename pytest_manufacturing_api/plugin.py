import os
import tempfile
import pytest
import requests
import re
import json

__pytest_sequencer_plugin__ = True

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

@pytest.fixture(scope='session')
def unit_id(request):
    # Initialize unit_id with a default value (or None)
    request.config.unit_id = None
    return request.config

def pytest_configure(config):
    if not getattr(config.option, 'json_report', False):
        config.option.json_report = True

    if not getattr(config.option, 'json_report_file', None):
        # Create a temporary file for the JSON report
        temp_json = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        temp_json_path = temp_json.name
        temp_json.close()  # Close the file so pytest-json-report can write to it
        config.option.json_report_file = temp_json_path
        # Indicate that we created this temp file
        config.option.created_temp_json_report_file = True
    else:
        config.option.created_temp_json_report_file = False

def pytest_sessionfinish(session, exitstatus):
    """
    After the test session finishes, upload JSON test results, and delete the temp file.
    """

    unit_id = getattr(session, 'unit_id', None)
    if unit_id:
        print(f"Unit ID: {unit_id}")
    else:
        print("No unit ID was set. No test results were logged")
        return #TODO

    # Retrieve the json_report_file option
    json_report_file = session.config.option.json_report_file

    if not json_report_file or not os.path.exists(json_report_file):
        print("JSON report file not found. Skipping upload.")
        return
    
    try:
        with open(json_report_file, 'r', encoding='utf-8-sig') as f:
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
        # Only delete the temporary JSON report file if we created it
        if getattr(session.config.option, 'created_temp_json_report_file', False):
            try:
                os.remove(json_report_file)
                print("Temporary JSON report file deleted.")
            except Exception as e:
                print(f"Failed to delete temporary JSON report file: {e}")
        else:
            print("Did not delete JSON report file since it was not created by this plugin.")
    
@pytest.fixture(scope='session')
def manufacturing_api_client(request):
    """Provides an API client for interacting with the REST API."""
    use_api = request.config.getoption("--use-manufacturing-api")
    api_url = request.config.getoption("--manufacturing-api-url")

    if not use_api:
        pytest.skip("Manufacturing API not enabled. Use --use-manufacturing-api to enable.")

    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url.rstrip('/')  # Ensure no trailing slash
            self.session = requests.Session()
        
        def create_unit(self, product_id, serial_number_id=None, mac_address_id=None):
            url = f'{self.base_url}/units/create_api'
            data = {'product_id': product_id}
            if serial_number_id is not None:
                data['serial_number'] = serial_number_id
            if mac_address_id is not None:
                data['mac_address'] = mac_address_id
            response = self.session.post(url, json=data)
            response.raise_for_status()
            unit = response.json()
            unit_id = unit["id"]
            return unit_id

        def get_products(self, name):
            url = f'{self.base_url}/products/json'
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        
        def get_next_serial(self, product_id):
            unit_id = None
            serial_number_str = None
            url = f"{self.base_url}/units/next_serial"
            create_unit_response = self.session.post(url, params={"product_id": product_id})
            create_unit_response.raise_for_status()
            
            unit = create_unit_response.json()
            unit_id = unit["id"]
            serial_number_str = unit["serial_number"]["serial_number"]
            
            print(f"Created new unit with Serial Number: {serial_number_str}, Unit ID: {unit_id}")

            return unit_id, serial_number_str
        
        def get_unit_by_serial(self, serial_number):
            unit_id = None

            url = f"{self.base_url}/units/by_serial/{serial_number}"
            get_unit_response = self.session.get(url)
            # get_unit_response.raise_for_status()

            if get_unit_response.status_code == 200:
                unit = get_unit_response.json()
                unit_id = unit["id"]
                print(f"Serial number {serial_number} exists. Unit ID: {unit_id}")
            else:
                print(f"Serial number does not exists.")
            
            return unit_id

        # Add more methods as needed for other endpoints

    return APIClient(api_url)
