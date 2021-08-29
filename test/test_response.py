"""Test papers functionality."""
# pylint: disable=redefined-outer-name, unused-argument

from json import loads
from datetime import datetime

from test.conftest import DEFAULT_LIST

from flask import url_for

from app.model import Paper

def test_load_papers(client):
    """Test paper loading."""
    response = client.post(url_for('auto_bp.load_papers', # nosec
                                   token='test_token', # nosec
                                   n_papers=500,
                                   set='physics:hep-ex'
                                   ))
    assert response.status_code == 201

def test_paper_api(client, login):
    """Test paper API."""
    response5 = client.get(url_for('main_bp.data', date='unseen'))
    response4 = client.get(url_for('main_bp.data', date='last'))
    response1 = client.get(url_for('main_bp.data', date='today'))
    response2 = client.get(url_for('main_bp.data', date='week'))
    response3 = client.get(url_for('main_bp.data', date='month'))
    # response4 = client.get(url_for('main_bp.data', date='last'))
    data1 = loads(response1.get_data(as_text=True))
    data2 = loads(response2.get_data(as_text=True))
    data3 = loads(response3.get_data(as_text=True))
    data4 = loads(response4.get_data(as_text=True))
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert response4.status_code == 200
    assert response5.status_code == 200
    assert data1.get('papers') is not None
    assert len(data1.get('papers')) > 0
    assert data2.get('papers') is not None
    assert len(data2.get('papers')) > 0
    assert data3.get('papers') is not None
    assert len(data3.get('papers')) > 0
    assert data4.get('papers') is not None
    # assert len(data4.get('papers')) > 0

def test_paper_dates(client, login):
    """Test dates of the papers in the API response."""
    response1 = client.get(url_for('main_bp.data', date='today'))

    date_list = [datetime.strptime(paper['date_up'], '%d %B %Y')
                                   for paper in response1.json['papers']]
    date_list = sorted(date_list, reverse=True)

    assert abs((date_list[0] - date_list[-1]).days) < 2 and  \
           date_list[0].weekday != 1 or \
           abs((date_list[0] - date_list[-1]).days) < 4

def test_paper_dates_week(client, login):
    """Test dates of the papers in the API response."""
    response1 = client.get(url_for('main_bp.data', date='week'))

    date_list = [datetime.strptime(paper['date_up'], '%d %B %Y')
                                   for paper in response1.json['papers']]
    date_list = sorted(date_list, reverse=True)

    assert abs((date_list[0] - date_list[-1]).days) < 8


def test_paper_page(client, login):
    """Test paper page load."""
    response = client.get(url_for('main_bp.papers_list'),
                          follow_redirects=True
                          )
    assert response.status_code == 200

def test_signup_page(client):
    """Test sign up page."""
    response = client.get(url_for('auth_bp.signup'))
    assert response.status_code == 200

def test_paper_page_not_auth(client):
    """Test anauthorised paper access."""
    response = client.get(url_for('main_bp.papers_list'),
                          follow_redirects=True)
    assert response.status_code == 200
    assert 'ERROR' in response.get_data(as_text=True)

def test_add_bm(client, login):
    """Test bookmark add."""
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client.post(url_for('main_bp.add_bm'),
                           data={'paper_id': test_paper.paper_id,
                                 'list_id': 1
                                 }
                           )
    assert response.status_code == 201

def test_del_bm(client, login):
    """Test bookmark delete."""
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client.post(url_for('main_bp.del_bm'),
                           data={'paper_id': test_paper.paper_id,
                                 'list_id': 1
                                 }
                           )
    assert response.status_code == 201

def test_del_wrong_bm(client, login):
    """Test wrong bookmark delete."""
    response = client.post(url_for('main_bp.del_bm'),
                           data={'paper_id': 11,
                                 'list_id': 1
                                 }
                           )
    assert response.status_code == 204

def test_bookshelf_page(client, login):
    """Test bookmark page load."""
    response = client.get(url_for('main_bp.bookshelf'),
                          follow_redirects=True
                          )
    assert response.status_code == 200

def test_bookshelf_page(client, login):
    """Test bookmark page with a wrong argument."""
    response = client.get(url_for('main_bp.bookshelf'),
                          data={'page': 'abracadabra'},
                          follow_redirects=True
                          )
    assert response.status_code == 200

def test_settings_page(client, login):
    """Test settings page render."""
    response = client.get(url_for('settings_bp.settings_page'),
                          follow_redirects=True
                          )
    assert response.status_code == 200

def test_wrong_token(client):
    """Test access of the auto functions with wrong token."""
    response = client.post(url_for('auto_bp.load_papers', # nosec
                                   token='wrong_token', # nosec
                                   ))
    assert response.status_code == 422

def test_paper_bookmark(client):
    """Test auto bookmark papers."""
    response = client.post(url_for('auto_bp.bookmark_papers', # nosec
                                   token='test_token' # nosec
                                   ))
    assert response.status_code == 201


def test_paper_email(client):
    """Test auto email papers."""
    response = client.post(url_for('auto_bp.email_papers', # nosec
                                   token='test_token', # nosec
                                   do_send=False
                                   ))
    assert response.status_code == 201

def test_public_tags(client, login):
    """Test public available tags."""
    response = client.get(url_for('main_bp.public_tags'))
    resp = loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert  resp[0]['name'] == 'test'

def test_paper_delete(client, login):
    """Test paper delete endpoint."""
    response = client.post(url_for('auto_bp.delete_papers', # nosec
                                   token='test_token', # nosec
                                   week=1
                                   ))
    # download papers again for future tests
    client.get(url_for('auto_bp.load_papers', # nosec
                       token='test_token', # nosec
                       n_papers=100,
                       set='physics:hep-ex'
                       ))
    assert response.status_code == 201

def test_unsubscribe(client, login):
    """Test unsubscribe from all emails."""
    response = client.post(url_for('settings_bp.no_email'))
    assert response.status_code == 201
