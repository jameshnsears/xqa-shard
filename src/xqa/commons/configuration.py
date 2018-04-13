import logging
import socket
import sys

message_broker_host = socket.gethostbyname(socket.gethostname())
message_broker_port = 5672
message_broker_user = 'admin'
message_broker_password = 'admin'
message_broker_topic_cmd_stop = 'topic://xqa.cmd.stop'
message_broker_topic_shard_size = 'topic://xqa.shard.size'
message_broker_queue_shard_insert_uuid = 'queue://xqa.shard.insert'
message_broker_topic_shard_xquery = 'topic://xqa.shard.xquery'
message_broker_queue_db_amqp_insert_event = 'queue://xqa.event'

storage_host = '127.0.0.1'
storage_port = 1984
storage_user = 'admin'
storage_password = 'admin'
storage_database_name = 'xqa'

logging.basicConfig(stream=sys.stdout,
                    level=logging.INFO,
                    format="%(asctime)s  %(levelname)8s --- [%(threadName)20s]: %(funcName)25s, %(lineno)3s: %(message)s")
