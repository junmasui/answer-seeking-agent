import log from 'loglevel'

// Configure loglevel based on environment
if (import.meta.env.PROD) {
  // In production, only show warnings and errors
  log.setLevel('warn')
} else {
  // In development, show everything
  log.setLevel('trace')
}

// Check for URL parameter override (useful for debugging production builds)
const urlParams = new URLSearchParams(window.location.search)
if (urlParams.get('debug') === 'true') {
  log.setLevel('trace')
}

// Create a logger wrapper with convenience methods
class AppLogger {
  // Basic log methods (these map directly to loglevel)
  debug(message, context = {}) {
    log.debug(this.formatMessage(message, context))
  }

  info(message, context = {}) {
    log.info(this.formatMessage(message, context))
  }

  warn(message, context = {}) {
    log.warn(this.formatMessage(message, context))
  }

  error(message, error = null, context = {}) {
    const errorContext = error ? { ...context, error: error.message, stack: error.stack } : context
    log.error(this.formatMessage(message, errorContext))
  }

  // Helper method to format messages with context
  formatMessage(message, context = {}) {
    const timestamp = new Date().toISOString()
    const contextStr = Object.keys(context).length > 0 ? JSON.stringify(context) : ''
    return `[${timestamp}] ${message} ${contextStr}`.trim()
  }

  // Convenience methods for common use cases
  apiSuccess(operation, data = {}) {
    this.info(`API Success: ${operation}`, data)
  }

  apiError(operation, error, context = {}) {
    this.error(`API Error: ${operation}`, error, context)
  }

  userAction(action, context = {}) {
    this.info(`User Action: ${action}`, context)
  }

  uploadProgress(fileName, progress) {
    this.debug(`Upload Progress: ${fileName}`, { progress })
  }
}

// Create singleton instance
const logger = new AppLogger()

export default logger