import { useCurrentUserStore } from './CurrentUserStore'
import { storeToRefs } from 'pinia'
import { ACCESS_TOKEN_EXPIRY_BUFFER_SECONDS } from './AppConstants'

export async function getAuthorization() {
  const currentUserStore = useCurrentUserStore()
  const { signedIn, accessToken, refreshToken, refreshAccessAfter } = storeToRefs(currentUserStore)

  if (signedIn.value) {
    const now = new Date()
    const refreshDate = refreshAccessAfter.value ? new Date(refreshAccessAfter.value) : null

    if (refreshDate && now > refreshDate) {
      try {
        const formData = new FormData()
        formData.append('refresh_token', refreshToken.value)

        const response = await fetch('/api/sim_auth/refresh', {
          method: 'POST',
          body: formData
        })

        if (!response.ok) {
          throw new Error(`Token refresh failed: ${response.statusText}`)
        }

        const data = await response.json()

        accessToken.value = data.access_token
        refreshToken.value = data.refresh_token
        const expiresIn = data.expires_in
        const newNow = new Date()
        // 30-second safety window
        refreshAccessAfter.value = new Date(
          newNow.getTime() + (expiresIn - ACCESS_TOKEN_EXPIRY_BUFFER_SECONDS) * 1000
        )
      } catch (error) {
        console.error('Failed to refresh access token:', error)
        // Sign out
        accessToken.value = ''
        refreshToken.value = ''
        refreshAccessAfter.value = null
        signedIn.value = false
        return null
      }
    }
    return `Bearer ${accessToken.value}`
  }

  return null
}
