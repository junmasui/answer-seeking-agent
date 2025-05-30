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
  /**
   * Logs a debug message with optional context information.
   * @param {string} message - The debug message to log
   * @param {Object} context - Additional context data to include with the message
   */
  debug(message, context = {}) {
    log.debug(this.formatMessage(message, context))
  }

  /**
   * Logs an informational message with optional context information.
   * @param {string} message - The info message to log
   * @param {Object} context - Additional context data to include with the message
   */
  info(message, context = {}) {
    log.info(this.formatMessage(message, context))
  }

  /**
   * Logs a warning message with optional context information.
   * @param {string} message - The warning message to log
   * @param {Object} context - Additional context data to include with the message
   */
  warn(message, context = {}) {
    log.warn(this.formatMessage(message, context))
  }

  /**
   * Logs an error message with optional error object and context information.
   * @param {string} message - The error message to log
   * @param {Error|null} error - The error object to extract details from
   * @param {Object} context - Additional context data to include with the message
   */
  error(message, error = null, context = {}) {
    const errorContext = error ? { ...context, error: error.message, stack: error.stack } : context
    log.error(this.formatMessage(message, errorContext))
  }

  // Helper method to format messages with context
  /**
   * Formats a log message with timestamp and context information.
   * @param {string} message - The message to format
   * @param {Object} context - Context data to append to the message
   * @returns {string} The formatted message string
   */
  formatMessage(message, context = {}) {
    const timestamp = new Date().toISOString()
    const contextStr = Object.keys(context).length > 0 ? JSON.stringify(context) : ''
    return `[${timestamp}] ${message} ${contextStr}`.trim()
  }

  // Convenience methods for common use cases
  /**
   * Logs a successful API operation with optional data.
   * @param {string} operation - The name of the API operation that succeeded
   * @param {Object} data - Additional data related to the successful operation
   */
  apiSuccess(operation, data = {}) {
    this.info(`API Success: ${operation}`, data)
  }

  /**
   * Logs a failed API operation with error details and context.
   * @param {string} operation - The name of the API operation that failed
   * @param {Error} error - The error that occurred during the operation
   * @param {Object} context - Additional context data related to the failure
   */
  apiError(operation, error, context = {}) {
    this.error(`API Error: ${operation}`, error, context)
  }

  /**
   * Logs a user action with optional context information.
   * @param {string} action - The name of the user action performed
   * @param {Object} context - Additional context data related to the action
   */
  userAction(action, context = {}) {
    this.info(`User Action: ${action}`, context)
  }

  /**
   * Logs file upload progress information.
   * @param {string} fileName - The name of the file being uploaded
   * @param {string|number} progress - The current progress status or percentage
   */
  uploadProgress(fileName, progress) {
    this.debug(`Upload Progress: ${fileName}`, { progress })
  }
}

// Create singleton instance
const logger = new AppLogger()

export default logger
