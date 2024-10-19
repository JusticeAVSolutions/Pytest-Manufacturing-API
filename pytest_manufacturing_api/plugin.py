# conftest.py
import pytest
import requests

# Add a custom marker attribute so that pytest sequencer picks it up
__pytest_sequencer_plugin__ = True

def pytest_addoption(parser):
    parser.addoption(
        "--api-url",
        action="store",
        default="http://192.168.114.187:8000/",
        help="Manufacturing API URL"
    )
    parser.addoption(
        "--use-manufacturing-api",
        action="store_true",
        default=False,
        help="Utilize database for serial numbering and logging test results"
    )

@pytest.fixture(scope='session')
def api_client(request):
    """Provides an API client for interacting with the REST API."""
    use_api = request.config.getoption("--use-manufacturing-api")
    api_url = request.config.getoption("--api-url")

    if not use_api:
        pytest.skip("Manufacturing API not enabled. Use --use-manufacturing-api to enable.")

    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url.rstrip('/')  # Ensure no trailing slash
            self.session = requests.Session()

        def create_product(self, name, uses_serial=False, uses_mac=False):
            url = f'{self.base_url}/products/create'
            data = {
                'name': name,
                'uses_serial': str(uses_serial).lower(),
                'uses_mac': str(uses_mac).lower()
            }
            response = self.session.post(url, data=data)
            response.raise_for_status()
            return response.json()

        def create_serial_number(self, product_id, serial_number):
            url = f'{self.base_url}/serial_numbers/create'
            data = {
                'product_id': product_id,
                'serial_number': serial_number
            }
            response = self.session.post(url, data=data)
            response.raise_for_status()
            return response.json()

        def create_mac_address(self, product_id, mac_address):
            url = f'{self.base_url}/mac_addresses/create'
            data = {
                'product_id': product_id,
                'mac_address': mac_address
            }
            response = self.session.post(url, data=data)
            response.raise_for_status()
            return response.json()

        def create_unit(self, product_id, serial_number_id=None, mac_address_id=None):
            url = f'{self.base_url}/units/create'
            data = {'product_id': product_id}
            if serial_number_id is not None:
                data['serial_number_id'] = serial_number_id
            if mac_address_id is not None:
                data['mac_address_id'] = mac_address_id
            response = self.session.post(url, data=data)
            response.raise_for_status()
            return response.json()

        def log_test_result(self, unit_id, test_data):
            url = f'{self.base_url}/test_results/create'
            files = {'test_data_text': (None, test_data)}
            data = {'unit_id': unit_id}
            response = self.session.post(url, data=data, files=files)
            response.raise_for_status()
            return response.json()

        def get_unit(self, unit_id):
            url = f'{self.base_url}/units/{unit_id}/json'
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()

        # Add more methods as needed for other endpoints

    return APIClient(api_url)
