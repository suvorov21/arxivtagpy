"""Test papers functionality."""
# pylint: disable=redefined-outer-name

from json import loads

import pytest

from app import db
from app.model import Paper

from test.test_auth import init_app

@pytest.fixture(scope='module', autouse=True)
def client_with_papers(init_app):
    """Fixture for filling DB with papers."""
    init_app.get('/load_papers?token=test_token&n_papers=10&search_query=hep-ex&method=new')
    init_app.post('/new_user',
                  data={'email': 'tester2@gmail.com',
                        'pasw': 'tester2',
                        'pasw2': 'tester2'
                        },
                  follow_redirects=True
                  )
    yield init_app
    db.session.remove()
    db.drop_all()

def test_paper_api(client_with_papers):
    """Test paper download."""
    response = client_with_papers.get('/data?date=today')
    data = loads(response.get_data())
    assert response.status_code == 200
    assert data.get('papers') is not None
    assert len(data.get('papers')) > 0

def test_paper_page(client_with_papers):
    """Test paper page load."""
    response = client_with_papers.get('/papers',
                                      follow_redirects=True
                                      )
    assert response.status_code == 200

def test_add_bm(client_with_papers):
    """Test bookmark add."""
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client_with_papers.post('/add_bm',
                                       data={'paper_id': test_paper.paper_id}
                                       )
    assert response.status_code == 201

def test_del_bm(client_with_papers):
    """Test bookmark delete."""
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client_with_papers.post('/del_bm',
                                       data={'paper_id': test_paper.paper_id}
                                       )
    assert response.status_code == 201

def test_bookshelf_page(client_with_papers):
    """Test bookmark page load."""
    response = client_with_papers.get('/bookshelf')
    assert response.status_code == 200