"""Test papers functionality."""
# pylint: disable=redefined-outer-name, unused-argument, no-self-use

from json import loads
from datetime import datetime

from test.conftest import EMAIL, PASS, TMP_EMAIL

from flask import url_for
import pytest

from app.interfaces.model import Paper, UpdateDate, User, PaperList
from app import mail, db
from app.utils import encode_token

ROOT_LOAD = 'auto_bp.load_papers'
ROOT_DATA = 'main_bp.data'
ROOT_PAPERS = 'main_bp.papers_list'
ROOT_BOOKSHELF = 'main_bp.bookshelf'
ROOT_ADD_BM = 'main_bp.add_bm'
ROOT_BM_USER = 'auto_bp.bookmark_user'
ROOT_DEL_PAPERS = 'auto_bp.delete_papers'


@pytest.mark.usefixtures('live_server')
class TestMainPages:
    """Main pages simple tests."""
    def test_signup_page(self, client):
        """Test sign up page."""
        response = client.get(url_for('auth_bp.signup'))
        assert response.status_code == 200

    def test_paper_land(self, client, login):
        """Test paper loading page."""
        response = client.get(url_for('main_bp.paper_land'),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'ERROR' not in response.get_data(as_text=True)
        assert 'Select' in response.get_data(as_text=True)

    def test_paper_page(self, client, login):
        """Test paper page load."""
        response = client.get(url_for(ROOT_PAPERS),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'ERROR' not in response.get_data(as_text=True)

    def test_bookshelf_page(self, client, papers, login):
        """Test bookmark page load."""
        paper_list = User.query.filter_by(email=EMAIL).first().lists[0]
        paper_list.papers.append(Paper.query.filter_by().first())
        db.session.commit()
        response = client.get(url_for(ROOT_BOOKSHELF),
                              follow_redirects=True
                              )
        assert response.status_code == 200

    def test_bookshelf_page_wrong_page(self, client, login):
        """Test bookmark page with a wrong argument."""
        list_id = User.query.filter_by(email=EMAIL).first().id
        response = client.get(url_for(ROOT_BOOKSHELF,
                                      page='abracadabra',
                                      list_id=list_id
                                      ),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'page=1' in response.history[-1].location

    def test_bookshelf_page_wrong_list(self, client, login):
        """Test bookmark page with a wrong argument."""
        list_id = User.query.filter_by(email=EMAIL).first().id
        response = client.get(url_for(ROOT_BOOKSHELF,
                                      list_id=list_id+3
                                      ),
                              follow_redirects=True
                              )
        assert 'list_id=' + str(list_id+3) not in response.history[-1].location
        assert 'list_id=' + str(list_id) in response.history[-1].location

    def test_bookshelf_large_page(self, client, login):
        """Test bookmark page with a wrong argument."""
        list_id = User.query.filter_by(email=EMAIL).first().id
        response = client.get(url_for(ROOT_BOOKSHELF,
                                      page=10000,
                                      list_id=list_id
                                      ),
                              follow_redirects=True
                              )
        assert 'page=10000' not in response.history[-1].location
        assert 'page=1' in response.history[-1].location

    def test_pass_restore_page(self, client):
        """Test password restore page."""
        response = client.get(url_for('auth_bp.restore'))
        assert response.status_code == 200

    def test_settings_page(self, client, login):
        """Test settings page render."""
        response = client.get(url_for('settings_bp.settings_page'),
                              follow_redirects=True
                              )
        assert response.status_code == 200

    def test_settings_page_wrong(self, client, login):
        """Test settings page with wrong argument."""
        response = client.get(url_for('settings_bp.settings_page',
                                      page='blablabla'),
                              follow_redirects=True
                              )
        assert response.status_code == 200
        assert 'cat' in response.history[-1].location
        assert 'blablabla' not in response.history[-1].location

    def test_about_page(self, client):
        """Test about page view."""
        response = client.get(url_for('main_bp.about'))
        assert response.status_code == 200

    def test_error(self, client):
        """Test error page."""
        response = client.get(url_for('error_path'))
        assert response.status_code == 500
        assert 'Sorry' in response.get_data(as_text=True)

    def test_wrong_url(self, client):
        """Test wrong URL error page."""
        response = client.get('blablabla')
        assert response.status_code == 404
        assert 'main page' in response.get_data(as_text=True)

    def test_missed_csrf_token(self, client, user):
        """Test missed CSRF token."""
        client.application.config['WTF_CSRF_ENABLED'] = True
        response = client.post(url_for('auth_bp.login'),
                               data={'i_login': EMAIL,
                                     'i_pass': PASS
                                     },
                               follow_redirects=True
                               )
        assert 'ERROR' in response.get_data(as_text=True)
        client.application.config['WTF_CSRF_ENABLED'] = False


@pytest.mark.usefixtures('live_server')
class TestPaperPage:
    """Main paper feed page features."""
    def test_paper_api(self, client, papers, login):
        """Test paper API."""
        response5 = client.get(url_for(ROOT_DATA, date='unseen'))
        response4 = client.get(url_for(ROOT_DATA, date='last'))
        response1 = client.get(url_for(ROOT_DATA, date='today'))
        response2 = client.get(url_for(ROOT_DATA, date='week'))
        response3 = client.get(url_for(ROOT_DATA, date='month'))

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

    def test_paper_dates(self, client, login):
        """Test dates of the papers in the API response."""
        response1 = client.get(url_for(ROOT_DATA, date='today'))

        date_list = [datetime.strptime(paper['date_up'], '%d %B %Y')
                     for paper in response1.json['papers']]
        date_list = sorted(date_list, reverse=True)

        assert abs((date_list[0] - date_list[-1]).days) < 2 and \
               date_list[0].weekday != 1 or \
               abs((date_list[0] - date_list[-1]).days) < 4

    def test_paper_dates_week(self, client, login):
        """Test dates of the papers in the API response."""
        response1 = client.get(url_for(ROOT_DATA, date='week'))

        date_list = [datetime.strptime(paper['date_up'], '%d %B %Y')
                     for paper in response1.json['papers']]
        date_list = sorted(date_list, reverse=True)

        assert abs((date_list[0] - date_list[-1]).days) < 8

    def test_paper_page_args(self, client, login):
        """Test paper page load with different date types."""
        response1 = client.get(url_for(ROOT_PAPERS,
                                       date='today'
                                       ),
                               follow_redirects=True
                               )
        response2 = client.get(url_for(ROOT_PAPERS,
                                       date='week'
                                       ),
                               follow_redirects=True
                               )
        response3 = client.get(url_for(ROOT_PAPERS,
                                       date='month'
                                       ),
                               follow_redirects=True
                               )
        response4 = client.get(url_for(ROOT_PAPERS,
                                       date='last'
                                       ),
                               follow_redirects=True
                               )
        response5 = client.get(url_for(ROOT_PAPERS,
                                       date='unseen'
                                       ),
                               follow_redirects=True
                               )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert response4.status_code == 200
        assert response5.status_code == 200

    def test_paper_page_not_auth(self, client):
        """Test unauthorised paper access."""
        response = client.get(url_for(ROOT_PAPERS),
                              follow_redirects=True)
        assert response.status_code == 200
        assert 'ERROR' in response.get_data(as_text=True)

    def test_add_and_del_bm(self, client, papers, login, user):
        """Test bookmark add and delete."""
        # first add --> response 201
        test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
        response = client.post(url_for(ROOT_ADD_BM),
                               data={'paper_id': test_paper.paper_id,
                                     'list_id': user.lists[0].id
                                     }
                               )
        assert response.status_code == 201

        # same paper --> response 200
        response = client.post(url_for(ROOT_ADD_BM),
                               data={'paper_id': test_paper.paper_id,
                                     'list_id': user.lists[0].id
                                     }
                               )
        assert response.status_code == 200

        # delete BM
        response = client.post(url_for('main_bp.del_bm'),
                               data={'paper_id': test_paper.paper_id,
                                     'list_id': user.lists[0].id
                                     }
                               )
        assert response.status_code == 201

    def test_add_wrong_bm(self, client, papers, login, user):
        """Test adding wrong bookmark."""
        response = client.post(url_for(ROOT_ADD_BM),
                               data={'paper_id': 1000000,
                                     'list_id': user.lists[0].id
                                     }
                               )
        assert response.status_code == 422

    def test_add_bm_to_wrong_list(self, client, papers, login, user):
        """Test adding bookmark to a wrong list."""
        test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
        response = client.post(url_for(ROOT_ADD_BM),
                               data={'paper_id': test_paper.id,
                                     'list_id': 100000
                                     }
                               )
        assert response.status_code == 422

    def test_add_bm_to_other_user_list(self, client, papers, login, user, tmp_user):
        """Test adding bookmark to a wrong list."""
        test_paper = Paper.query.order_by(Paper.date_up.desc()).first()
        response = client.post(url_for(ROOT_ADD_BM),
                               data={'paper_id': test_paper.id,
                                     'list_id': tmp_user.lists[0].id
                                     }
                               )
        assert response.status_code == 422

    def test_del_wrong_bm(self, client, login, user):
        """Test wrong bookmark delete."""
        response = client.post(url_for('main_bp.del_bm'),
                               data={'paper_id': 11,
                                     'list_id': user.lists[0].id
                                     }
                               )
        assert response.status_code == 204

    def test_new_list_creation(self, client, papers, login):
        """Test that the default list will be created if needed."""
        lists = User.query.filter_by(email=EMAIL).first().lists
        for paper_list in lists:
            PaperList.query.filter_by(id=paper_list.id).delete()
        db.session.commit()
        response = client.get(url_for(ROOT_DATA,
                                      date='today'
                                      ),
                              follow_redirects=True
                              )
        assert 'Favourite' in response.get_data(as_text=True)


@pytest.mark.usefixtures('live_server')
class TestAutoHooks:
    """
    Test AutoHooks.

    Automatic functions for paper downloading,
    bookmarking and creating email feeds.
    """
    def test_wrong_token(self, client):
        """Test access of the auto functions with wrong token."""
        response = client.post(url_for(ROOT_LOAD,  # nosec
                                       token='wrong_token',  # nosec
                                       ))
        assert response.status_code == 422

    def test_paper_bookmark(self, client, papers, user):
        """Test auto bookmark papers."""
        user.tags[0].bookmark = True
        db.session.commit()
        response = client.post(url_for('auto_bp.bookmark_papers',  # nosec
                                       token='test_token'  # nosec
                                       ))
        assert response.status_code == 201

    def test_paper_bookmark_range(self, client, papers, user):
        """Test auto bookmark papers for a given range."""
        user.tags[0].bookmark = True
        db.session.commit()
        response = client.post(url_for('auto_bp.bookmark_papers',  # nosec
                                       token='test_token',  # nosec
                                       start_date='2020-10-11'
                                       ))
        assert response.status_code == 201

    def test_paper_email(self, client, papers, user, tmp_user):
        """Test auto email papers."""
        # email is not verified
        user.tags[0].email = True
        tmp_user.tags[0].email = True
        db.session.commit()
        with mail.record_messages() as outbox:
            response = client.post(url_for('auto_bp.email_papers',  # nosec
                                           token='test_token',  # nosec
                                           do_send=True
                                           ))
            assert response.status_code == 201
            assert len(outbox) == 0

        # Make email verified
        user.verified_email = True
        tmp_user.verified_email = True
        UpdateDate.query.filter_by().delete()
        db.session.commit()

        with mail.record_messages() as outbox:
            response = client.post(url_for('auto_bp.email_papers',  # nosec
                                           token='test_token',  # nosec
                                           do_send=True
                                           ))
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
                                       token='test_token',  # nosec
                                       n_papers=1500,
                                       set='physics:hep-ex',
                                       do_update='True',
                                       start_date='2020-10-11',
                                       until='2020-12-20'
                                       ))
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
        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       token='test_token'
                                       )
                               )
        assert response.status_code == 422
        assert 'deleted' not in loads(response.get_data())

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       token='test_token',  # nosec
                                       days=1
                                       ))
        assert response.status_code == 201
        assert loads(response.get_data())['deleted'] > 0

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       token='test_token',  # nosec
                                       week=1
                                       ))
        assert response.status_code == 201
        assert 'deleted' in loads(response.get_data())

        response = client.post(url_for(ROOT_DEL_PAPERS,  # nosec
                                       token='test_token',  # nosec
                                       until='2019-09-10'
                                       ))
        assert response.status_code == 201
        assert 'deleted' in loads(response.get_data())


@pytest.mark.usefixtures('live_server')
class TestSettings:
    """
    Test settings endpoints.

    E.g. categories changes, tags modifications, preferences updates
    """
    def test_unsubscribe(self, client, login):
        """Test unsubscribe from all emails."""
        response = client.post(url_for('settings_bp.no_email'))
        assert response.status_code == 302

    def test_public_tags(self, client, login, user):
        """Test public available tags."""
        user.tags[0].public = True
        db.session.commit()
        response = client.get(url_for('main_bp.public_tags'))
        resp = loads(response.get_data(as_text=True))
        assert response.status_code == 200
        assert resp[0]['name'] == 'example'

    def test_add_wrong_list(self, client, login):
        """Add new paper list endpoint."""
        response = client.post(url_for('settings_bp.add_list'),
                               data={'name': ''}
                               )
        assert response.status_code == 422

    def test_add_list(self, client, login):
        """Add new paper list endpoint."""
        response = client.post(url_for('settings_bp.add_list'),
                               data={'name': 'new_one'}
                               )
        assert response.status_code == 201
