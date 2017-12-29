import hashlib
import logging
import os
from uuid import uuid4

from proton import ConnectionException, Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

from xqa.commons import configuration
from xqa.commons.xqa_messaging_handler import XqaMessagingHandler
from xqa.storage.storage_service import StorageService


class Shard(XqaMessagingHandler):
    def __init__(self):
        MessagingHandler.__init__(self)
        self._stopping = False
        shard_id = str(uuid4()).split('-')[0]
        self._insert_uuid = '%s.%s' % (configuration.queue_shard_insert_uuid, shard_id)

        logging.info('%s - %s' % (self.__class__.__name__, shard_id))
        self._storage_service = StorageService()

    def on_start(self, event):
        connection = event.container.connect(configuration.url_amqp)

        self.size_receiver = event.container.create_receiver(connection, configuration.topic_shard_size)
        self.size_sender = event.container.create_sender(connection, None)

        self.insert_uuid_receiver = event.container.create_receiver(connection, self._insert_uuid)

        self.xquery_receiver = event.container.create_receiver(connection, configuration.topic_shard_xquery)
        self.xquery_sender = event.container.create_sender(connection, None)

        self.cmd_stop_receiver = event.container.create_receiver(connection, configuration.topic_cmd_stop)

        logging.debug('receivers up')

    def on_message(self, event):
        if configuration.topic_shard_size in event.message.address:
            self._size(event)
            return

        if self._insert_uuid in event.message.address:
            self._insert(event)
            return

        if configuration.topic_shard_xquery in event.message.address:
            self._xquery(event)
            return

        if configuration.topic_cmd_stop in event.message.address:
            self._cmd_stop(event)
            return

    def _size(self, event):
        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s',
                     '>',
                     event.message.creation_time,
                     event.message.correlation_id,
                     event.message.address,
                     event.message.reply_to)

        message = Message(address=event.message.reply_to,
                          correlation_id=event.message.correlation_id,
                          reply_to=self._insert_uuid,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds(),
                          body=self._storage_service.storage_size())

        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; body=%s',
                     '<',
                     message.creation_time,
                     message.correlation_id,
                     message.address,
                     message.reply_to,
                     message.body)

        self.size_sender.send(message)

    def _insert(self, event):
        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; sha256(body)=%s',
                     '>',
                     event.message.creation_time,
                     event.message.correlation_id,
                     event.message.address,
                     event.message.reply_to,
                     hashlib.sha256(event.message.body).hexdigest())

        if os.getenv('XQA_WRITE_FOLDER', default=None):
            with open('%s/%s.%s' % (os.getenv('XQA_WRITE_FOLDER'), event.message.correlation_id, hashlib.sha256(event.message.body).hexdigest()), 'w') as f:
                f.write(event.message.body.decode('utf-8'))

        self._storage_service.storage_insert(event.message.body.decode('utf-8'),
                                             event.message.correlation_id,
                                             hashlib.sha256(event.message.body).hexdigest())

    def _xquery(self, event):
        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; body=%s',
                     '>',
                     event.message.creation_time,
                     event.message.correlation_id,
                     event.message.address,
                     event.message.reply_to,
                     event.message.body)

        message = Message(address=event.message.reply_to,
                          correlation_id=event.message.correlation_id,
                          creation_time=XqaMessagingHandler.now_timestamp_seconds(),
                          body=self._storage_service.storage_xquery(event.message.body))

        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; body=%s',
                     '<',
                     message.creation_time,
                     message.correlation_id,
                     message.address,
                     message.reply_to,
                     message.body)

        self.xquery_sender.send(message)

    def _cmd_stop(self, event):
        self._storage_service.storage_terminate()
        super()._cmd_stop(event)


if __name__ == '__main__':
    try:
        Container(Shard()).run()
    except (ConnectionException, KeyboardInterrupt) as exception:
        pass
