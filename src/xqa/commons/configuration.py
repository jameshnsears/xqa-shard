import logging
import socket
import sys

url_amqp = 'amqp://admin:admin@%s:5672/' % socket.gethostbyname(socket.gethostname())

topic_cmd_stop = 'topic://xqa.cmd.stop'

topic_shard_size = 'topic://xqa.shard.size'

queue_shard_insert_uuid = 'queue://xqa.shard.insert'

topic_shard_xquery = 'topic://xqa.shard.xquery'

storage_host = '127.0.0.1'
storage_port = 1984
storage_user = 'admin'
storage_password = 'admin'
storage_database_name = 'xqa'

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format="%(asctime)s  %(levelname)8s --- [%(threadName)20s]: %(funcName)25s, %(lineno)3s: %(message)s")
