package com.sleekydz86.backend.global.exception

class StockNotFoundException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)

class InvalidSymbolException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)

class ExternalApiException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)

class DataProcessingException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)

class WebSocketException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)

class CircuitBreakerOpenException(message: String? = null) :
    RuntimeException(message)

class RateLimitExceededException(message: String? = null) :
    RuntimeException(message)

class AuthenticationException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)

class AuthorizationException(message: String? = null, cause: Throwable? = null) :
    RuntimeException(message, cause)
