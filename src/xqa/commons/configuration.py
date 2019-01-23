import logging
import sys

message_broker_host = '0.0.0.0'
message_broker_port_amqp = 5672
message_broker_user = 'admin'
message_broker_password = 'admin'
message_broker_cmd_stop_topic = 'topic://xqa.cmd.stop'
message_broker_shard_size_topic = 'topic://xqa.shard.size'
message_broker_shard_insert_uuid_queue = 'queue://xqa.shard.insert'
message_broker_shard_xquery_topic = 'topic://xqa.shard.xquery'
message_broker_db_amqp_insert_event_queue = 'queue://xqa.event'

storage_mainmem = 'false'
storage_host = '0.0.0.0'
storage_port = 1984
storage_user = 'admin'
storage_password = 'admin'
storage_database_name = 'xqa'

logging.basicConfig(stream=sys.stdout,
                    level=logging.DEBUG,
                    format="%(asctime)s.%(msecs)03d  %(levelname)8s --- [%(process)5d] %(filename)25s:%(funcName)30s, %(lineno)3s: %(message)s")

logging.getLogger('docker').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
