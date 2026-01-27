import { describe, it, expect, vi, beforeEach } from 'vitest'
import logger from '@/common/Logger'
import log from 'loglevel'

// Mock loglevel
vi.mock('loglevel', () => ({
    default: {
        setLevel: vi.fn(),
        debug: vi.fn(),
        info: vi.fn(),
        warn: vi.fn(),
        error: vi.fn(),
    },
}))

describe('Logger', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('should format message with timestamp and context', () => {
        const message = 'Test message'
        const context = { key: 'value' }
        // We can't easily assert the exact timestamp, but we can check the structure
        // Accessing internal method for testing logic if possible, or just checking the output passed to loglevel

        logger.info(message, context)

        expect(log.info).toHaveBeenCalledTimes(1)
        const calledArg = log.info.mock.calls[0][0]
        expect(calledArg).toContain(message)
        expect(calledArg).toContain('{"key":"value"}')
    })

    it('should call log.debug for debug level', () => {
        logger.debug('Debug msg')
        expect(log.debug).toHaveBeenCalled()
    })

    it('should call log.info for info level', () => {
        logger.info('Info msg')
        expect(log.info).toHaveBeenCalled()
    })

    it('should call log.warn for warn level', () => {
        logger.warn('Warn msg')
        expect(log.warn).toHaveBeenCalled()
    })

    it('should call log.error for error level', () => {
        logger.error('Error msg')
        expect(log.error).toHaveBeenCalled()
    })

    it('should include error details in error log', () => {
        const error = new Error('Something went wrong')
        logger.error('Error msg', error)

        expect(log.error).toHaveBeenCalled()
        const calledArg = log.error.mock.calls[0][0]
        expect(calledArg).toContain('Something went wrong') // Error message should be in context
    })

    it('apiSuccess should log info', () => {
        logger.apiSuccess('fetchUsers', { count: 10 })
        expect(log.info).toHaveBeenCalled()
        const calledArg = log.info.mock.calls[0][0]
        expect(calledArg).toContain('API Success: fetchUsers')
    })

    it('apiError should log error', () => {
        const err = new Error('404 Not Found')
        logger.apiError('fetchUsers', err)
        expect(log.error).toHaveBeenCalled()
        const calledArg = log.error.mock.calls[0][0]
        expect(calledArg).toContain('API Error: fetchUsers')
    })
})
