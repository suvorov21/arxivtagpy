"""Test module with selenium."""
# pylint: disable=redefined-outer-name, no-self-use

from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from test.test_auth import make_user
from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from flask import url_for
import pytest

from app import app_init, db
import multiprocessing

EMAIL = 'tester@gmail.com'

@pytest.fixture(scope='session')
def driver():
    """Create chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    yield driver

@pytest.fixture(scope='session')
def app():
    """Initialize app + user recrod in db."""
    multiprocessing.set_start_method("fork")
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    with app.app_context():
        db.create_all()
        user = make_user(EMAIL)
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.mark.usefixtures('live_server')
class TestLiveServer():
    """Class for tests with visual driver/"""
    def test_server_is_up_and_running(self, driver):
        """Test server is up and driver is working."""
        driver.get(url_for('main_bp.root', _external=True))
        alert = driver.find_element_by_id('alert')
        assert alert is not None

    def test_login(self, driver):
        """Test login form."""
        root = url_for('main_bp.root', _external=True)
        driver.get(root + '/load_papers?token=test_token&n_papers=10&set=physics:hep-ex')

        driver.get(root)
        driver.find_element_by_name('i_login').send_keys(EMAIL)
        driver.find_element_by_name('i_pass').send_keys('tester')
        driver.find_element_by_class_name('btn-primary').click()
        sleep(1)
        element = driver.find_element_by_id('about-nav')
        assert element is not None

    def test_paper_view(self, driver):
        """Test paper view."""
        root = url_for('main_bp.root', _external=True)
        driver.get(root + '/papers')
        sleep(3)
        num = driver.find_element_by_id('paper-num-0').text
        assert num == '1'

    def test_bookshelf_view(self, driver):
        """Test bookshelf page load properly."""
        root = url_for('main_bp.bookshelf', _external=True)
        driver.get(root)
        sleep(3)
        title = driver.find_element_by_id('paper-list-title')
        element = driver.find_element_by_id('loading-papers')
        display = element.value_of_css_property('display')
        assert title.text == 'Favourite'
        assert display == 'none'

    def test_settings_view(self, driver):
        """Test settings page load properly."""
        root = url_for('main_bp.settings', _external=True)
        driver.get(root)
        sleep(3)
        cat = driver.find_element_by_id('cat-name-hep-ex')
        assert cat.text == 'High Energy Physics - Experiment'
