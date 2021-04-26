"""Test papers functionality."""
# pylint: disable=redefined-outer-name, unused-argument

from json import loads

from flask import url_for

from app.model import Paper

def test_load_papers(client):
    """Test paper loading."""
    response = client.get(url_for('auto_bp.load_papers', # nosec
                                  token='test_token', # nosec
                                  n_papers=10,
                                  set='physics:hep-ex'
                                  ))
    assert response.status_code == 201

def test_paper_api(client, login):
    """Test paper API."""
    response = client.get(url_for('main_bp.data', date='today'))
    data = loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert data.get('papers') is not None
    assert len(data.get('papers')) > 0

def test_paper_page(client, login):
    """Test paper page load."""
    response = client.get(url_for('main_bp.papers_list'),
                          follow_redirects=True
                          )
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
                           data={'paper_id': test_paper.paper_id}
                           )
    assert response.status_code == 201

def test_del_bm(client, login):
    """Test bookmark delete."""
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client.post(url_for('main_bp.del_bm'),
                           data={'paper_id': test_paper.paper_id}
                           )
    assert response.status_code == 201

def test_bookshelf_page(client, login):
    """Test bookmark page load."""
    response = client.get(url_for('main_bp.bookshelf'),
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
    response = client.get(url_for('auto_bp.load_papers', # nosec
                              token='wrong_token', # nosec
                              ))
    assert response.status_code == 422

def test_paper_bookmark(client):
    """Test auto bookmark papers."""
    response = client.get(url_for('auto_bp.bookmark_papers', # nosec
                              token='test_token' # nosec
                              ))
    assert response.status_code == 201


def test_paper_email(client):
    """Test auto email papers."""
    response = client.get(url_for('auto_bp.email_papers', # nosec
                              token='test_token', # nosec
                              do_send=False
                              ))
    assert response.status_code == 201

def test_public_tags(client, login):
    """Test public available tags."""
    response = client.get(url_for('main_bp.public_tags'))
    exp_tag = '[{"name":"test","rule":"ti{math}|abs{physics}&au{John}"}]\n'
    assert response.status_code == 200
    assert response.get_data(as_text=True) == exp_tag
