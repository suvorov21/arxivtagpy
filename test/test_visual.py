"""Test module with selenium."""
# pylint: disable=redefined-outer-name, no-self-use

from time import sleep
from os import environ

from test.conftest import EMAIL, PASS

from flask import url_for

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

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


def wait_load(wait, by, name):
    """Helper function to wait for element load."""
    return wait.until(EC.element_to_be_clickable((by, name)))


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
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT, _external=True))
        element = wait_load(wait, By.CLASS_NAME, 'btn-primary')

        driver.find_element(By.NAME, 'i_login').send_keys(EMAIL)
        driver.find_element(By.NAME, 'i_pass').send_keys(PASS)
        element.click()
        element = wait_load(wait, By.ID, 'about-nav')
        assert element is not None

    def test_paper_view(self, driver):
        """Test paper view."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_PAPERS, _external=True))
        element = wait_load(wait, By.ID, 'paper-num-0')
        assert element.text == '1'

    def test_paper_selector(self, driver):
        """Test paper selector href."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for('main_bp.paper_land', _external=True))
        element = wait_load(wait, By.CLASS_NAME, 'paper-day')
        element.click()
        element = wait_load(wait, By.ID, 'paper-num-0')
        assert element.text == '1'

    def test_paper_view_month(self, driver):
        """Test paper view month."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT, _external=True) + '/papers?date=month')
        element = wait_load(wait, By.ID, 'paper-num-0')
        assert element.text == '1'

    def test_bookshelf_view(self, driver):
        """Test bookshelf page load properly."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for('main_bp.bookshelf', _external=True))
        element = wait_load(wait, By.ID, 'paper-list-title')
        load = driver.find_element(By.ID, 'loading-papers')
        display_load = load.value_of_css_property('display')
        assert element.text == 'Favourite'
        assert display_load == 'none'

    def test_settings_view(self, driver):
        """Test settings page load properly."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='cat',
                           _external=True))
        element = wait_load(wait, By.ID, 'cat-name-hep-ex')
        assert element.text == 'High Energy Physics - Experiment'

    def test_delete_cat(self, driver):
        """Test category delete."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='cat',
                           _external=True))
        element = wait_load(wait, By.ID, 'close_hep-ex')
        element.click()
        sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        element = wait_load(wait, By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_tag(self, driver):
        """Test tag modifications."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='tag',
                           _external=True
                           ))
        element = wait_load(wait, By.ID, 'tag-label-1')
        element.click()
        element = wait_load(wait, By.ID, 'tag-name')
        element.send_keys('test_test')
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(1)
        element = wait_load(wait, By.ID, 'tag-label-1')
        element.click()
        new_val = driver.find_element(By.ID, 'tag-name').get_attribute("value")
        assert new_val == 'testtest_test'

    def test_del_tag(self, driver):
        """Test tag modifications."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='tag',
                           _external=True
                           ))
        element = wait_load(wait, By.ID, 'tag-label-1')
        element.click()
        element = wait_load(wait, By.ID, 'btn-del')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'btn-success')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_pref(self, driver):
        """Test preference modifications."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='pref',
                           _external=True
                           ))
        element = wait_load(wait, By.ID, 'tex-check')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'btn-success')
        element.click()
        sleep(1)
        element = wait_load(wait, By.ID, 'tex-check')
        assert not element.is_selected()

    def test_mod_book(self, driver):
        """Test bookmarks modifications."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='bookshelf',
                           _external=True
                           ))
        element = wait_load(wait, By.CLASS_NAME, 'close-btn')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'btn-success')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_add_book(self, driver):
        """Test add bookmarks."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='bookshelf',
                           _external=True
                           ))
        element = wait_load(wait, By.ID, 'new-list')
        element.send_keys('new_list')
        driver.find_element(By.ID, 'add-book-btn').click()
        sleep(1)

        assert 'new_list' in driver.page_source

    def test_btn_save(self, driver):
        """Test if save button become active on change on settings page."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_SET,
                           page='pref',
                           _external=True
                           ))
        element1 = wait_load(wait, By.CLASS_NAME, 'btn-success')
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
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT_PAPERS, _external=True))
        element = wait_load(wait, By.ID, 'check-nov-1')
        assert element.is_selected()
        element.click()
        driver.get(url_for(ROOT_PAPERS, _external=True))
        element = wait_load(wait, By.ID, 'check-nov-1')
        assert not element.is_selected()

    def test_orcid_auth(self, driver):
        """Test ORCID authentication."""
        login = environ.get('ORCID_NAME')
        passw = environ.get('ORCID_PASSW')

        if not login or not passw:
            print('WARNING! Test is skipped as no ORCID credentials are provided')
            assert True
            return

        wait = WebDriverWait(driver, 10)

        driver.get(url_for(ROOT, _external=True))
        sleep(3)
        try:
            element = driver.find_element(By.ID, 'logout')
            element.click()
        except NoSuchElementException:
            pass

        driver.get(url_for('auth_bp.orcid', _external=True))
        element = wait_load(wait, By.ID, 'signin-button')
        driver.find_element(By.ID, 'username').send_keys(login)
        driver.find_element(By.ID, 'password').send_keys(passw)
        element.click()
        element = wait_load(wait, By.ID, 'about-nav')
        assert element is not None
