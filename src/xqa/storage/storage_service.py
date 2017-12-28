import hashlib
import logging
import os
import signal
from subprocess import Popen, PIPE

import psutil

from org.basex.examples.api import BaseXClient
from xqa.commons import configuration


class StorageService:
    def __init__(self, cp=os.path.join(os.path.dirname(__file__), 'BaseX867.jar')):
        self._cp = cp
        self._kill_any_prior_process()
        self._server_create()
        self._session_open()
        self._database_create()
        self._database_open()

    def _kill_any_prior_process(self):
        for process in psutil.process_iter():
            for arg in process.cmdline():
                if 'BaseX867.jar' in arg:
                    process.kill()
                    return

    def _server_create(self):
        self._basex = Popen(
            'java -cp %s -Dorg.basex.MAINMEM=true -Dorg.basex.path=/tmp org.basex.BaseXServer -S -z' % self._cp,
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
        self._session = BaseXClient.Session(configuration.storage_host,
                                            configuration.storage_port,
                                            configuration.storage_user,
                                            configuration.storage_password)

    def _database_create(self):
        logging.debug('CREATE DB %s' % configuration.storage_database_name)
        self._session.execute('CREATE DB %s' % configuration.storage_database_name)

    def _database_reset(self):
        logging.debug('DROP DB %s' % configuration.storage_database_name)
        self._session.execute('DROP DB %s' % configuration.storage_database_name)

    def _database_open(self):
        logging.debug('OPEN %s' % configuration.storage_database_name)
        self._session.execute('OPEN %s' % configuration.storage_database_name)

    def storage_insert(self, xml, correlation_id, sha256):
        self._session.add(configuration.storage_database_name, xml)
        process = psutil.Process(os.getpid())
        mem = process.memory_percent()
        logging.info('correlation_id=%s; sha256=%s; size=%d; memory_percent=%f' % (correlation_id, sha256, self.storage_size(), mem))

    def storage_size(self):
        return int(self._session.execute('xquery count(/)'))

    def storage_xquery(self, xquery):
        logging.info('xquery=%s' % xquery)
        return self._session.execute('xquery %s' % xquery)
