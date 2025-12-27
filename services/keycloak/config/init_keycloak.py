
import logging
import os
import time
from keycloak import KeycloakAdmin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Keycloak configuration
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://keycloak:8080/')
USERNAME = os.getenv('KEYCLOAK_ADMIN', 'admin')

# Attempt to load secret if not set or default
PASSWORD = os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin')

# Tenant definitions
TENANTS = ['tenant-1', 'tenant-2']
USERS_PER_TENANT = 3
ADMINS_GLOBAL = 2

# Roles/Claims from models.py
ROLES = [
    'doc:read', 'doc:write', 'doc:ingest',
    'prompt:read', 'prompt:write',
    'query',
    'admin'
]

def wait_for_keycloak(url):
    """Wait for Keycloak to be ready."""
    logger.info(f"Waiting for Keycloak at {url}...")
    while True:
        try:
            # We don't have a health check endpoint exposed on 8080 by default in all configs,
            # but getting the auth screen or a 404 on root means it's running.
            # Using KeycloakAdmin to check connection is easiest.
            kc_admin = KeycloakAdmin(server_url=url,
                          username=USERNAME,
                          password=PASSWORD,
                          realm_name="master",
                          user_realm_name="master",
                          verify=True)
            
            # Force verification of token/connection
            logger.info("Verifying connection by fetching clients...")
            kc_admin.get_clients()
            
            logger.info("Keycloak is ready and authenticated.")
            return kc_admin
        except Exception as e:
            logger.info(f"Keycloak not ready yet: {e}")
            time.sleep(5)

def get_admin_client(url):
    return KeycloakAdmin(server_url=url,
                         username=USERNAME,
                         password=PASSWORD,
                         realm_name="master",
                         user_realm_name="master",
                         verify=True)


def get_realm_client(url, realm_name):
    """Get a KeycloakAdmin client authenticated against master but targeting a specific realm."""
    return KeycloakAdmin(server_url=url,
                         username=USERNAME,
                         password=PASSWORD,
                         realm_name=realm_name,
                         user_realm_name="master",
                         verify=True)

def create_realm_if_missing(keycloak_admin, realm_name):
    """Create a realm if it does not exist."""
    # We use the master admin for this
    keycloak_admin.realm_name = "master"
    realms = keycloak_admin.get_realms()
    existing_realms = [r['realm'] for r in realms]
    if realm_name not in existing_realms:
        logger.info(f"Creating realm: {realm_name}")
        keycloak_admin.create_realm(payload={"realm": realm_name, "enabled": True})
    else:
        logger.info(f"Realm {realm_name} already exists.")

def create_client_if_missing(realm_name):
    """Create the api-client for OIDC authentication."""
    # Create a fresh connection object for the realm operations
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    
    clients = kc_realm.get_clients()
    existing_clients = [c['clientId'] for c in clients]
    
    client_id = "api-client"
    if client_id not in existing_clients:
        logger.info(f"Creating client {client_id} in {realm_name}")
        kc_realm.create_client(payload={
            "clientId": client_id,
            "enabled": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "serviceAccountsEnabled": False,
            "publicClient": True,
            "redirectUris": ["http://localhost:5173/*", "http://localhost:80/*"],
            "webOrigins": ["+"],
        })
    else:
        logger.info(f"Client {client_id} already exists in {realm_name}")

def create_roles(realm_name):
    """Create roles in the realm."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    existing_roles = [r['name'] for r in kc_realm.get_realm_roles()]
    
    for role in ROLES:
        if role not in existing_roles:
            logger.info(f"Creating role {role} in {realm_name}")
            kc_realm.create_realm_role(payload={"name": role})

def create_users(realm_name):
    """Create users in the realm."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    
    # Create 3 users
    for i in range(1, USERS_PER_TENANT + 1):
        username = f"user{i}"
        user_email = f"user{i}@{realm_name}.local"
        
        # Check if exists
        users = kc_realm.get_users(query={"username": username})
        if not users:
            logger.info(f"Creating user {username} in {realm_name}")
            new_user_id = kc_realm.create_user(payload={
                "username": username,
                "email": user_email,
                "enabled": True,
                "emailVerified": True,
                "credentials": [{"value": "password", "type": "password", "temporary": False}]
            })
            
            role_objects =[]
            for r_name in ROLES:
                if r_name != 'admin':
                     role_node = kc_realm.get_realm_role(role_name=r_name)
                     role_objects.append(role_node)
            
            kc_realm.assign_realm_roles(user_id=new_user_id, roles=role_objects)
        else:
            logger.info(f"User {username} already exists in {realm_name}")

def create_global_admins(keycloak_admin):
    """Create global admins in the master realm."""
    keycloak_admin.realm_name = "master"
    for i in range(1, ADMINS_GLOBAL + 1):
        username = f"globaladmin{i}"
        
        users = keycloak_admin.get_users(query={"username": username})
        if not users:
            logger.info(f"Creating global admin {username}")
            keycloak_admin.create_user(payload={
                "username": username,
                "enabled": True,
                "emailVerified": True,
                "credentials": [{"value": "adminpassword", "type": "password", "temporary": False}]
            })
            # Assign admin role? 
            # In master realm, usually 'admin' role provides console access.
        else:
            logger.info(f"Global admin {username} already exists")

def main():
    kc_admin = wait_for_keycloak(KEYCLOAK_URL)
    
    # Global Admins
    create_global_admins(kc_admin)
    
    for tenant in TENANTS:
        create_realm_if_missing(kc_admin, tenant)
        # Use explicit realm clients for the rest
        create_client_if_missing(tenant)
        create_roles(tenant)
        create_users(tenant)
        
    logger.info("Initialization complete.")

if __name__ == "__main__":
    main()
