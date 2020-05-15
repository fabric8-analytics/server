# Copyright © 2020 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Dharmendra G Patel <dhpatel@redhat.com>
#
"""Test DB Communicator."""

import os
import json
import unittest
from unittest.mock import patch

from bayesian.exceptions import HTTPError
from bayesian.utility.db_gateway import GraphAnalyses
from bayesian.utility.db_gateway import RdbAnalyses
from sqlalchemy.exc import SQLAlchemyError


class DbgatewayTest(unittest.TestCase):
    """Test Communicator."""

    @classmethod
    def setUpClass(cls):
        """Class variables initialised."""
        cls.eco = 'eco'
        cls.ver = '1'
        cls.pkg = 'pkg'

        # Read Vendor Data from JSON.
        rest_json_path2 = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data/gremlin/snyk_component_analyses_response.json')
        with open(rest_json_path2) as f:
            resp_json = json.load(f)

        cls.resp_json = resp_json

    @patch('bayesian.utility.db_gateway.post')
    def test_get_data_from_graph(self, _mockpost):
        """Test Get data from Graph. Gremlin calls."""
        _mockpost().json.return_value = self.resp_json
        ga = GraphAnalyses.get_ca_data_from_graph('eco', 'pkg', 'ver', 'snyk')
        self.assertIsInstance(ga, dict)
        self.assertIn('result', ga)
        self.assertIsInstance(ga.get('result'), dict)
        self.assertIn('requestId', ga)
        self.assertIsInstance(ga.get('requestId'), str)
        self.assertIn('status', ga)
        self.assertIsInstance(ga.get('status'), dict)


class TestRdbAnalyses(unittest.TestCase):
    """Test RDB Analyses."""

    @patch('bayesian.utility.db_gateway.fetch_sa_request', return_value={})
    def test_get_request_data_success(self, _fetch_sa_request):
        """Test get SA request data."""
        self.assertEqual(RdbAnalyses.get_request_data('dummy_request_id'), {})

    @patch('bayesian.utility.db_gateway.fetch_sa_request', return_value=None)
    def test_get_request_data_error(self, _fetch_sa_request):
        """Test get SA request data."""
        self.assertRaises(HTTPError, RdbAnalyses.get_request_data, 'dummy_request_id')

    @patch('bayesian.utility.db_gateway.retrieve_worker_result', return_value={})
    def test_get_stack_result(self, _fetch_sa_request):
        """Test get SA stack result."""
        self.assertEqual(RdbAnalyses.get_stack_result('dummy_request_id'), {})

    @patch('bayesian.utility.db_gateway.retrieve_worker_result', return_value={})
    def test_get_recommendation_data(self, _fetch_sa_request):
        """Test get SA recommendation data."""
        self.assertEqual(RdbAnalyses.get_recommendation_data('dummy_request_id'), {})

    @patch('bayesian.utility.db_gateway.rdb.session.execute',
           side_effect=SQLAlchemyError('Mock exception'))
    def test_save_post_request_error(self, _execute):
        """Test error save request that raises exception."""
        self.assertRaises(HTTPError, RdbAnalyses.save_post_request, 'dummy_request_id', '', {}, {})

    @patch('bayesian.utility.db_gateway.rdb.session.execute', return_value=0)
    @patch('bayesian.utility.db_gateway.rdb.session.commit', return_value=0)
    def test_save_post_request_success(self, _commit, _execute):
        """Test success save request."""
        self.assertEqual(RdbAnalyses.save_post_request('dummy_request_id', '', {}, {}), None)
