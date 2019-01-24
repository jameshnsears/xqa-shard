import hashlib
import os

from xqa.storage.storage_service import StorageService


def test_storage_service():
    try:
        storage_service = StorageService()
        xml_file = os.path.join(os.path.dirname(__file__), '../../resources/test-data/eapb_mon_14501A_033.xml')
        xml_in = open(xml_file, encoding='utf-8').read()
        storage_service.storage_add(xml_in, xml_file)

        assert storage_service.storage_size() == 1
        assert storage_service.storage_xquery('count(/)') == '1'
        assert storage_service.storage_xquery('/book/@contentType') == 'contentType=\"monograph\"'

        xml_out = storage_service.storage_xquery("/")
        assert hashlib.sha256(xml_out.encode('utf-8')).hexdigest() == hashlib.sha256(xml_in.encode('utf-8')).hexdigest()
    # except AssertionError as e:
    #     open(xml_file, 'w').write(xml_out)
    #     raise e
    finally:
        storage_service.storage_terminate()


def test_invalid_xquery_syntax():
    try:
        storage_service = StorageService()
        assert storage_service.storage_xquery('blah') == StorageService.NO_RESULT_FROM_XQUERY
        assert storage_service.storage_xquery("'XQueryRequest('count(/)'") == StorageService.INVALID_XQUERY_SYNTAX_XPST0003
    finally:
        storage_service.storage_terminate()
