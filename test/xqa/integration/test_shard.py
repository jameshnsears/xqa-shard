import hashlib
import logging
import os
import subprocess
from time import sleep
from uuid import uuid4

import pytest
from proton import Message, ConnectionException
from proton._handlers import MessagingHandler
from proton.reactor import Container

from xqa.commons import configuration
from xqa.commons.xqa_messaging_handler import XqaMessagingHandler


class IngestBalancerTest(XqaMessagingHandler):
    def __init__(self):
        XqaMessagingHandler.__init__(self)
        MessagingHandler.__init__(self)

        logging.info(self.__class__.__name__)
        self._stopping = False

        self._cmd_test_size_queue = 'queue://xqa.test.size'
        self._size_test_response_received = False
        self._cmd_test_xquery_queue = 'queue://xqa.test.xquery'
        self._xquery_test_response_received = False

        self._test_xquery_correlation_id = None

    def on_start(self, event):
        message_broker_url = 'amqp://%s:%s@%s:%s/' % (configuration.message_broker_user,
                                                      configuration.message_broker_password,
                                                      configuration.message_broker_host,
                                                      configuration.message_broker_port_amqp)
        connection = event.container.connect(message_broker_url)
        self.container = event.reactor

        self.cmd_test_size_sender = event.container.create_sender(connection, self._cmd_test_size_queue)
        self.cmd_test_size_receiver = event.container.create_receiver(connection, self._cmd_test_size_queue)

        self.cmd_test_xquery_sender = event.container.create_sender(connection, self._cmd_test_xquery_queue)
        self.cmd_test_xquery_receiver = event.container.create_receiver(connection, self._cmd_test_xquery_queue)

        self.shard_size_sender = event.container.create_sender(connection,
                                                               configuration.message_broker_shard_size_topic)
        self.shard_size_receiver = event.container.create_receiver(self.shard_size_sender.connection, None,
                                                                   dynamic=True)

        self.shard_xquery_sender = event.container.create_sender(connection,
                                                                 configuration.message_broker_shard_xquery_topic)
        self.shard_xquery_receiver = event.container.create_receiver(self.shard_xquery_sender.connection, None,
                                                                     dynamic=True)

        self.cmd_stop_sender = event.container.create_sender(connection, configuration.message_broker_cmd_stop_topic)
        self.cmd_stop_receiver = event.container.create_receiver(connection,
                                                                 configuration.message_broker_cmd_stop_topic)

        self.container.schedule(1, self)

    def _cmd_test_xquery(self):
        self._test_xquery_correlation_id = str(uuid4())
        message = Message(address=self._cmd_test_xquery_queue,
                          correlation_id=self._test_xquery_correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds())
        self.cmd_test_xquery_sender.send(message)

    def _cmd_test_size(self):
        message = Message(address=self._cmd_test_size_queue,
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
        message = Message(address=configuration.message_broker_shard_size_topic,
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
        if self._cmd_test_size_queue in event.message.address or self._cmd_test_xquery_queue in event.message.address:
            logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s, body=%s',
                         "T",
                         event.message.creation_time,
                         event.message.correlation_id,
                         event.message.address,
                         event.message.reply_to,
                         event.message.expiry_time,
                         event.message.body)

        if self._cmd_test_xquery_queue in event.message.address:
            self._xquery(event)
            return

        if event.message.correlation_id == self._test_xquery_correlation_id:
            self._xquery_response(event)
            return

        if self._cmd_test_size_queue in event.message.address:
            self._size(event)
            return

        if event.message.reply_to and configuration.message_broker_shard_insert_uuid_queue in event.message.reply_to:
            self._insert(event)
            return

        if configuration.message_broker_cmd_stop_topic in event.message.address:
            self._cmd_stop(event)
            return

    def _xquery(self, event):
        message = Message(address=configuration.message_broker_shard_xquery_topic,
                          correlation_id=event.message.correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds(),
                          reply_to=self.shard_xquery_receiver.remote_source.address,
                          body='/copyrightStatement/text()')

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

        assert '© Bodleian Libraries, University of Oxford' in event.message.body

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
                          subject='a/b/c.xml',
                          body='<copyrightStatement>© Bodleian Libraries, University of Oxford</copyrightStatement>'.encode(
                              'UTF-8'))

        logging.info(
            '%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; subject=%s; expiry_time=%s; digest(body)=%s',
            "<",
            message.creation_time,
            message.correlation_id,
            message.address,
            message.reply_to,
            message.subject,
            message.expiry_time,
            hashlib.sha256(message.body).hexdigest())

        self.shard_size_sender.send(message)

        self._size_test_response_received = True

    def _send_cmd_stop(self):
        message = Message(address=configuration.message_broker_cmd_stop_topic,
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


@pytest.fixture
def dockerpy():
    return [{'image': 'jameshnsears/xqa-message-broker:latest',
             'name': 'xqa-message-broker',
             'ports': {'%d/tcp' % configuration.message_broker_port_amqp: configuration.message_broker_port_amqp,
                       '8161/tcp': 8161},
             'network': 'xqa'},
            ]


@pytest.mark.timeout(120)
def test_shard(dockerpy):
    subprocess.Popen([
        'python3',
        os.path.join(os.path.dirname(__file__), '../../../src/xqa/shard.py'),
        '-message_broker_host', '0.0.0.0'])
    sleep(2)

    try:
        Container(IngestBalancerTest()).run()
    except (ConnectionException, KeyboardInterrupt) as exception:
        logging.error(exception)
        exit(-1)
