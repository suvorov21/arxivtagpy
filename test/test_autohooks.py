from json import loads

import pytest
import requests_mock
import urllib3
from flask import url_for

from app import db, mail
from app.interfaces.model import UpdateDate
from app.paper_api import ArxivOaiApi
from app.utils import encode_token
from test.conftest import TMP_EMAIL, EMAIL
from test.test_response import ROOT_LOAD, ROOT_BM_USER, ROOT_DEL_PAPERS


@pytest.mark.usefixtures('live_server')
class TestAutoHooks:
    """
    Test AutoHooks.

    Automatic functions for paper downloading,
    bookmarking and creating email feeds.
    """

    def test_wrong_token(self, client):
        """Test access of the auto functions with wrong token."""
        response = client.post(url_for(ROOT_LOAD),
                               headers={"token": "wrong_token"}  # nosec
                               )
        assert response.status_code == 422

    def test_paper_bookmark(self, client, papers, user):
        """Test auto bookmark papers."""
        user.tags[0].bookmark = True
        db.session.commit()
        response = client.post(url_for('auto_bp.bookmark_papers'),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201

    def test_paper_bookmark_range(self, client, papers, user):
        """Test auto bookmark papers for a given range."""
        user.tags[0].bookmark = True
        db.session.commit()
        response = client.post(url_for('auto_bp.bookmark_papers',  # nosec
                                       start_date='2020-10-11'
                                       ),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201

    def test_paper_email(self, client, papers, user, tmp_user):
        """Test auto email papers."""
        # email is not verified
        user.tags[0].email = True
        tmp_user.tags[0].email = True
        db.session.commit()
        with mail.record_messages() as outbox:
            response = client.post(url_for('auto_bp.email_papers',  # nosec
                                           do_send=True
                                           ),
                                   headers={"token": "test_token"}  # nosec
                                   )
            assert response.status_code == 201
            assert len(outbox) == 0

        # Make email verified
        user.verified_email = True
        tmp_user.verified_email = True
        UpdateDate.query.filter_by().delete()
        db.session.commit()

        with mail.record_messages() as outbox:
            response = client.post(url_for('auto_bp.email_papers',  # nosec
                                           do_send=True
                                           ),
                                   headers={"token": "test_token"}  # nosec
                                   )
            assert response.status_code == 201
            assert len(outbox) == 2
            assert outbox[0].recipients == [EMAIL]
            assert outbox[1].recipients == [TMP_EMAIL]

    def test_bookmark_user(self, client, login, user):
        """Test the bookmarking for the past month."""
        data = {'name': 'example'}
        response = client.post(url_for(ROOT_BM_USER),
                               data=data
                               )
        assert response.status_code == 201

    def test_bookmark_user_token(self, client, user):
        """Check the bookmarking triggered remotely with a token."""
        data = {'name': 'example',
                'token': 'test_token',
                'email': EMAIL
                }
        response = client.post(url_for(ROOT_BM_USER),
                               data=data
                               )
        assert response.status_code == 201

    def test_bookmark_user_bad_request(self, client, login, user):
        """Test the bookmarking with wrong arguments."""
        data = {'name': 'example'}
        response = client.post(url_for(ROOT_BM_USER,
                                       email=EMAIL,
                                       data=data
                                       )
                               )
        assert response.status_code == 422

        response = client.post(url_for(ROOT_BM_USER,
                                       email=EMAIL,
                                       data={}
                                       )
                               )
        assert response.status_code == 422

        response = client.post(url_for(ROOT_BM_USER,
                                       email=EMAIL,
                                       data={'name': 'wrong'}
                                       )
                               )
        assert response.status_code == 422

    def test_load_papers(self, client):
        """Test paper loading."""
        response = client.post(url_for(ROOT_LOAD,  # nosec
                                       n_papers=1500,
                                       set='physics:hep-ex',
                                       do_update='True',
                                       start_date='2020-10-11',
                                       until='2020-12-20'
                                       ),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201

    def test_rss(self, client, papers, login):
        """Test RSS endpoint."""
        # check wrong token
        response = client.get(url_for('auto_bp.rss_feed',
                                      token='test'
                                      ),
                              follow_redirects=False
                              )

        assert response.status_code == 303

        # check the correct token
        response = client.get(url_for('auto_bp.rss_feed',
                                      token=encode_token({"user": EMAIL})
                                      ),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        # check that there is a paper inside
        assert '<item><title>' in response.get_data(as_text=True)

    def test_paper_delete(self, client, papers, login):
        """Test paper delete endpoint."""
        # no date --> error
        response = client.post(url_for(ROOT_DEL_PAPERS),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 422
        assert 'deleted' not in loads(response.get_data())

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       days=1
                                       ),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201
        assert loads(response.get_data())['deleted'] > 0

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       week=1
                                       ),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201
        assert 'deleted' in loads(response.get_data())

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       until='2030-09-10'
                                       ),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201
        assert 'deleted' in loads(response.get_data())

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       until='2030-09-10',
                                       force=True
                                       ),
                               headers={"token": "test_token"}  # nosec
                               )
        assert response.status_code == 201
        assert 'deleted' in loads(response.get_data())


def test_exceeds_max_error_limit():
    with requests_mock.Mocker(real_http=False) as mock_api:
        mock_api.get(
            'http://export.arxiv.org/oai2?verb=ListRecords&metadataPrefix=arXivRaw&set=cs&from=2022-01-01&until=2022-01-31',
            status_code=404)

        api = ArxivOaiApi()
        api.set_set('cs')
        api.set_from('2022-01-01')
        api.set_until('2022-01-31')

        papers = list(api.download_papers())
        assert len(papers) == 0
        assert api.fail_attempts > api.MAX_FAIL


def test_retry_after_error():
    with requests_mock.Mocker(real_http=False) as mock_api:
        mock_api.get(
            'http://export.arxiv.org/oai2?verb=ListRecords&metadataPrefix=arXivRaw&set=cs&from=2022-01-01&until=2022-01-31',
            status_code=404, headers={'Retry-After': '1'})

        api = ArxivOaiApi()
        api.set_set('cs')
        api.set_from('2022-01-01')
        api.set_until('2022-01-31')

        papers = list(api.download_papers())
        assert len(papers) == 0
        assert api.fail_attempts > api.MAX_FAIL


def test_exception_throw():
    with requests_mock.Mocker(real_http=False) as mock_api:
        def cb(req, ctx):
            raise urllib3.exceptions.HTTPError

        mock_api.get(
            'http://export.arxiv.org/oai2?verb=ListRecords&metadataPrefix=arXivRaw&set=cs&from=2022-01-01&until=2022-01-31',
            status_code=404, text=cb)

        api = ArxivOaiApi()
        api.set_set('cs')
        api.set_from('2022-01-01')
        api.set_until('2022-01-31')

        papers = list(api.download_papers())
        assert len(papers) == 0
        assert api.fail_attempts > api.MAX_FAIL
