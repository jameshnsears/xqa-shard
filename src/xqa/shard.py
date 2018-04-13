import argparse
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
        XqaMessagingHandler.__init__(self)
        MessagingHandler.__init__(self)
        self._stopping = False
        uuid = str(uuid4()).split('-')[0]
        self._service_id = '%s/%s' % (self.__class__.__name__.lower(), uuid)
        self._insert_uuid = '%s.%s' % (configuration.message_broker_queue_shard_insert_uuid, uuid)

        logging.info(self._service_id)
        logging.debug('-message_broker_host=%s' % configuration.message_broker_host)

        self._storage_service = StorageService()

    def on_start(self, event):
        message_broker_url = 'amqp://%s:%s@%s:%s/' % (configuration.message_broker_user,
                                                      configuration.message_broker_password,
                                                      configuration.message_broker_host,
                                                      configuration.message_broker_port)
        connection = event.container.connect(message_broker_url, reconnect=XqaMessagingHandler.XqaBackoff())

        self.size_receiver = event.container.create_receiver(connection, configuration.message_broker_topic_shard_size)
        self.size_sender = event.container.create_sender(connection, None)

        self.insert_uuid_receiver = event.container.create_receiver(connection, self._insert_uuid)

        self.xquery_receiver = event.container.create_receiver(connection,
                                                               configuration.message_broker_topic_shard_xquery)
        self.xquery_sender = event.container.create_sender(connection, None)

        self.cmd_stop_receiver = event.container.create_receiver(connection,
                                                                 configuration.message_broker_topic_cmd_stop)

        self.insert_event_sender = event.container.create_sender(connection,
                                                                 configuration.message_broker_queue_db_amqp_insert_event)

        logging.debug('receivers up')

    def on_message(self, event):
        if configuration.message_broker_topic_shard_size in event.message.address:
            self._size(event)
            return

        if self._insert_uuid in event.message.address:
            self._insert(event)
            return

        if configuration.message_broker_topic_shard_xquery in event.message.address:
            self._xquery(event)
            return

        if configuration.message_broker_topic_cmd_stop in event.message.address:
            self._cmd_stop(event)
            return

    def _size(self, event):
        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s',
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
        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; subject=%s; digest(body)=%s',
                      '>',
                      event.message.creation_time,
                      event.message.correlation_id,
                      event.message.address,
                      event.message.reply_to,
                      event.message.subject,
                      hashlib.sha256(event.message.body).hexdigest())

        if os.getenv('XQA_WRITE_FOLDER', default=None):
            with open('%s/%s.%s' % (os.getenv('XQA_WRITE_FOLDER'), event.message.correlation_id,
                                    hashlib.sha256(event.message.body).hexdigest()), 'w') as f:
                f.write(event.message.body.decode('utf-8'))

        self._insert_event(event.message, "START")
        self._storage_service.storage_add(event.message.body.decode('utf-8'),
                                          event.message.correlation_id,
                                          event.message.subject,
                                          hashlib.sha256(event.message.body).hexdigest())
        self._insert_event(event.message, "END")

    def _insert_event(self, message, state):
        creation_time = XqaMessagingHandler.now_timestamp_seconds()

        insert_event = """{ "serviceId": "%s", "creationTime": %s, "correlationId": "%s", "digest": "%s", "state": "%s" }""" % \
                       (self._service_id,
                        self._standardise_creation_time_with_other_servics(creation_time),
                        message.correlation_id,
                        hashlib.sha256(message.body).hexdigest(),
                        state)

        message = Message(address=configuration.message_broker_queue_db_amqp_insert_event,
                          correlation_id=str(uuid4()),
                          creation_time=creation_time,
                          body=insert_event.encode('utf-8'))

        self.insert_event_sender.send(message)

    def _standardise_creation_time_with_other_servics(self, creation_time):
        if '.' in str(creation_time):
            creation_time = str(creation_time).replace('.', '')
        return creation_time.ljust(9, '0')[:13]

    def _xquery(self, event):
        logging.info('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; body=%s',
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
    parser = argparse.ArgumentParser()
    parser.add_argument('-message_broker_host', '--message_broker_host', required=True,
                        help='i.e. xqa-message-broker')
    args = parser.parse_args()
    configuration.message_broker_host = args.message_broker_host

    try:
        Container(Shard()).run()
    except (ConnectionException, KeyboardInterrupt) as exception:
        logging.error(exception)
        exit(-1)
