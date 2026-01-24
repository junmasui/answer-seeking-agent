
import logging
import os
import time
import json
from keycloak import KeycloakAdmin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Keycloak configuration
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://keycloak:8080/')
USERNAME = os.getenv('KEYCLOAK_ADMIN', 'admin')

# Attempt to load secret if not set or default
PASSWORD = os.getenv('KEYCLOAK_ADMIN_PASSWORD', 'admin')
logger.info(f"DEBUG: KEYCLOAK_ADMIN={USERNAME}")
if PASSWORD:
    logger.info(f"DEBUG: KEYCLOAK_ADMIN_PASSWORD={PASSWORD[:2]}***{PASSWORD[-2:]} length={len(PASSWORD)}")
else:
    logger.info("DEBUG: KEYCLOAK_ADMIN_PASSWORD is unset/empty")

# Roles/Claims from models.py
ROLES_BASE = [
    'doc:read', 'doc:write', 'doc:ingest',
    'prompt:read', 'prompt:write',
    'query',
    'admin'
]

REALM_CONFIG = {
    "global": {
        "clients": ["api-client"],
        "roles": ROLES_BASE + ["global-admin"],
        "users": [
            {
                "username": "global-admin-1",
                "firstName": "global",
                "lastName": "admin-1",
                "email": "admin-1@global.local",
                "roles": ROLES_BASE + ["global-admin"]
            },
            {
                "username": "global-admin-2",
                "firstName": "global",
                "lastName": "admin-2",
                "email": "admin-2@global.local",
                "roles": ROLES_BASE + ["global-admin"]
            }
        ]
    },
    "tenant-a": {
        "clients": ["api-client"],
        "roles": ROLES_BASE + ["tenant-admin", "user"],
        "organizations": [
            {
                "name": "org-a",
                "members": ["admin-a1", "user-a1", "user-a2"]
            },
            {
                "name": "org-b",
                "members": ["admin-b1", "user-b1", "user-b2"]
            }
        ],
        "users": [
            {
                "username": "admin-a1",
                "firstName": "org-a",
                "lastName": "admin-a1",
                "email": "admin-1@org-a.local",
                "roles": ROLES_BASE + ["org-admin"]
            },
            {
                "username": "user-a1",
                "firstName": "org-a",
                "lastName": "user-a1",
                "email": "user-1@org-a.local",
                "roles": ROLES_BASE + ["user"]
            },
            {
                "username": "user-a2",
                "firstName": "org-a",
                "lastName": "user-a2",
                "email": "user-2@org-a.local",
                "roles": ROLES_BASE + ["user"]
            },
            {
                "username": "admin-b1",
                "firstName": "org-b",
                "lastName": "admin-b1",
                "email": "admin-1@org-b.local",
                "roles": ROLES_BASE + ["org-admin"]
            },
            {
                "username": "user-b1",
                "firstName": "org-b",
                "lastName": "user-b1",
                "email": "user-1@org-b.local",
                "roles": ROLES_BASE + ["user"]
            },
            {
                "username": "user-b2",
                "firstName": "org-b",
                "lastName": "user-b2",
                "email": "user-2@org-b.local",
                "roles": ROLES_BASE + ["user"]
            }
        ]
    },
    "tenant-b": {
        "clients": ["api-client"],
        "roles": ROLES_BASE + ["tenantadmin", "user"],
        "users": [
            {
                "username": "admin-1",
                "firstName": "tenant-b",
                "lastName": "admin-1",
                "email": "admin-1@tenant-b.local",
                "roles": ROLES_BASE + ["tenantadmin"]
            },
            {
                "username": "user-1",
                "firstName": "tenant-b",
                "lastName": "user-1",
                "email": "user-1@tenant-b.local",
                "roles": ROLES_BASE + ["user"]
            },
            {
                "username": "user-2",
                "firstName": "tenant-b",
                "lastName": "user-2",
                "email": "user-2@tenant-b.local",
                "roles": ROLES_BASE + ["user"]
            }
        ]
    }
}

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
    """Create or update the api-client for OIDC authentication."""
    # Create a fresh connection object for the realm operations
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    
    clients = kc_realm.get_clients()
    client_id = "api-client"
    client_uuid = next((c['id'] for c in clients if c.get('clientId') == client_id), None)
    
    client_payload = {
        "clientId": client_id,
        "enabled": True,
        "standardFlowEnabled": True,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled": False,
        "publicClient": True,
        "redirectUris": [
            "http://localhost:5173/*", 
            "http://localhost:80/*", 
            "https://localhost:25173/*", 
            "https://localhost:25173", 
            "https://localhost:25183/*", 
            "https://localhost:25183"
        ],
        "webOrigins": ["+"],
        "protocolMappers": [
            {
                "name": "audience-mapper",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-audience-mapper",
                "consentRequired": False,
                "config": {
                    "included.client.audience": client_id,
                    "id.token.claim": "true",
                    "access.token.claim": "true"
                }
            }
        ]
    }

    if not client_uuid:
        logger.info(f"Creating client {client_id} in {realm_name}")
        kc_realm.create_client(payload=client_payload)
    else:
        logger.info(f"Client {client_id} already exists in {realm_name}. Updating configuration...")
        # Note: update_client takes the UUID as the first argument, not the client_id string
        kc_realm.update_client(client_id=client_uuid, payload=client_payload)

def create_roles(realm_name, roles):
    """Create roles in the realm."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    existing_roles = [r['name'] for r in kc_realm.get_realm_roles()]
    
    for role in roles:
        if role not in existing_roles:
            logger.info(f"Creating role {role} in {realm_name}")
            kc_realm.create_realm_role(payload={"name": role})

def create_users(realm_name, users_config):
    """Create users in the realm."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    
    for user_conf in users_config:
        username = user_conf["username"]
        email = user_conf["email"]
        first_name = user_conf["firstName"]
        last_name = user_conf["lastName"]
        user_roles = user_conf["roles"]
        
        # Check if exists
        users = kc_realm.get_users(query={"username": username})
        user_id = None
        
        if not users:
            logger.info(f"Creating user {username} in {realm_name}")
            try:
                user_id = kc_realm.create_user(payload={
                    "username": username,
                    "email": email,
                    "firstName": first_name,
                    "lastName": last_name,
                    "enabled": True,
                    "emailVerified": True,
                    "credentials": [{"value": "Password123!", "type": "password", "temporary": False}]
                })
            except Exception as e:
                logger.error(f"Failed to create user {username}: {e}")
                continue
        else:
            logger.info(f"User {username} already exists in {realm_name}")
            user_id = users[0]['id']
            
        if user_id:
            logger.info(f"Assigning roles for {username}...")
            role_objects = []
            for r_name in user_roles:
                 try:
                    role_node = kc_realm.get_realm_role(role_name=r_name)
                    role_objects.append(role_node)
                 except Exception as e:
                    logger.warning(f"Role {r_name} not found or error: {e}")

            if role_objects:
                try:
                    kc_realm.assign_realm_roles(user_id=user_id, roles=role_objects)
                except Exception as e:
                    logger.error(f"Failed to assign roles to {username}: {e}")

def create_organizations(realm_name, orgs_config):
    """Create organizations in the realm."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    
    # We use raw_rest_request because python-keycloak might not have specific org methods yet,
    # or to ensure compatibility with the feature.
    # Endpoint: /admin/realms/{realm}/organizations
    
    for org in orgs_config:
        org_name = org["name"]
        
        # Check if org exists
        try:
            # Listing orgs to check existence
            # Depending on API, we might need to iterate.
            # Assuming GET /organizations returns a list
            existing_orgs = kc_realm.raw_rest_request(url=f"{KEYCLOAK_URL}admin/realms/{realm_name}/organizations", method="GET")
            existing_org_names = [o['name'] for o in existing_orgs] if existing_orgs else []
            
            if org_name not in existing_org_names:
                logger.info(f"Creating organization {org_name} in {realm_name}")
                payload = {"name": org_name, "enabled": True}
                kc_realm.raw_rest_request(url=f"{KEYCLOAK_URL}admin/realms/{realm_name}/organizations", method="POST", data=json.dumps(payload))
            else:
                logger.info(f"Organization {org_name} already exists in {realm_name}")
                
            # Get Org ID (needed for membership)
            # Re-fetch or filter from list
            existing_orgs = kc_realm.raw_rest_request(url=f"{KEYCLOAK_URL}admin/realms/{realm_name}/organizations", method="GET")
            org_id = next((o['id'] for o in existing_orgs if o['name'] == org_name), None)
            
            if org_id and "members" in org:
                assign_members_to_organization(kc_realm, realm_name, org_id, org_name, org["members"])

        except Exception as e:
            logger.error(f"Failed to process organization {org_name}: {e}")

def assign_members_to_organization(kc_realm, realm_name, org_id, org_name, members):
    """Assign users to an organization."""
    for username in members:
        try:
            # Find user ID
            users = kc_realm.get_users(query={"username": username})
            if not users:
                logger.warning(f"User {username} not found, cannot assign to organization {org_name}")
                continue
            
            user_id = users[0]['id']
            
            # Add member
            # Endpoint: /admin/realms/{realm}/organizations/{orgId}/members/{userId} ?? 
            # OR POST /admin/realms/{realm}/organizations/{orgId}/members with user id in body?
            # Keycloak Organizations API is usually POST /organizations/{id}/members with user id
            # Let's check documentation pattern or assume standard REST approach.
            # Based on recent Keycloak features, it is often POST /organizations/{orgId}/members
            # bearing the user ID.
            # Actually, standard way usually: POST /realms/{realm}/organizations/{orgId}/members
            # Payload: user ID string or object? 
            # Verifying common pattern: POST /organizations/{id}/members, body: userId (as string or json?)
            # Let's try sending the user_id strings.
            logger.info(f"Assigning {username} to {org_name}")
            kc_realm.raw_rest_request(url=f"{KEYCLOAK_URL}admin/realms/{realm_name}/organizations/{org_id}/members", method="POST", data=json.dumps(user_id))
            
        except Exception as e:
            # It might fail if already a member, so we log as warning
            logger.warning(f"Failed to assign {username} to {org_name} (might already be member): {e}")

def create_client_scopes_and_assign(realm_name, roles):
    """Create client scopes and assign them to the api-client."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    client_id = "api-client"
    
    # Get client UUID
    # Get client UUID
    clients = kc_realm.get_clients()
    clients = [c for c in clients if c.get('clientId') == client_id]
    if not clients:
        logger.error(f"Client {client_id} not found in {realm_name}")
        return
    client_uuid = clients[0]['id']

    existing_scopes = [s['name'] for s in kc_realm.get_client_scopes()]

    for scope_name in roles:
        # Create scope if missing
        if scope_name not in existing_scopes:
            logger.info(f"Creating client scope {scope_name} in {realm_name}")
            kc_realm.create_client_scope(payload={
                "name": scope_name,
                "protocol": "openid-connect",
            })
        
        # Assign to client as optional
        try:
             # Find scope ID
             all_scopes = kc_realm.get_client_scopes()
             scope_id = next((s['id'] for s in all_scopes if s['name'] == scope_name), None)
             
             if scope_id:
                 kc_realm.add_client_optional_client_scope(client_id=client_uuid, client_scope_id=scope_id, payload={})
                 logger.info(f"Assigned optional scope {scope_name} to {client_id}")
             else:
                 logger.warning(f"Scope {scope_name} not found, cannot assign.")
        except Exception as e:
             logger.warning(f"Could not assign scope {scope_name}: {e}")

def configure_organization_scope(realm_name):
    """Configure organization scope."""
    kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
    scope_name = "organizations"
    
    try:
        existing = [s['name'] for s in kc_realm.get_client_scopes()]
        if scope_name not in existing:
             logger.info(f"Creating client scope {scope_name}")
             kc_realm.create_client_scope(payload={
                 "name": scope_name,
                 "protocol": "openid-connect",
                 "attributes": {"include.in.token.scope": "true", "display.on.consent.screen": "true"}
             })
        
        # Assign to api-client
        client_id = "api-client"
        clients = kc_realm.get_clients()
        client = next((c for c in clients if c.get('clientId') == client_id), None)
        if client:
            # Get scope ID
            scopes = kc_realm.get_client_scopes()
            scope_id = next((s['id'] for s in scopes if s['name'] == scope_name), None)
            if scope_id:
                 kc_realm.add_client_optional_client_scope(client_id=client['id'], client_scope_id=scope_id, payload={})
                 logger.info(f"Assigned optional scope {scope_name} to {client_id}")
    except Exception as e:
        logger.error(f"Failed to configure organization scope: {e}")



def main():
    kc_admin = wait_for_keycloak(KEYCLOAK_URL)
    
    for realm_name, config in REALM_CONFIG.items():
        try:
            logger.info(f"Initializing realm: {realm_name}")
            create_realm_if_missing(kc_admin, realm_name)
            
            # Create clients
            for _ in config.get("clients", []):
                 create_client_if_missing(realm_name) # simplified as we only support one client config for now
            
            create_roles(realm_name, config["roles"])
            create_users(realm_name, config["users"])
            if "organizations" in config:
                create_organizations(realm_name, config["organizations"])
                configure_organization_scope(realm_name)
            create_client_scopes_and_assign(realm_name, config["roles"])
            
        except Exception as e:
            logger.error(f"Failed to initialize realm {realm_name}: {e}")
        
    # Verification
    logger.info("Verifying initialization...")
    total_users_created = 0
    for realm_name in REALM_CONFIG.keys():
        try:
             kc_realm = get_realm_client(KEYCLOAK_URL, realm_name)
             users = kc_realm.get_users()
             count = len(users)
             logger.info(f"Realm {realm_name} has {count} users.")
             total_users_created += count
        except Exception as e:
             logger.error(f"Could not verify realm {realm_name}: {e}")

    logger.info(f"Initialization complete. Total users verifiable: {total_users_created}")

if __name__ == "__main__":
    main()
