import argparse
import datetime
import hashlib
import logging
import mimetypes
import os
import threading
import time
from uuid import uuid4

from lxml import etree
from lxml.etree import XMLSyntaxError
from proton import ConnectionException, Message
from proton.handlers import MessagingHandler
from proton.reactor import Container

from commons import configuration


class Ingester(MessagingHandler):
    class IngestException(Exception):
        def __init__(self, message=None):
            if message:
                self.message = message

    ERROR_NO_XML_FILES_FOUND = 'no XML files found'
    ERROR_FILE_MIMETYPE = 'incorrect mimetype'
    ERROR_FILE_CONTENTS_NOT_WELL_FORMED = 'file not well-formed'

    def __init__(self, path_to_xml_candidate_files):
        MessagingHandler.__init__(self)
        logging.info(self.__class__.__name__)
        self._stopping = False
        self.path_to_xml_candidate_files = path_to_xml_candidate_files

    def _find_xml_files(self):
        xml_files = []

        for root, _, filenames in os.walk(self.path_to_xml_candidate_files):
            for filename in filenames:
                path_to_filename = self._full_path_to_file(root, filename)
                if self._can_file_be_used(path_to_filename, filename):
                    contents_of_file = self._contents_of_file(path_to_filename)
                    logging.info(path_to_filename)
                    xml_files.append(path_to_filename)

        if not xml_files:
            logging.warning(Ingester.ERROR_NO_XML_FILES_FOUND)
            raise Ingester.IngestException(Ingester.ERROR_NO_XML_FILES_FOUND)

        return sorted(xml_files)

    def _full_path_to_file(self, root, filename):
        return os.path.join(root, filename)

    def _can_file_be_used(self, path_to_filename, filename):
        if not self._check_file_mimetype_recognised(path_to_filename):
            logging.warning('%s: %s' % (Ingester.ERROR_FILE_MIMETYPE, filename))
            return False

        if not self._check_file_contents_well_formed(path_to_filename):
            logging.warning('%s: %s' % (Ingester.ERROR_FILE_CONTENTS_NOT_WELL_FORMED, filename))
            return False

        return True

    def _check_file_contents_well_formed(self, path_to_filename):
        try:
            etree.parse(path_to_filename)
            return True
        except XMLSyntaxError:
            return False

    def _check_file_mimetype_recognised(self, path_to_filename):
        if mimetypes.guess_type(path_to_filename) in [('application/xml', None), ('text/xml', None)]:
            return True
        return False

    def _contents_of_file(self, xml_file):
        with open(xml_file) as f:
            return f.read()

    def on_start(self, event):
        connection = event.container.connect(configuration.url_amqp)

        self.ingest_sender = event.container.create_sender(connection, configuration.queue_ingest)

        self.cmd_stop_receiver = event.container.create_receiver(connection, configuration.topic_cmd_stop)
        self.cmd_stop_sender = event.container.create_sender(connection)

        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def on_message(self, event):
        if configuration.topic_cmd_stop in event.message.address:
            self._cmd_stop(event)

    def _run(self):
        time.sleep(1)
        try:
            self._send_ingest_messages(self._find_xml_files())
        except Ingester.IngestException:
            pass
        finally:
            # time.sleep(5)
            # self._send_cmd_stop()
            pass

    def _send_ingest_messages(self, xml_files):
        sent_count = 0
        for xml_file in xml_files:
            body = self._contents_of_file(xml_file)

            message = Message(address=configuration.queue_ingest,
                              correlation_id=str(uuid4()),
                              creation_time=self._now_timestamp_seconds(),
                              body=body.encode('utf-8'))

            sent_count += 1
            logging.info('%s,%3s: creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s; sha256(body)=%s',
                         ">",
                         sent_count,
                         message.creation_time,
                         message.correlation_id,
                         message.address,
                         message.reply_to,
                         message.expiry_time,
                         hashlib.sha256(message.body).hexdigest())

            self.ingest_sender.send(message)

    def _now_timestamp_seconds(self):
        return (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds()

    def _cmd_stop(self, event):
        self._stopping = True

        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s; body=%s',
                     ">",
                     event.message.creation_time,
                     event.message.correlation_id,
                     event.message.address,
                     event.message.reply_to,
                     event.message.expiry_time,
                     event.message.body)

        event.connection.close()
        logging.info("EXIT")
        exit(0)

    def _send_cmd_stop(self, event=None):
        m = Message(address=configuration.topic_cmd_stop,
                    correlation_id=str(uuid4()),
                    creation_time=self._now_timestamp_seconds())

        logging.debug('%s creation_time=%s; correlation_id=%s; address=%s; reply_to=%s; expiry_time=%s; body=%s',
                     "<",
                     m.creation_time,
                     m.correlation_id,
                     m.address,
                     m.reply_to,
                     m.expiry_time,
                     m.body)

        self.cmd_stop_sender.send(m)

    def on_transport_error(self, event):
        logging.error('%s: %s' % (event.type, event.transport.condition.description))
        raise ConnectionException(event.transport.condition.description)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path', required=True,
                        help='path to folder containing xml files')
    args = parser.parse_args()

    try:
        Container(Ingester(args.path)).run()
    except (ConnectionException, KeyboardInterrupt):
        exit(-1)
