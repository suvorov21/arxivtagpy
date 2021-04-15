"""Test module with selenium."""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from werkzeug.utils import import_string
from werkzeug.security import generate_password_hash

from app import app_init, db
from app.model import User
from time import sleep

from flask import url_for

import multiprocessing

@pytest.fixture
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    yield driver

@pytest.fixture(scope='session')
def app():
    multiprocessing.set_start_method("fork")
    app = app_init()
    cfg = import_string('configmodule.TestingConfig')
    app.config.from_object(cfg)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.mark.usefixtures('live_server')
class TestLiveServer():
    def test_server_is_up_and_running(self, driver):
        driver.get(url_for('main_bp.root', _external=True))
        alert = driver.find_element_by_id('alert')
        assert alert is not None

    def test_paper_view(self, driver):
        root = url_for('main_bp.root', _external=True)
        driver.get(root + '/load_papers?token=test_token&n_papers=10&set=physics:hep-ex')
        email = 'tester@gmail.com'
        user1 = User(email=email,
                     pasw=generate_password_hash('tester'),
                     arxiv_cat=['hep-ex'],
                     tags='[{"name": "test", "rule":"ti{test}", "color":"#ff0000"}]',
                     pref='{"tex": "True"}'
                     )
        db.session.add(user1)
        db.session.commit()

        driver.get(root)
        driver.find_element_by_name('i_login').send_keys(email)
        driver.find_element_by_name('i_pass').send_keys('tester')
        driver.find_element_by_class_name('btn-primary').click()
        driver.get(root + '/papers')
        sleep(3)
        num = driver.find_element_by_id('paper-num-0').text
        assert num == '1'
