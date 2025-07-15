#!/usr/bin/env python3
"""Test utils module
"""
import unittest
from parameterized import parameterized
from unittest.mock import patch, Mock, PropertyMock
from utils import access_nested_map, get_json, memoize


class TestAccessNestedMap(unittest.TestCase):
    """Test access_nested_map function"""

    @parameterized.expand([
        ({"a": 1}, ("a",), 1),
        ({"a": {"b": 2}}, ("a",), {"b": 2}),
        ({"a": {"b": 2}}, ("a", "b"), 2)
    ])
    def test_access_nested_map(self, nested_map, path, expected):
        """Test access_nested_map with valid inputs"""
        self.assertEqual(access_nested_map(nested_map, path), expected)

    @parameterized.expand([
        ({}, ("a",), "a"),
        ({"a": 1}, ("a", "b"), "b")
    ])
    def test_access_nested_map_exception(self, nested_map, path, expected_key):
        """Test access_nested_map raises KeyError for invalid paths"""
        with self.assertRaises(KeyError) as cm:
            access_nested_map(nested_map, path)
        self.assertEqual(str(cm.exception), f"'{expected_key}'")


class TestGetJson(unittest.TestCase):
    """Test get_json function"""

    @parameterized.expand([
        ("http://example.com", {"payload": True}),
        ("http://holberton.io", {"payload": False})
    ])
    @patch('requests.get')
    def test_get_json(self, test_url, test_payload, mock_get):
        """Test get_json returns expected result
            without making actual HTTP call
        """
        mock_get.return_value = Mock(json=lambda: test_payload)
        result = get_json(test_url)
        mock_get.assert_called_once_with(test_url)
        self.assertEqual(result, test_payload)


class TestMemoize(unittest.TestCase):
    """Test memoize decorator"""

    def test_memoize(self):
        """Test that memoize caches the result"""
        class TestClass:
            """Test class for memoize"""
            def a_method(self):
                return 42

            @memoize
            def a_property(self):
                return self.a_method()

        with patch.object(TestClass, 'a_method') as mock_method:
            mock_method.return_value = 42
            test = TestClass()
            self.assertEqual(test.a_property, 42)
            self.assertEqual(test.a_property, 42)
            mock_method.assert_called_once()


if __name__ == '__main__':
    unittest.main()
