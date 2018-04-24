import datetime
import logging

from proton import ConnectionException
from proton.handlers import MessagingHandler
from proton.reactor import Backoff


class XqaMessagingHandler(MessagingHandler):
    class XqaBackoff(Backoff):
        def __init__(self):
            self.delay = 1

    def __init__(self):
        MessagingHandler.__init__(self)
        self.retry_attempts = 0

    @staticmethod
    def now_timestamp_seconds():
        return (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds()

    def _cmd_stop(self, event):
        self._stopping = True
        event.connection.close()
        logging.info("EXIT")
        exit(0)

    def on_transport_error(self, event):
        self.retry_attempts += 1
        if self.retry_attempts == 10:
            logging.error('Unable to connect to message_broker_host')
            raise ConnectionException(event.transport.condition.description)
        super()
