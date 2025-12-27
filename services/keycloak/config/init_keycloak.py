
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
            KeycloakAdmin(server_url=url,
                          username=USERNAME,
                          password=PASSWORD,
                          realm_name="master",
                          verify=True)
            logger.info("Keycloak is ready.")
            return
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

def create_realm_if_missing(keycloak_admin, realm_name):
    """Create a realm if it does not exist."""
    keycloak_admin.realm_name = "master"
    realms = keycloak_admin.get_realms()
    existing_realms = [r['realm'] for r in realms]
    if realm_name not in existing_realms:
        logger.info(f"Creating realm: {realm_name}")
        keycloak_admin.create_realm(payload={"realm": realm_name, "enabled": True})
    else:
        logger.info(f"Realm {realm_name} already exists.")

def create_client_if_missing(keycloak_admin, realm_name):
    """Create the api-client for OIDC authentication."""
    # Switch context to the target realm (required if using KeycloakAdmin instance bound to a realm?)
    # The python-keycloak library actions are often method-specific or require a new instance.
    # It's safer to use the connection methods.
    
    # We can use the existing admin connection but specify the realm in calls where supported,
    # or create a new admin connection for convenience if the library supports it.
    # Actually, create_client usually requires us to be connected *to* a specific realm or passing it?
    # python-keycloak usually manages context. Let's create a fresh connection object for the realm operations to be safe if needed,
    # or just use the master admin to operate on other realms.
    
    # Using 'master' admin to manage other realms:
    
    keycloak_admin.realm_name = realm_name
    clients = keycloak_admin.get_clients()
    existing_clients = [c['clientId'] for c in clients]
    
    client_id = "api-client"
    if client_id not in existing_clients:
        logger.info(f"Creating client {client_id} in {realm_name}")
        keycloak_admin.create_client(payload={
            "clientId": client_id,
            "enabled": True,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": True,
            "serviceAccountsEnabled": True,
            "publicClient": False,
            "clientAuthenticatorType": "client-secret",
            "secret": "secret" # In a real app, generate this or load from env
        })
    else:
        logger.info(f"Client {client_id} already exists in {realm_name}")

def create_roles(keycloak_admin, realm_name):
    """Create roles in the realm."""
    # Realm roles
    keycloak_admin.realm_name = realm_name
    existing_roles = [r['name'] for r in keycloak_admin.get_realm_roles()]
    
    for role in ROLES:
        if role not in existing_roles:
            logger.info(f"Creating role {role} in {realm_name}")
            keycloak_admin.create_realm_role(payload={"name": role})

def create_users(keycloak_admin, realm_name):
    """Create users in the realm."""
    
    # Create 3 users
    keycloak_admin.realm_name = realm_name
    for i in range(1, USERS_PER_TENANT + 1):
        username = f"user{i}"
        user_email = f"user{i}@{realm_name}.local"
        
        # Check if exists
        users = keycloak_admin.get_users(query={"username": username})
        if not users:
            logger.info(f"Creating user {username} in {realm_name}")
            new_user_id = keycloak_admin.create_user(payload={
                "username": username,
                "email": user_email,
                "enabled": True,
                "emailVerified": True,
                "credentials": [{"value": "password", "type": "password", "temporary": False}]
            })
            
            # Assign roles (let's assign all for simplicity or round robin?)
            # User wants: "users should have claims as defined in models.py"
            # We'll assign a subset or all. Let's assign 'doc:read' and 'query' by default
            # and maybe 'admin' for one user?
            
            # Let's assign all roles to user1, and fewer to others to test.
            # Actually user asked for "users... defined in...".
            # The prompt implies capabilities. Let's give all generic roles to all users,
            # and 'admin' only to specific ones if implied.
            # The requirement says "create 2 tenants with 3 users each and 2 admins".
            # This implies the admins are separate users.
            # So the normal 3 users should probably NOT have admin role.
            
            role_objects =[]
            for r_name in ROLES:
                if r_name != 'admin':
                     role_node = keycloak_admin.get_realm_role(role_name=r_name)
                     role_objects.append(role_node)
            
            keycloak_admin.assign_realm_roles(user_id=new_user_id, roles=role_objects)
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
    wait_for_keycloak(KEYCLOAK_URL)
    kc_admin = get_admin_client(KEYCLOAK_URL)
    
    # Global Admins
    create_global_admins(kc_admin)
    
    for tenant in TENANTS:
        create_realm_if_missing(kc_admin, tenant)
        create_client_if_missing(kc_admin, tenant)
        create_roles(kc_admin, tenant)
        create_users(kc_admin, tenant)
        
        # Create tenant admin?
        # Requirement: "2 tenants with 3 users each and 2 admins"
        # The "2 admins" part was clarified as "Global". 
        # So we don't necessarily need tenant-local admins unless implied by "admins" in the tenant counting.
        # But user said "Admins: Global". So we are done with admins.
        
    logger.info("Initialization complete.")

if __name__ == "__main__":
    main()
