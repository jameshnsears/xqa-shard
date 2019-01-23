import logging
import os
import signal
from subprocess import Popen, PIPE
from time import sleep

import psutil

from org.basex.examples.api import BaseXClient
from xqa.commons import configuration

BASEX_JAR = 'BaseX91.jar'


class StorageService:
    INVALID_XQUERY_SYNTAX = 'Invalid XQuery Syntax'
    INVALID_XQUERY_SYNTAX_XPST0003 = 'Invalid XQuery Syntax - XPST0003'

    def __init__(self, cp=os.path.join(os.path.dirname(__file__), BASEX_JAR)):
        self._cp = cp
        self._basex_jar = BASEX_JAR
        self._kill_any_prior_process()
        self._server_create()
        self._session_open()
        self._database_create()
        self._database_open()

    def _kill_any_prior_process(self):
        for process in psutil.process_iter():
            for arg in process.cmdline():
                if self._basex_jar in arg:
                    try:
                        process.kill()
                    except Exception as e:
                        logging.warning(e)
                    return

    def _server_create(self):
        self._basex = Popen(
            'java -cp %s -Dorg.basex.MAINMEM=%s -Dorg.basex.path=/tmp org.basex.BaseXServer -S -z' % 
            (self._cp, configuration.storage_mainmem),
            stdout=PIPE, stderr=PIPE, shell=True, preexec_fn=os.setsid)
        basex_stdout, basex_stderr = self._basex.communicate()
        logging.info('pid=%d; stdout=%s; stderr=%s' % (self._basex.pid, basex_stdout, basex_stderr))

    def storage_terminate(self):
        try:
            self._database_reset()
            self._session.close()
            os.killpg(self._basex.pid, signal.SIGTERM)
            logging.info('pid=%d' % self._basex.pid)
        except ProcessLookupError as e:
            logging.error(e)

    def _session_open(self):
        max_retry_attempts = 10
        retry_attempts = 1
        connected = False
        while not connected:
            try:
                self._session = BaseXClient.Session(configuration.storage_host,
                                                    configuration.storage_port,
                                                    configuration.storage_user,
                                                    configuration.storage_password)
                connected = True
            except ConnectionRefusedError as e:
                logging.info('ConnectionRefusedError: %s/%s' % (retry_attempts, max_retry_attempts))
                if retry_attempts == max_retry_attempts:
                    raise e
                retry_attempts += 1
                sleep(retry_attempts)

    def _database_create(self):
        logging.debug('CREATE DB %s' % configuration.storage_database_name)
        self._session.execute('CREATE DB %s' % configuration.storage_database_name)

    def _database_reset(self):
        logging.debug('DROP DB %s' % configuration.storage_database_name)
        self._session.execute('DROP DB %s' % configuration.storage_database_name)

    def _database_open(self):
        logging.debug('OPEN %s' % configuration.storage_database_name)
        self._session.execute('OPEN %s' % configuration.storage_database_name)

    def storage_add(self, xml, subject):
        logging.debug('START')
        self._session.add(subject, xml)
        logging.debug('END')
        process = psutil.Process(os.getpid())
        logging.info('size=%d; memory_percent=%f' % (self.storage_size(), process.memory_percent()))

    def storage_size(self):
        return int(self._session.execute('xquery count(/)'))

    def storage_xquery(self, xquery):
        logging.debug('xquery=%s' % xquery)
        try:
            xquery_response = self._session.execute('xquery %s' % xquery)
            if xquery_response == "":
                return StorageService.INVALID_XQUERY_SYNTAX
            return xquery_response
        except Exception as e:
            logging.warning(e)
            return StorageService.INVALID_XQUERY_SYNTAX_XPST0003
