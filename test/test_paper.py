"""Test papers functionality."""
# pylint: disable=redefined-outer-name

from json import loads

import pytest

from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from app import app_init, db
from app.model import User, Paper


@pytest.fixture(scope='module', autouse=True)
def client_with_papers():
    """Fixture for filling DB with papers."""
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    with app.app_context():
        db.create_all()
        user1 = User(email='tester@gmail.com',
                 pasw=generate_password_hash('tester'),
                 arxiv_cat=['hep-ex'],
                 tags='[{"name": "test", "rule":"ti{test}", "color":"#ff0000"}]',
                 pref='{"tex": "True"}'
                 )
        db.session.add(user1)
        db.session.commit()
        client_with_papers = app.test_client()
        client_with_papers.get('/load_papers?token=test_token&n_papers=10&search_query=hep-ex')
        yield client_with_papers
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