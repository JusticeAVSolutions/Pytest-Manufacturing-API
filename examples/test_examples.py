'''
run tests with -s --use-manufacturing-api --manufacturing-api-url http://localhost:8000/
'''
import pytest

def test_get_product_id_by_name(manufacturing_api_client):
    name = "AXIO Boundary Mic"
    id = None

    products = manufacturing_api_client.get_products(name)
    
    for product in products:
        if product["name"] == name:
            id = product["id"]
            break

    if id:
        print (f"Product ID for {name} is {id}")
    else:
        print (f"Product ID for {name} was not found")
        

    