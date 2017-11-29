import datetime
import logging

from proton import ConnectionException
from proton.handlers import MessagingHandler


class XqaMessagingHandler(MessagingHandler):
    @staticmethod
    def now_timestamp_seconds():
        return (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds()

    def _cmd_stop(self, event):
        self._stopping = True
        event.connection.close()
        logging.info("EXIT")
        exit(0)

    def on_transport_error(self, event):
        logging.error('%s: %s' % (event.type, event.transport.condition.description))
        raise ConnectionException(event.transport.condition.description)
