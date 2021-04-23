"""Test papers functionality."""
# pylint: disable=redefined-outer-name, unused-argument

from json import loads

from flask import url_for

from app.model import Paper

def test_load_papers(client):
    """Test paper loading."""
    response = client.get('/load_papers?token=test_token&n_papers=10&set=physics:hep-ex')
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
    response = client.get('/papers',
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
    response = client.get(url_for('settings_bp.settings'),
                          follow_redirects=True
                          )
    assert response.status_code == 200