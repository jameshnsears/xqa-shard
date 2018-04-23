import hashlib
import os
from uuid import uuid4

from xqa.storage.storage_service import StorageService


def test_storage_service():
    try:
        storage_service = StorageService()
        xml_file = os.path.join(os.path.dirname(__file__), '../resources/test-data/eapb_mon_14501A_033.xml')
        xml_in = open(xml_file, encoding='utf-8').read()
        storage_service.storage_add(xml_in, xml_file)

        assert 1 == storage_service.storage_size()

        assert 'contentType=\"monograph\"' == storage_service.storage_xquery('/book/@contentType')

        xml_out = storage_service.storage_xquery("/")
        assert hashlib.sha256(xml_out.encode('utf-8')).hexdigest() == hashlib.sha256(xml_in.encode('utf-8')).hexdigest()
    except AssertionError as e:
        open(xml_file, 'w').write(xml_out)
        raise e
    finally:
        storage_service.storage_terminate()
