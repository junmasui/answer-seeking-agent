"""Provides JWT (JSON Web Token) authentication and authorization for OIDC."""

import logging
from typing import Optional

import httpx
import jwt
from jwt.exceptions import InvalidTokenError, PyJWTError

from ..app_config import get_app_config
from .error import raise_credentials_error
from .models import User

logger = logging.getLogger(__name__)

# Cache keys in memory
_JWKS_CACHE = {}


class JWKSClient:
    """Client to fetch and cache JSON Web Key Set from OIDC Provider."""

    def __init__(self):
        self.config = get_app_config()
        self.jwks_url = self.config.oidc_jwks_url
        if not self.jwks_url:
            # Infer JWKS URL from Issuer if not explicitly set
            issuer = self.config.oidc_issuer
            if issuer:
                if issuer.endswith('/'):
                    issuer = issuer[:-1]
                # Standard OIDC discovery path
                self.discovery_url = f'{issuer}/.well-known/openid-configuration'
            else:
                self.discovery_url = None

    async def get_signing_key(self, kid: Optional[str]) -> Optional[jwt.PyJWK]:
        """Retrieve the signing key from the JWKS cache or fetch it."""
        if not kid:
            return None

        if kid in _JWKS_CACHE:
            return _JWKS_CACHE[kid]

        await self._refresh_jwks()

        return _JWKS_CACHE.get(kid)

    async def _refresh_jwks(self):
        """Fetch JWKS and update cache."""
        url = self.jwks_url
        if not url and self.discovery_url:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(self.discovery_url)
                    resp.raise_for_status()
                    config = resp.json()
                    url = config.get('jwks_uri')
            except Exception as e:
                logger.error(f'Failed to discover OIDC config: {e}')
                return

        if not url:
            logger.error('No JWKS URL configured or discoverable.')
            return

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url)
                resp.raise_for_status()
                jwks = resp.json()

                # Parse keys into PyJWK objects
                public_keys = {}
                for key_data in jwks.get('keys', []):
                    # Skip encryption keys, we only need signing keys
                    if key_data.get('use') == 'enc':
                        logger.debug(f'Skipping encryption key {key_data.get("kid")}')
                        continue

                    try:
                        py_jwk = jwt.PyJWK(key_data)
                        public_keys[key_data['kid']] = py_jwk
                    except Exception as e:
                        logger.warning(f'Failed to parse JWK: {e}')

                _JWKS_CACHE.update(public_keys)
                logger.info(f'Refreshed JWKS, cached {len(public_keys)} keys.')

        except Exception as e:
            logger.error(f'Failed to fetch JWKS from {url}: {e}')


_jwks_client = JWKSClient()


async def _decode_token_data(token: str) -> Optional[User]:
    """Decode and validate OIDC JWT token."""
    try:
        # 1. Get unverified header to find key ID (kid)
        header = jwt.get_unverified_header(token)
        kid = header.get('kid')

        # 2. Get signing key
        key = await _jwks_client.get_signing_key(kid)
        if not key:
            logger.warning(f'Unknown key ID: {kid}')
            raise_credentials_error('Bearer')

        # 3. Verify signature and claims
        config = get_app_config()

        # public_key property returns the RSA public key
        issuers = [config.oidc_issuer]
        if config.oidc_extra_issuers:
            issuers.extend(config.oidc_extra_issuers)

        payload = jwt.decode(token, key.key, algorithms=['RS256'], audience=config.oidc_audience, issuer=issuers)

        # 4. Extract user info
        userid: str = payload.get('sub')

        # Flatten roles/scopes
        # OIDC standard 'scope' is space separated string
        # Keycloak puts roles in realm_access.roles or resource_access
        scopes = []
        if 'scope' in payload:
            scopes.extend(payload['scope'].split(' '))

        # Map Realm Roles if present (Keycloak specific but common)
        realm_access = payload.get('realm_access', {})
        if 'roles' in realm_access:
            scopes.extend(realm_access['roles'])

        if userid is None:
            raise_credentials_error('Bearer')

        return User(userid=userid, scopes=scopes)

    except (InvalidTokenError, PyJWTError) as e:
        logger.warning(f'Invalid token: {e}. Token header: {jwt.get_unverified_header(token)}')
        try:
            # Try to decode without verification to see what's inside for debugging
            logger.warning(f'Failed token payload: {jwt.decode(token, options={"verify_signature": False})}')
        except:
            pass
        raise_credentials_error('Bearer')
    except Exception as e:
        logger.error(f'Token validation error: {e}')
        raise_credentials_error('Bearer')

    return None


async def get_current_user_from_token(token: str):
    """Extract and validate user information from a JWT token."""
    if not token:
        return None

    user = await _decode_token_data(token)

    if user is None:
        raise_credentials_error('Bearer')
    return user
