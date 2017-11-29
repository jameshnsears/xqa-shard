import hashlib
import logging
from uuid import uuid4

from proton import ConnectionException, Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

from xqa.commons import configuration
from xqa.commons.xqa_messaging_handler import XqaMessagingHandler


class IngestBalancerTest(XqaMessagingHandler):
    def __init__(self):
        MessagingHandler.__init__(self)
        logging.info(self.__class__.__name__)
        self._stopping = False

        self._queue_cmd_test_size = 'queue://xqa.test.size'
        self._size_test_response_received = False
        self._queue_cmd_test_xquery = 'queue://xqa.test.xquery'
        self._xquery_test_response_received = False

        self._test_xquery_correlation_id = None

    def on_start(self, event):
        connection = event.container.connect(configuration.url_amqp)

        self.cmd_test_size_sender = event.container.create_sender(connection, self._queue_cmd_test_size)
        self.cmd_test_size_receiver = event.container.create_receiver(connection, self._queue_cmd_test_size)

        self.cmd_test_xquery_sender = event.container.create_sender(connection, self._queue_cmd_test_xquery)
        self.cmd_test_xquery_receiver = event.container.create_receiver(connection, self._queue_cmd_test_xquery)

        self.shard_size_sender = event.container.create_sender(connection, configuration.topic_shard_size)
        self.shard_size_receiver = event.container.create_receiver(self.shard_size_sender.connection, None,
                                                                   dynamic=True)

        self.shard_xquery_sender = event.container.create_sender(connection, configuration.topic_shard_xquery)
        self.shard_xquery_receiver = event.container.create_receiver(self.shard_xquery_sender.connection, None,
                                                                     dynamic=True)

        self.cmd_stop_sender = event.container.create_sender(connection, configuration.topic_cmd_stop)
        self.cmd_stop_receiver = event.container.create_receiver(connection, configuration.topic_cmd_stop)

        self.container = event.reactor
        self.container.schedule(1, self)

    def _cmd_test_xquery(self):
        self._test_xquery_correlation_id = str(uuid4())
        message = Message(address=self._queue_cmd_test_xquery,
                          correlation_id=self._test_xquery_correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds())
        self.cmd_test_xquery_sender.send(message)

    def _cmd_test_size(self):
        message = Message(address=self._queue_cmd_test_size,
                          correlation_id=str(uuid4()),
                          creation_time=XqaMessagingHandler.now_timestamp_seconds())
        self.cmd_test_size_sender.send(message)

    def on_timer_task(self, event):
        if not self._size_test_response_received:
            self._cmd_test_size()

        elif self._size_test_response_received and not self._xquery_test_response_received:
            self._cmd_test_xquery()

        elif self._size_test_response_received and self._xquery_test_response_received:
            self._send_cmd_stop()

        self.container.schedule(1, self)

    def _size(self, event):
        message = Message(address=configuration.topic_shard_size,
                          correlation_id=event.message.correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds(),
                          reply_to=self.shard_size_receiver.remote_source.address)

        self.shard_size_sender.send(message)

        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s; body=%s',
                     "<",
                     message.creation_time,
                     message.correlation_id,
                     message.address,
                     message.reply_to,
                     message.expiry_time,
                     message.body)

    def on_message(self, event):
        if self._queue_cmd_test_size in event.message.address or self._queue_cmd_test_xquery in event.message.address:
            logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s, body=%s',
                         "T",
                         event.message.creation_time,
                         event.message.correlation_id,
                         event.message.address,
                         event.message.reply_to,
                         event.message.expiry_time,
                         event.message.body)

        if self._queue_cmd_test_xquery in event.message.address:
            self._xquery(event)
            return

        if event.message.correlation_id == self._test_xquery_correlation_id:
            self._xquery_response(event)
            return

        if self._queue_cmd_test_size in event.message.address:
            self._size(event)
            return

        if event.message.reply_to and configuration.queue_shard_insert_uuid in event.message.reply_to:
            self._insert(event)
            return

        if configuration.topic_cmd_stop in event.message.address:
            self._cmd_stop(event)
            return

    def _xquery(self, event):
        message = Message(address=configuration.topic_shard_xquery,
                          correlation_id=event.message.correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds(),
                          reply_to=self.shard_xquery_receiver.remote_source.address,
                          body='/a/text()')

        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s; body=%s',
                     "<",
                     message.creation_time,
                     message.correlation_id,
                     message.address,
                     message.reply_to,
                     message.expiry_time,
                     message.body)

        self.shard_xquery_sender.send(message)

    def _xquery_response(self, event):
        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s, body=%s',
                     ">",
                     event.message.creation_time,
                     event.message.correlation_id,
                     event.message.address,
                     event.message.reply_to,
                     event.message.expiry_time,
                     event.message.body)

        assert event.message.body == 'b'

        self._xquery_test_response_received = True

    def _insert(self, event):
        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s, body=%s',
                     ">",
                     event.message.creation_time,
                     event.message.correlation_id,
                     event.message.address,
                     event.message.reply_to,
                     event.message.expiry_time,
                     event.message.body)

        message = Message(address=event.message.reply_to,
                          correlation_id=event.message.correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds(),
                          body='<a>b</a>'.encode('utf-8'))

        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s; sha256(body)=%s',
                     "<",
                     message.creation_time,
                     message.correlation_id,
                     message.address,
                     message.reply_to,
                     message.expiry_time,
                     hashlib.sha256(message.body).hexdigest())

        self.shard_size_sender.send(message)

        self._size_test_response_received = True

    def _send_cmd_stop(self):
        message = Message(address=configuration.topic_cmd_stop,
                          correlation_id=str(uuid4()),
                          creation_time=XqaMessagingHandler.now_timestamp_seconds())

        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s',
                     "<",
                     message.creation_time,
                     message.correlation_id,
                     message.address,
                     message.reply_to,
                     message.expiry_time)

        self.cmd_stop_sender.send(message)


if __name__ == "__main__":
    try:
        Container(IngestBalancerTest()).run()
    except (ConnectionException, KeyboardInterrupt):
        pass
