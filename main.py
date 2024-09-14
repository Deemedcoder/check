import json
import requests
from pysnmp.hlapi import *

# API URL
url = "http://localhost:81/test-soft/api.php"

try:
    # Send a GET request to the API
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Convert the response to a dictionary using .json()
        data = response.json()
        print("Type of data:", type(data))
        print("API Response Data (as a dictionary):")
       # print(data)  # This will print the dictionary
    else:
        # Handle unsuccessful response
        print(f"Failed to get data. Status code: {response.status_code}")
        print(f"Response Body: {response.text}")

except Exception as e:
    # Handle any exceptions during the request
    print(f"An error occurred: {e}")

# SNMP GET function
def snmp_get(ip, port, community, *oids):
    try:
        object_types = [ObjectType(ObjectIdentity(oid)) for oid in oids]
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community, mpModel=1),  # SNMP v2c (mpModel=1)
                   UdpTransportTarget((ip, port)),
                   ContextData(),
                   *object_types
                   ))

        if errorIndication:
            print(f"Error Indication: {errorIndication}")
            return [None] * len(oids)
        elif errorStatus:
            print(f"Error Status: {errorStatus.prettyPrint()} at {errorIndex}")
            return [None] * len(oids)
        else:
            return [varBind[1].prettyPrint() for varBind in varBinds]

    except Exception as e:
        print(f"Exception in SNMP GET: {e}")
        return [None] * len(oids)

# Function to process the data and query SNMP
def process_data_and_query_snmp(data_dict):
    result = {}

    # Ensure that 'data_dict' is a dictionary
    if not isinstance(data_dict, dict):
        raise ValueError("Expected 'data_dict' to be a dictionary.")

    # Iterate over each device in the dictionary
    for hostname, device_data in data_dict.items():
        # Ensure that 'device_data' is a dictionary
        if not isinstance(device_data, dict):
            print(f"Expected a dictionary for device data: {device_data}")
            continue

        # Extract connection details and OID definitions
        ip = device_data.get("ip")
        port = device_data.get("port", 161)  # Default to 161 if not provided
        community = device_data.get("community_string")
        oids_str = device_data.get("oids")
        print(oids_str)

       

        # Convert OID string into a dictionary
        try:
            oids_dict = json.loads(oids_str)
        except json.JSONDecodeError as e:
            print(f"Error decoding OID string: {e}")
            continue

        oids = list(oids_dict.keys())

        # Get SNMP values using the provided snmp_get function
        snmp_values = snmp_get(ip, port, community, *oids)

        # Prepare the result for this device
        device_result = {}
        for oid, value in zip(oids, snmp_values):
            device_result[oids_dict[oid]] = value

        # Store the result in the final dictionary under the hostname key
        result[hostname] = device_result

    return result

# Process the data and get SNMP values
final_result = process_data_and_query_snmp(data)

# Convert the result to JSON format
json_result = json.dumps(final_result, indent=4)

# Output the final result (for debugging purposes)
print("Final Result (JSON):")
print(json_result)

# API endpoint where you want to post the result
api_url = 'http://localhost:81/test-soft/update_api.php'

# Send the POST request with the result data
headers = {'Content-Type': 'application/json'}
try:
    response = requests.post(api_url, headers=headers, data=json_result)

    # Output the API response
    print("API Response Status Code:", response.status_code)
    print("API Response Body:", response.text)
except Exception as e:
    print(f"An error occurred during the POST request: {e}")
