"""Test papers functionality."""
# pylint: disable=redefined-outer-name

from json import loads

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

import pytest

from app import app_init, db
from app.model import User, Paper

from test.test_auth import init_app

@pytest.fixture(scope='module', autouse=True)
def client_with_papers(init_app):
    """Fixture for filling DB with papers."""
    init_app.get('/load_papers?token=test_token&n_papers=10&search_query=hep-ex&method=new')
    response = init_app.post('/new_user',
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
    response = client_with_papers.post('/login',
                                       data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                       follow_redirects=True
                                       )
    response = client_with_papers.get('/data?date=today')
    data = loads(response.get_data())
    assert response.status_code == 200
    assert data.get('papers') is not None
    assert len(data.get('papers')) > 0


def test_add_bm(client_with_papers):
    """Test bookmark add."""
    response = client_with_papers.post('/login',
                                       data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                       follow_redirects=True
                                       )
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client_with_papers.post('/add_bm',
                                       data={'paper_id': test_paper.paper_id}
                                       )
    assert response.status_code == 201

def test_del_bm(client_with_papers):
    """Test bookmark delete."""
    response = client_with_papers.post('/login',
                                       data={'i_login': 'tester@gmail.com', 'i_pass':'tester'},
                                       follow_redirects=True
                                       )
    test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
    response = client_with_papers.post('/del_bm',
                                       data={'paper_id': test_paper.paper_id}
                                       )
    assert response.status_code == 201