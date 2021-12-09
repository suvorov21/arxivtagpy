"""Test module with selenium."""
# pylint: disable=redefined-outer-name, no-self-use

from time import sleep

from test.conftest import EMAIL, PASS

from flask import url_for

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

import pytest

ROOT = 'main_bp.root'
ROOT_PAPERS = 'main_bp.papers_list'
ROOT_SET = 'settings_bp.settings_page'


@pytest.fixture(scope='session')
def driver():
    """Create chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    yield driver


@pytest.mark.usefixtures('live_server')
class TestLiveServer:
    """Class for tests with visual driver."""
    def test_server_is_up_and_running(self, driver):
        """Test server is up and driver is working."""
        driver.get(url_for(ROOT, _external=True))
        alert = driver.find_element(By.ID, 'alert')
        assert alert is not None

    def test_login(self, driver):
        """Test login form."""
        driver.get(url_for(ROOT, _external=True))
        driver.find_element(By.NAME, 'i_login').send_keys(EMAIL)
        driver.find_element(By.NAME, 'i_pass').send_keys(PASS)
        driver.find_element(By.CLASS_NAME, 'btn-primary').click()
        sleep(1)
        element = driver.find_element(By.ID,'about-nav')
        assert element is not None

    def test_paper_view(self, driver):
        """Test paper view."""
        driver.get(url_for(ROOT_PAPERS, _external=True))
        sleep(3)
        num = driver.find_element(By.ID,'paper-num-0').text
        assert num == '1'

    def test_paper_selector(self, driver):
        """Test paper selector href."""
        driver.get(url_for('main_bp.paper_land', _external=True))
        sleep(3)
        driver.find_element(By.CLASS_NAME, 'paper-day').click()
        sleep(3)
        num = driver.find_element(By.ID,'paper-num-0').text
        assert num == '1'

    def test_paper_view_month(self, driver):
        """Test paper view month."""
        driver.get(url_for(ROOT, _external=True) + '/papers?date=month')
        sleep(3)
        num = driver.find_element(By.ID,'paper-num-0').text
        assert num == '1'

    def test_bookshelf_view(self, driver):
        """Test bookshelf page load properly."""
        driver.get(url_for('main_bp.bookshelf', _external=True))
        sleep(3)
        title = driver.find_element(By.ID, 'paper-list-title')
        element = driver.find_element(By.ID, 'loading-papers')
        displayEl = element.value_of_css_property('display')
        assert title.text == 'Favourite'
        assert displayEl == 'none'

    def test_settings_view(self, driver):
        """Test settings page load properly."""
        driver.get(url_for(ROOT_SET,
                           page='cat',
                           _external=True))
        sleep(3)
        cat = driver.find_element(By.ID, 'cat-name-hep-ex')
        assert cat.text == 'High Energy Physics - Experiment'

    def test_delete_cat(self, driver):
        """Test category delete."""
        driver.get(url_for(ROOT_SET,
                           page='cat',
                           _external=True))
        sleep(3)
        driver.find_element(By.ID, 'close_hep-ex').click()
        sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(1)
        element = driver.find_element(By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_tag(self, driver):
        """Test tag modifications."""
        driver.get(url_for(ROOT_SET,
                           page='tag',
                           _external=True
                           ))
        sleep(3)
        driver.find_element(By.ID, 'tag-label-1').click()
        sleep(1)
        driver.find_element(By.ID, 'tag-name').send_keys('test_test')
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(2)
        driver.find_element(By.ID, 'tag-label-1').click()
        sleep(1)
        new_val = driver.find_element(By.ID, 'tag-name').get_attribute("value")
        assert new_val == 'testtest_test'

    def test_del_tag(self, driver):
        """Test tag modifications."""
        driver.get(url_for(ROOT_SET,
                           page='tag',
                           _external=True
                           ))
        sleep(3)
        driver.find_element(By.ID, 'tag-label-1').click()
        sleep(1)
        driver.find_element(By.ID, 'btn-del').click()
        sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(1)
        element = driver.find_element(By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_pref(self, driver):
        """Test preference modifications."""
        driver.get(url_for(ROOT_SET,
                           page='pref',
                           _external=True
                           ))
        sleep(3)
        driver.find_element(By.ID, 'tex-check').click()
        sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(2)
        element = driver.find_element(By.ID, 'tex-check')
        assert not element.is_selected()

    def test_mod_book(self, driver):
        """Test bookmarks modifications."""
        driver.get(url_for(ROOT_SET,
                           page='bookshelf',
                           _external=True
                           ))
        sleep(3)
        driver.find_element(By.CLASS_NAME, 'close-btn').click()
        sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(1)
        element = driver.find_element(By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_add_book(self, driver):
        """Test add bookmarks."""
        driver.get(url_for(ROOT_SET,
                           page='bookshelf',
                           _external=True
                           ))
        sleep(3)
        driver.find_element(By.ID, 'new-list').send_keys('new_list')
        sleep(1)
        driver.find_element(By.ID, 'add-book-btn').click()
        sleep(2)
        assert 'new_list' in driver.page_source

    def test_btn_save(self, driver):
        """Test if save button become active on change on settings page."""
        driver.get(url_for(ROOT_SET,
                           page='pref',
                           _external=True
                           ))
        sleep(2)
        element1 = driver.find_element(By.CLASS_NAME, 'btn-success')
        element2 = driver.find_element(By.CLASS_NAME, 'btn-secondary')

        assert 'disabled' in element1.get_attribute('class')
        assert 'disabled' in element2.get_attribute('class')

        driver.find_element(By.ID, 'tex-check').click()
        sleep(1)
        element1 = driver.find_element(By.CLASS_NAME, 'btn-success')
        element2 = driver.find_element(By.CLASS_NAME, 'btn-secondary')

        assert 'disabled' not in element1.get_attribute('class')
        assert 'disabled' not in element2.get_attribute('class')

    def test_cookies(self, driver):
        """Test cookies."""
        driver.get(url_for(ROOT_PAPERS, _external=True))
        sleep(3)
        assert driver.find_element(By.ID, 'check-nov-1').is_selected()
        driver.find_element(By.ID, 'check-nov-1').click()
        driver.get(url_for(ROOT_PAPERS, _external=True))
        sleep(3)
        assert not driver.find_element(By.ID, 'check-nov-1').is_selected()
