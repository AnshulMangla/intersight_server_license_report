from intersight.api import chassis_api, power_api, snmp_api, thermal_api, organization_api
from intersight.model.organization_organization_relationship import OrganizationOrganizationRelationship
from intersight.model.chassis_profile import ChassisProfile
from intersight.model.power_policy import PowerPolicy
from intersight.model.snmp_policy import SnmpPolicy
from intersight.model.thermal_policy import ThermalPolicy
from intersight.model.policy_abstract_policy_relationship import PolicyAbstractPolicyRelationship
from intersight.apis import ComputeApi
import intersight
import sys
import re


def get_api_client(api_key_id, api_secret_file = None, private_key_string = None, proxy = None, endpoint="https://intersight.com"):
    if api_secret_file is None and private_key_string is None:
        print("Either api_secret_file or private_key_string is required to create api client")
        sys.exit(1)
    if api_secret_file is not None and private_key_string is not None:
        print("Please provide only one among api_secret_file or private_key_string")
        sys.exit(1)

    if api_secret_file is not None: 
        with open(api_secret_file, 'r') as f:
            api_key = f.read()
    else:
        api_key = private_key_string

    if re.search('BEGIN RSA PRIVATE KEY', api_key):
        # API Key v2 format
        signing_algorithm = intersight.signing.ALGORITHM_RSASSA_PKCS1v15
        
    elif re.search('BEGIN EC PRIVATE KEY', api_key):
        # API Key v3 format
        signing_algorithm = intersight.signing.ALGORITHM_ECDSA_MODE_DETERMINISTIC_RFC6979
    
    configuration = intersight.Configuration(
        host=endpoint,
        signing_info=intersight.signing.HttpSigningConfiguration(
            key_id=api_key_id,
            private_key_string = api_key,
            signing_scheme=intersight.signing.SCHEME_HS2019,
            signing_algorithm=signing_algorithm,
            hash_algorithm=intersight.signing.HASH_SHA256,
            signed_headers=[
                intersight.signing.HEADER_REQUEST_TARGET,
                intersight.signing.HEADER_HOST,
                intersight.signing.HEADER_DATE,
                intersight.signing.HEADER_DIGEST,
            ]
        )
    )
    # if you want to turn off certificate verification
    configuration.verify_ssl = False

    # setting proxy
    if proxy is not None and proxy != "":
        configuration.proxy = proxy

    return intersight.ApiClient(configuration)


api_key = "api_key"
api_key_file = "secret-key.txt"

api_client = get_api_client(api_key, api_key_file)


def get_organization(organization_name = 'default'):
    # Get the organization and return OrganizationRelationship
    api_instance = organization_api.OrganizationApi(api_client)
    odata = {"filter":f"Name eq {organization_name}"}
    organizations = api_instance.get_organization_organization_list(**odata)
    if organizations.results and len(organizations.results) > 0:
        moid = organizations.results[0].moid
        print (moid);
    else:
        print("No organization was found with given name")
        sys.exit(1)
    return OrganizationOrganizationRelationship(class_id="mo.MoRef",
                                                object_type="organization.Organization",
                                                moid=moid)

def fetch_servers_with_license():
    # Use the Compute API
    compute = ComputeApi(api_client)
    response = compute.get_compute_physical_summary_list()

    licensed_servers = []
    for server in response.results:
        tags = getattr(server, 'tags', [])
        for tag in tags:
            if tag.get('key') == 'Intersight.LicenseTier':
                licensed_servers.append({
                    'name': getattr(server, 'name', 'Unknown'),
                    'license_type': tag.get('value', 'N/A')
                })
                break  # Stop after finding the license tier tag

    # Display
    print("Servers with Licenses Applied:")
    for server in licensed_servers:
        print(f"Server Name: {server['name']}, License Type: {server['license_type']}")

if __name__ == "__main__":
    get_organization()

    fetch_servers_with_license()
