'''
run tests with -s --use-manufacturing-api --manufacturing-api-url http://localhost:8000/
'''
import pytest

MIC_DEFAULT_SN = "0000000000000000"

# Use pytest built-in 'request' fixture so that unit_id can be tracked for result logging
# Use pytest built-in 'record_property' fixture to log SN
def test_get_or_make_unit(request, record_property, manufacturing_api_client):
    product_name = "AXIO Boundary Mic"
    product_id = None
    unit_id = None
    serial_number_str = None

    # Determine product id based on product name
    products = manufacturing_api_client.get_products(product_name)
    for product in products:
        if product["name"] == product_name:
            product_id = product["id"]
            break
    
    # Get mic's SN to see if mic has default serial number (all 0x00's)
    # Some modbus read ...

    # Mocking that mic has default sn
    # mic_initial_sn = MIC_DEFAULT_SN

    # Mocking that mic has sn that doesn't exist in DB
    mic_initial_sn = "JP1369999998"

    # Mocking that mic has sn that exists in DB
    # mic_initial_sn = "JP1362442001"

    if mic_initial_sn == MIC_DEFAULT_SN:
        # Need to pull new SN from DB
        unit_id, serial_number_str = manufacturing_api_client.get_next_serial(product_id)
        pass
    else:
        # Check if SN exists in DB
        unit_id = manufacturing_api_client.get_unit_by_serial(mic_initial_sn)
        if unit_id == None:
            # Serial number doesn't exist in DB, create SN in DB, create a new unit and link to the SN
            unit_id = manufacturing_api_client.create_unit(product_id, mic_initial_sn)
            serial_number_str = mic_initial_sn
        else:
            # Serial number exists
            serial_number_str = mic_initial_sn
            pass

    # Tell session what the unit_id is
    request.session.unit_id = unit_id

    # Record the SN for log, label, etc
    record_property("serial number", serial_number_str)