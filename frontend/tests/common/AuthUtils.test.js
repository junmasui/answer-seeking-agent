import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getAuthorization } from '@/common/AuthUtils'
import { authService } from '@/common/AuthService'

// Mock AuthService
vi.mock('@/common/AuthService', () => ({
  authService: {
    getUser: vi.fn()
  }
}))

describe('AuthUtils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should return Bearer token when user is valid', async () => {
    authService.getUser.mockResolvedValue({
      expired: false,
      access_token: 'fake-token'
    })

    const authHeader = await getAuthorization()
    expect(authHeader).toBe('Bearer fake-token')
  })

  it('should return null when user is null', async () => {
    authService.getUser.mockResolvedValue(null)

    const authHeader = await getAuthorization()
    expect(authHeader).toBeNull()
  })

  it('should return null when user is expired', async () => {
    authService.getUser.mockResolvedValue({
      expired: true,
      access_token: 'fake-token'
    })

    const authHeader = await getAuthorization()
    expect(authHeader).toBeNull()
  })

  it('should return null when access_token is missing', async () => {
    authService.getUser.mockResolvedValue({
      expired: false,
      access_token: null
    })

    const authHeader = await getAuthorization()
    expect(authHeader).toBeNull()
  })
})
