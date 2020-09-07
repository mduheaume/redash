from collections import namedtuple
from unittest import TestCase

from redash.utils import (
    build_url,
    collect_parameters_from_request,
    filter_none,
    json_dumps,
    generate_token,
    update_query_hash,
)
from tests import BaseTestCase


DummyRequest = namedtuple("DummyRequest", ["host", "scheme"])


class TestBuildUrl(TestCase):
    def test_simple_case(self):
        self.assertEqual(
            "http://example.com/test",
            build_url(DummyRequest("", "http"), "example.com", "/test"),
        )

    def test_uses_current_request_port(self):
        self.assertEqual(
            "http://example.com:5000/test",
            build_url(DummyRequest("example.com:5000", "http"), "example.com", "/test"),
        )

    def test_uses_current_request_schema(self):
        self.assertEqual(
            "https://example.com/test",
            build_url(DummyRequest("example.com", "https"), "example.com", "/test"),
        )

    def test_skips_port_for_default_ports(self):
        self.assertEqual(
            "https://example.com/test",
            build_url(DummyRequest("example.com:443", "https"), "example.com", "/test"),
        )
        self.assertEqual(
            "http://example.com/test",
            build_url(DummyRequest("example.com:80", "http"), "example.com", "/test"),
        )
        self.assertEqual(
            "https://example.com:80/test",
            build_url(DummyRequest("example.com:80", "https"), "example.com", "/test"),
        )
        self.assertEqual(
            "http://example.com:443/test",
            build_url(DummyRequest("example.com:443", "http"), "example.com", "/test"),
        )


class TestCollectParametersFromRequest(TestCase):
    def test_ignores_non_prefixed_values(self):
        self.assertEqual({}, collect_parameters_from_request({"test": 1}))

    def test_takes_prefixed_values(self):
        self.assertDictEqual(
            {"test": 1, "something_else": "test"},
            collect_parameters_from_request({"p_test": 1, "p_something_else": "test"}),
        )


class TestSkipNones(TestCase):
    def test_skips_nones(self):
        d = {"a": 1, "b": None}

        self.assertDictEqual(filter_none(d), {"a": 1})


class TestJsonDumps(TestCase):
    def test_handles_binary(self):
        self.assertEqual(json_dumps(memoryview(b"test")), '"74657374"')


class TestGenerateToken(TestCase):
    def test_format(self):
        token = generate_token(40)
        self.assertRegex(token, r"[a-zA-Z0-9]{40}")


class TestUpdateQueryHash(BaseTestCase):
    def test_update_query_hash_basesql_with_options(self):
        ds = self.factory.create_data_source(
            group=self.factory.org.default_group, type="databricks"
        )
        query = self.factory.create_query(query_text="SELECT 2", data_source=ds)
        query.options = {"apply_auto_limit": True}
        origin_hash = query.query_hash
        update_query_hash(query)
        self.assertNotEqual(origin_hash, query.query_hash)

    def test_update_query_hash_basesql_no_options(self):
        ds = self.factory.create_data_source(
            group=self.factory.org.default_group, type="databricks"
        )
        query = self.factory.create_query(query_text="SELECT 2", data_source=ds)
        query.options = {}
        origin_hash = query.query_hash
        update_query_hash(query)
        self.assertEqual(origin_hash, query.query_hash)

    def test_update_query_hash_non_basesql(self):
        ds = self.factory.create_data_source(
            group=self.factory.org.default_group, type="druid"
        )
        query = self.factory.create_query(query_text="SELECT 2", data_source=ds)
        query.options = {"apply_auto_limit": True}
        origin_hash = query.query_hash
        update_query_hash(query)
        self.assertEqual(origin_hash, query.query_hash)
