from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import iso8601
import pytest
from aw_core.models import Event
from aw_datastore.storages import MemoryStorage
from aw_query import query
from aw_query.exceptions import (
    QueryFunctionException,
    QueryInterpretException,
    QueryParseException,
)
from aw_query.query2 import (
    QDict,
    QFunction,
    QInteger,
    QList,
    QString,
    QVariable,
    _parse_token,
)

from .utils import param_datastore_objects


class MockDatastore(MemoryStorage):
    pass


mock_ds = MockDatastore(testing=True)


def assert_token_parses_as(source: str, expected_token: str, expected_type, ns: Dict[str, Any]):
    (parsed_type, parsed_token), remainder = _parse_token(source, ns)
    assert remainder == ""
    assert parsed_token == expected_token
    assert parsed_type == expected_type


def assert_dict_parse_error(source: str, ns: Dict[str, Any]):
    with pytest.raises(QueryParseException):
        QDict.parse(source, ns)


def assert_list_parse_error(source: str, ns: Dict[str, Any]):
    with pytest.raises(QueryParseException):
        QList.parse(source, ns)


def test_query2_test_token_parsing():
    ns: Dict[str, Any] = {}
    assert_token_parses_as("123", "123", QInteger, ns)
    assert_token_parses_as('"test"', '"test"', QString, ns)
    assert_token_parses_as("'test'", "'test'", QString, ns)
    assert_token_parses_as("'te\\'st'", "'te\\'st'", QString, ns)
    assert_token_parses_as('"te\\"st"', '"te\\"st"', QString, ns)
    assert_token_parses_as("test0xDEADBEEF", "test0xDEADBEEF", QVariable, ns)
    assert_token_parses_as("test1337(')')", "test1337(')')", QFunction, ns)
    assert_token_parses_as(
        "test1337('test\\'test',\"test\\\"test\")",
        "test1337('test\\'test',\"test\\\"test\")",
        QFunction,
        ns,
    )
    assert_token_parses_as("[1, 'a', {}]", "[1, 'a', {}]", QList, ns)
    assert_token_parses_as("{'a': 1, 'b}': 2}", "{'a': 1, 'b}': 2}", QDict, ns)

    assert _parse_token("", ns) == ((None, ""), "")

    with pytest.raises(QueryParseException):
        _parse_token(None, ns)  # type: ignore

    with pytest.raises(QueryParseException):
        _parse_token('"', ns)

    with pytest.raises(QueryParseException):
        _parse_token("#", ns)


def test_dict():
    ds = mock_ds
    ns: Dict[str, Any] = {}
    parsed_dict = QDict.parse("{'a': {'a': {'a': 1}}, 'b': {'b\\'\"': ':'}}", ns)
    expected_res = {"a": {"a": {"a": 1}}, "b": {"b'\"": ":"}}
    assert expected_res == parsed_dict.interpret(ds, ns)

    # Key in dict is not a string
    assert_dict_parse_error("{b: 1}", ns)

    # Key in dict without a value
    assert_dict_parse_error("{'test': }", ns)

    # Char following key string is not a :
    assert_dict_parse_error("{'test'p 1}", ns)

    assert_dict_parse_error("{'test': #}", ns)

    # Semicolon without key
    assert_dict_parse_error("{:}", ns)

    # Trailing comma
    assert_dict_parse_error("{'test':1,}", ns)


def test_list():
    ds = mock_ds
    ns: Dict[str, Any] = {}
    parsed_list = QList.parse("[1,2,[[3],4],5]", ns)
    expected_res = [1, 2, [[3], 4], 5]
    assert expected_res == parsed_list.interpret(ds, ns)

    quoted_list = QList.parse("['\\'',\"\\\"\"]", ns)
    expected_res = ["'", '"']
    assert expected_res == quoted_list.interpret(ds, ns)

    empty_list = QList.parse("[]", ns)
    expected_res = []
    assert expected_res == empty_list.interpret(ds, ns)

    # Comma without pre/post value
    assert_list_parse_error("[,]", ns)

    # Comma without post value
    assert_list_parse_error("[1,]", ns)

    # Comma without pre value
    assert_list_parse_error("[,2]", ns)


def test_query2_bogus_query():
    ds = mock_ds
    qname = "test"
    qstartdate = datetime.now(tz=timezone.utc)
    qenddate = qstartdate

    # Nothing to assign
    with pytest.raises(QueryParseException):
        example_query = "a="
        query(qname, example_query, qstartdate, qenddate, ds)

    # Assign to non-variable
    with pytest.raises(QueryParseException):
        example_query = "1 = 2"
        query(qname, example_query, qstartdate, qenddate, ds)

    # Unclosed function
    with pytest.raises(QueryParseException):
        example_query = "a = unclosed_function(var1"
        query(qname, example_query, qstartdate, qenddate, ds)

    # Two tokens in assignment
    with pytest.raises(QueryParseException):
        example_query = "asd nop() = 2"
        query(qname, example_query, qstartdate, qenddate, ds)

    # Unclosed string
    with pytest.raises(QueryParseException):
        example_query = 'asd = "something is wrong with me'
        query(qname, example_query, qstartdate, qenddate, ds)

    # Two tokens in value
    with pytest.raises(QueryParseException):
        example_query = "asd = asd1 asd2"
        query(qname, example_query, qstartdate, qenddate, ds)


def test_query2_query_function_calling():
    ds = mock_ds
    qname = "asd"
    starttime = iso8601.parse_date("1970-01-01")
    endtime = iso8601.parse_date("1970-01-02")

    # Function which doesn't exist
    with pytest.raises(QueryInterpretException):
        example_query = "RETURN = asd();"
        query(qname, example_query, starttime, endtime, ds)

    # Function which does exist with invalid arguments
    with pytest.raises(QueryInterpretException):
        example_query = "RETURN = nop(badarg);"
        query(qname, example_query, starttime, endtime, ds)

    # Function which does exist with valid arguments
    example_query = "RETURN = nop();"
    query(qname, example_query, starttime, endtime, ds)


def test_query2_return_value():
    ds = mock_ds
    qname = "asd"
    starttime = iso8601.parse_date("1970-01-01")
    endtime = iso8601.parse_date("1970-01-02")
    example_query = "RETURN = 1;"
    result = query(qname, example_query, starttime, endtime, ds)
    assert result == 1

    example_query = "RETURN = 'testing 123'"
    result = query(qname, example_query, starttime, endtime, ds)
    assert result == "testing 123"

    example_query = "RETURN = {'a': 1}"
    result = query(qname, example_query, starttime, endtime, ds)
    assert result == {"a": 1}

    # Nothing to return
    with pytest.raises(QueryParseException):
        example_query = "a=1"
        query(qname, example_query, starttime, endtime, ds)


def test_query2_multiline():
    ds = mock_ds
    qname = "asd"
    starttime = iso8601.parse_date("1970-01-01")
    endtime = iso8601.parse_date("1970-01-02")
    example_query = """
my_multiline_string = "a
b";
RETURN = my_multiline_string;
    """
    result = query(qname, example_query, starttime, endtime, ds)
    assert result == "a\nb"


def test_query2_function_invalid_types():
    """Tests the q2_typecheck decorator"""
    ds = mock_ds
    qname = "asd"
    starttime = iso8601.parse_date("1970-01-01")
    endtime = iso8601.parse_date("1970-01-02")

    # int instead of str
    example_query = """
        events = [];
        RETURN = filter_keyvals(events, 666, ["invalid_val"]);
    """
    with pytest.raises(QueryFunctionException):
        query(qname, example_query, starttime, endtime, ds)

    # str instead of list
    example_query = """
        events = [];
        RETURN = filter_keyvals(events, "2", "invalid_val");
    """
    with pytest.raises(QueryFunctionException):
        query(qname, example_query, starttime, endtime, ds)

    # FIXME: For unknown reasons, query2 drops the second argument
    #        when the first argument is a bare []
    """
    example_query = '''
        RETURN = filter_keyvals([], "2", "invalid_val");
    '''
    with pytest.raises(QueryFunctionException) as e:
        result = query(qname, example_query, starttime, endtime, None)
    """


def test_query2_function_invalid_argument_count():
    ds = mock_ds
    qname = "asd"
    starttime = iso8601.parse_date("1970-01-01")
    endtime = iso8601.parse_date("1970-01-02")
    example_query = "RETURN=nop(nop())"
    with pytest.raises(QueryInterpretException):
        query(qname, example_query, starttime, endtime, ds)


@pytest.mark.parametrize("datastore", param_datastore_objects())
def test_query2_function_in_function(datastore):
    qname = "asd"
    bid = "test_bucket"
    starttime = iso8601.parse_date("1970-01-01")
    endtime = iso8601.parse_date("1970-01-02")
    example_query = f"""
    RETURN=limit_events(query_bucket("{bid}"), 1);
    """
    try:
        # Setup buckets
        bucket1 = datastore.create_bucket(
            bucket_id=bid, type="test", client="test", hostname="test", name="test"
        )
        # Prepare buckets
        e1 = Event(data={}, timestamp=starttime, duration=timedelta(seconds=1))
        bucket1.insert(e1)
        result = query(qname, example_query, starttime, endtime, datastore)
        assert 1 == len(result)
    finally:
        datastore.delete_bucket(bid)


@pytest.mark.parametrize("datastore", param_datastore_objects())
def test_query2_query_functions(datastore):
    """
    Just test calling all functions just to see something isn't completely broken
    In many cases the functions doesn't change the result at all, so it's not a test
    for testing the validity of the data the functions transform
    """
    bid = "test_'bucket"
    qname = "test"
    starttime = iso8601.parse_date("1970")
    endtime = starttime + timedelta(hours=1)

    example_query = """
    bid = "{bid}";
    events = query_bucket("{bid}");
    events2 = query_bucket('{bid_escaped}');
    events2 = filter_keyvals(events2, "label", ["test1"]);
    events2 = exclude_keyvals(events2, "label", ["test2"]);
    events = filter_period_intersect(events, events2);
    events = filter_keyvals_regex(events, "label", ".*");
    events = limit_events(events, 1);
    events = merge_events_by_keys(events, ["label"]);
    events = chunk_events_by_key(events, "label");
    events = split_url_events(events);
    events = sort_by_timestamp(events);
    events = sort_by_duration(events);
    events = categorize(events, [[["test", "subtest"], {{"regex": "test1"}}]]);
    duration = sum_durations(events);
    eventcount = query_bucket_eventcount(bid);
    asd = nop();
    RETURN = {{"events": events, "eventcount": eventcount}};
    """.format(
        bid=bid, bid_escaped=bid.replace("'", "\\'")
    )
    try:
        bucket = datastore.create_bucket(
            bucket_id=bid, type="test", client="test", hostname="test", name="asd"
        )
        bucket.insert(
            Event(
                data={"label": "test1"},
                timestamp=starttime,
                duration=timedelta(seconds=1),
            )
        )
        result = query(qname, example_query, starttime, endtime, datastore)
        assert result["eventcount"] == 1
        assert len(result["events"]) == 1
        assert result["events"][0].data["label"] == "test1"
        assert result["events"][0].data["$category"] == ["test", "subtest"]
    finally:
        datastore.delete_bucket(bid)


@pytest.mark.parametrize("datastore", param_datastore_objects())
def test_query2_basic_query(datastore):
    name = "A label/name for a test bucket"
    bid1 = "bucket1"
    bid2 = "bucket2"
    qname = "test_query_basic"
    starttime = iso8601.parse_date("1970")
    endtime = starttime + timedelta(hours=1)

    example_query = f"""
    bid1 = "{bid1}";
    bid2 = "{bid2}";
    events = query_bucket(bid1);
    intersect_events = query_bucket(bid2);
    RETURN = filter_period_intersect(events, intersect_events);
    """

    try:
        # Setup buckets
        bucket1 = datastore.create_bucket(
            bucket_id=bid1, type="test", client="test", hostname="test", name=name
        )
        bucket2 = datastore.create_bucket(
            bucket_id=bid2, type="test", client="test", hostname="test", name=name
        )
        # Prepare buckets
        e1 = Event(
            data={"label": "test1"}, timestamp=starttime, duration=timedelta(seconds=1)
        )
        e2 = Event(
            data={"label": "test2"},
            timestamp=starttime + timedelta(seconds=2),
            duration=timedelta(seconds=1),
        )
        et = Event(
            data={"label": "intersect-label"},
            timestamp=starttime,
            duration=timedelta(seconds=1),
        )
        bucket1.insert(e1)
        bucket1.insert(e2)
        bucket2.insert(et)
        # Query
        result = query(qname, example_query, starttime, endtime, datastore)
        # Assert
        assert len(result) == 1
        assert result[0]["data"]["label"] == "test1"
    finally:
        datastore.delete_bucket(bid1)
        datastore.delete_bucket(bid2)


@pytest.mark.parametrize("datastore", param_datastore_objects())
def test_query2_test_merged_keys(datastore):
    name = "A label/name for a test bucket"
    bid = "bucket1"
    qname = "test_query_merged_keys"
    starttime = iso8601.parse_date("2080")
    endtime = starttime + timedelta(hours=1)

    example_query = f"""
    bid1 = "{bid}";
    events = query_bucket(bid1);
    events = merge_events_by_keys(events, ["label1", "label2"]);
    events = sort_by_duration(events);
    eventcount = query_bucket_eventcount(bid1);
    RETURN = {{"events": events, "eventcount": eventcount}};
    """
    try:
        # Setup buckets
        bucket1 = datastore.create_bucket(
            bucket_id=bid, type="test", client="test", hostname="test", name=name
        )
        # Prepare buckets
        e1 = Event(
            data={"label1": "test1", "label2": "test1"},
            timestamp=starttime,
            duration=timedelta(seconds=1),
        )
        e2 = Event(
            data={"label1": "test1", "label2": "test1"},
            timestamp=starttime + timedelta(seconds=1),
            duration=timedelta(seconds=1),
        )
        e3 = Event(
            data={"label1": "test1", "label2": "test2"},
            timestamp=starttime + timedelta(seconds=2),
            duration=timedelta(seconds=1),
        )
        bucket1.insert(e3)
        bucket1.insert(e1)
        bucket1.insert(e2)
        # Query
        result = query(qname, example_query, starttime, endtime, datastore)
        # Assert
        print(result)
        assert len(result["events"]) == 2
        assert result["eventcount"] == 3
        assert result["events"][0]["data"]["label1"] == "test1"
        assert result["events"][0]["data"]["label2"] == "test1"
        assert result["events"][0]["duration"] == timedelta(seconds=2)
        assert result["events"][1]["data"]["label1"] == "test1"
        assert result["events"][1]["data"]["label2"] == "test2"
        assert result["events"][1]["duration"] == timedelta(seconds=1)
    finally:
        datastore.delete_bucket(bid)


@pytest.mark.parametrize("datastore", param_datastore_objects())
def test_query2_fancy_query(datastore):
    """
    Tests:
     - find_bucket
     - simplify_window_titles
    """
    name = "A label/name for a test bucket"
    bid1 = "bucket-the-one"
    qname = "test_query_basic_fancy"
    starttime = iso8601.parse_date("1970")
    endtime = starttime + timedelta(hours=1)

    example_query = f"""
    bid = find_bucket("{bid1[:10]}");
    events = query_bucket(bid);
    RETURN = simplify_window_titles(events, "title");
    """

    try:
        # Setup buckets
        bucket_main = datastore.create_bucket(
            bucket_id=bid1, type="test", client="test", hostname="test", name=name
        )
        # Prepare buckets
        e1 = Event(
            data={"title": "(2) YouTube"},
            timestamp=starttime,
            duration=timedelta(seconds=1),
        )
        bucket_main.insert(e1)
        # Query
        result = query(qname, example_query, starttime, endtime, datastore)
        # Assert
        assert result[0]["data"]["title"] == "YouTube"
    finally:
        datastore.delete_bucket(bid1)


@pytest.mark.parametrize("datastore", param_datastore_objects())
def test_query2_query_categorize(datastore):
    bid = "test_bucket"
    qname = "test"
    starttime = iso8601.parse_date("1970")
    endtime = starttime + timedelta(hours=1)

    example_query = (
        rf"""
    events = query_bucket("{bid}");
    events = sort_by_timestamp(events);
    events = categorize(events, [
                [["test"], {{"regex": "test"}}],
                [["test", "subtest"], {{"regex": "test\w"}}]
            ]);
    events_by_cat = merge_events_by_keys(events, ["$category"]);
    RETURN = {{"events": events, "events_by_cat": events_by_cat}};
    """
    )
    try:
        bucket = datastore.create_bucket(
            bucket_id=bid, type="test", client="test", hostname="test", name="asd"
        )
        events = [
            Event(
                data={"label": "test"},
                timestamp=starttime,
                duration=timedelta(seconds=1),
            ),
            Event(
                data={"label": "testwithmoredetail"},
                timestamp=starttime + timedelta(seconds=1),
                duration=timedelta(seconds=1),
            ),
            Event(
                data={"label": "testwithmoredetail"},
                timestamp=starttime + timedelta(seconds=2),
                duration=timedelta(seconds=1),
            ),
        ]
        bucket.insert(events)
        result = query(qname, example_query, starttime, endtime, datastore)
        print(result)
        assert len(result["events"]) == 3
        assert result["events"][0].data["label"] == "test"
        assert result["events"][0].data["$category"] == ["test"]
        assert result["events"][1].data["$category"] == ["test", "subtest"]

        assert len(result["events_by_cat"]) == 2
        assert result["events_by_cat"][0].data["$category"] == ["test"]
        assert result["events_by_cat"][1].data["$category"] == ["test", "subtest"]
        assert result["events_by_cat"][1].duration == timedelta(seconds=2)
    finally:
        datastore.delete_bucket(bid)
