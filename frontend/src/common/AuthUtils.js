import { authService } from './AuthService'

export async function getAuthorization() {
    const user = await authService.getUser()
    if (user && user.access_token) {
        return `Bearer ${user.access_token}`
    }
    return null
}
