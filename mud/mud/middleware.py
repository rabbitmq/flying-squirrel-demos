import logging
log = logging.getLogger(__name__)

class LoggingMiddleware:
    def process_exception(self, request, exc):
        log.error("Exception:", exc_info=True)
        return None
