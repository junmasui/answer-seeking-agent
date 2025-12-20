/**
 * This file contains shared, application-wide constants.
 */

// Safety margin in seconds to subtract from the access token's expiry time.
// This ensures that the token is refreshed before it actually expires.
export const ACCESS_TOKEN_EXPIRY_BUFFER_SECONDS = 30
