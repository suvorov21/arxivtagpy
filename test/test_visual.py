"""Test module with selenium."""
# pylint: disable=redefined-outer-name, no-self-use

from time import sleep

from test.conftest import EMAIL, PASS

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from flask import url_for
import pytest

@pytest.fixture(scope='session')
def driver():
    """Create chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    yield driver

@pytest.mark.usefixtures('live_server')
class TestLiveServer():
    """Class for tests with visual driver."""
    def test_server_is_up_and_running(self, driver):
        """Test server is up and driver is working."""
        driver.get(url_for('main_bp.root', _external=True))
        alert = driver.find_element_by_id('alert')
        assert alert is not None

    def test_login(self, driver):
        """Test login form."""
        driver.get(url_for('main_bp.root', _external=True))
        driver.find_element_by_name('i_login').send_keys(EMAIL)
        driver.find_element_by_name('i_pass').send_keys(PASS)
        driver.find_element_by_class_name('btn-primary').click()
        sleep(1)
        element = driver.find_element_by_id('about-nav')
        assert element is not None

    def test_paper_view(self, driver):
        """Test paper view."""
        driver.get(url_for('main_bp.root', _external=True) + '/papers')
        sleep(3)
        num = driver.find_element_by_id('paper-num-0').text
        assert num == '1'

    def test_paper_view_month(self, driver):
        """Test paper view month."""
        driver.get(url_for('main_bp.root', _external=True) + '/papers?date=month')
        sleep(3)
        num = driver.find_element_by_id('paper-num-0').text
        assert num == '1'

    def test_bookshelf_view(self, driver):
        """Test bookshelf page load properly."""
        driver.get(url_for('main_bp.bookshelf', _external=True))
        sleep(3)
        title = driver.find_element_by_id('paper-list-title')
        element = driver.find_element_by_id('loading-papers')
        display = element.value_of_css_property('display')
        assert title.text == 'Favourite'
        assert display == 'none'

    def test_settings_view(self, driver):
        """Test settings page load properly."""
        driver.get(url_for('settings_bp.settings_page',
                           page='cat',
                           _external=True))
        sleep(3)
        cat = driver.find_element_by_id('cat-name-hep-ex')
        assert cat.text == 'High Energy Physics - Experiment'

    def test_delete_cat(self, driver):
        """Test category delete."""
        driver.get(url_for('settings_bp.settings_page',
                           page='cat',
                           _external=True))
        sleep(3)
        driver.find_element_by_id('close_hep-ex').click()
        sleep(1)
        driver.find_element_by_class_name('btn-success').click()
        sleep(1)
        element = driver.find_element_by_class_name('alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_tag(self, driver):
        """Test tag modifications."""
        driver.get(url_for('settings_bp.settings_page',
                           page='tag',
                           _external=True
                           ))
        sleep(3)
        driver.find_element_by_id('tag-label-1').click()
        sleep(1)
        driver.find_element_by_id('tag-name').send_keys('test_test')
        driver.find_element_by_class_name('btn-success').click()
        sleep(1)
        element = driver.find_element_by_class_name('alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_del_tag(self, driver):
        """Test tag modifications."""
        driver.get(url_for('settings_bp.settings_page',
                           page='tag',
                           _external=True
                           ))
        sleep(3)
        driver.find_element_by_id('tag-label-1').click()
        sleep(1)
        driver.find_element_by_id('btn-del').click()
        sleep(1)
        driver.find_element_by_class_name('btn-success').click()
        sleep(1)
        element = driver.find_element_by_class_name('alert-dismissible')
        assert 'success' in element.get_attribute('class')
