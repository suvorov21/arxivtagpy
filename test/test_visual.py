"""Test module with selenium."""
# pylint: disable=redefined-outer-name, no-self-use

from time import sleep
from os import environ
from functools import wraps

from test.conftest import EMAIL, PASS, TMP_EMAIL, TMP_PASS

from flask import url_for

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import pytest

ROOT = 'main_bp.root'
ROOT_PAPERS = 'main_bp.papers_list'
ROOT_SET = 'settings_bp.settings_page'
ROOT_LOGOUT = 'auth_bp.logout'


@pytest.fixture(scope='session')
def driver():
    """Create chrome driver."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(options=options)
    yield driver


def wait_load(wait, by_parameter, name):
    """Helper function to wait for element load."""
    return wait.until(EC.element_to_be_clickable((by_parameter, name)))


def check_orcid_credits(funct):
    """Check if the ORCID credits are in ENV."""

    @wraps(funct)
    def my_wrapper(*args, **kwargs):
        kwargs['login'] = environ.get('ORCID_NAME')
        kwargs['passw'] = environ.get('ORCID_PASSW')
        if not kwargs['login'] or not kwargs['passw']:
            print('WARNING! Test is skipped as no ORCID credentials are provided')
            assert True
            return None

        return funct(*args, **kwargs)

    return my_wrapper


def orcid_signin(driver, wait, **kwargs):
    """Attempt to sign in ORCID system."""
    try:
        element = wait_load(wait, By.ID, 'signin-button')
        driver.find_element(By.ID, 'username').send_keys(kwargs['login'])
        driver.find_element(By.ID, 'password').send_keys(kwargs['passw'])
        element.click()
    except TimeoutException:
        pass


def signin(driver, wait, **kwargs):
    """Sign in the website."""
    element = wait_load(wait, By.CLASS_NAME, 'btn-primary')
    driver.find_element(By.NAME, 'i_login').send_keys(kwargs['login'])
    driver.find_element(By.NAME, 'i_pass').send_keys(kwargs['passw'])
    element.click()


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
        signin(driver, wait, login=EMAIL, passw=PASS)
        element = wait_load(wait, By.ID, 'about-nav')
        assert element is not None

    def test_registration(self, driver):
        """Test login form."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for('auth_bp.signup', _external=True))
        element = wait_load(wait, By.ID, 'signup')

        driver.find_element(By.NAME, 'email').send_keys(TMP_EMAIL)
        driver.find_element(By.NAME, 'pasw').send_keys(TMP_PASS)
        driver.find_element(By.NAME, 'pasw2').send_keys(TMP_PASS)
        element.click()

        element = wait_load(wait, By.ID, 'about-nav')
        assert element is not None

        # restore login to main test user
        # sign out
        driver.get(url_for(ROOT, _external=True))
        element = wait_load(wait, By.ID, 'logout')
        element.click()
        # sign in
        signin(driver, wait, login=EMAIL, passw=PASS)
        wait_load(wait, By.ID, 'about-nav')

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

    @check_orcid_credits
    def test_orcid_auth(self, driver, **kwargs):
        """Test ORCID authentication."""
        wait = WebDriverWait(driver, 20)

        # sign out
        driver.get(url_for(ROOT_LOGOUT, _external=True))
        wait_load(wait, By.CLASS_NAME, 'btn-primary')

        driver.get(url_for('auth_bp.orcid', _external=True))
        orcid_signin(driver, wait, **kwargs)
        element = wait_load(wait, By.ID, 'about-nav')
        assert element is not None

    @check_orcid_credits
    def test_orcid_second_registration(self, driver, **kwargs):
        """Try to register with existing ORCID."""
        wait = WebDriverWait(driver, 10)

        # sign out
        driver.get(url_for(ROOT_LOGOUT, _external=True))

        # sign in other user credentials
        signin(driver, wait, login=TMP_EMAIL, passw=TMP_PASS)
        wait_load(wait, By.ID, 'about-nav')

        # Try to register with the same orcid
        driver.get(url_for('auth_bp.orcid', _external=True))
        orcid_signin(driver, wait, **kwargs)
        wait_load(wait, By.ID, 'about-nav')

        assert 'already registered!' in driver.page_source
        assert 'successfully' not in driver.page_source
        assert 'ERROR' in driver.page_source

    @check_orcid_credits
    def test_email_creation(self, driver, **kwargs):
        """Test email creation for the record with ORCID registration."""
        wait = WebDriverWait(driver, 10)
        # sign out
        driver.get(url_for(ROOT_LOGOUT, _external=True))
        wait_load(wait, By.CLASS_NAME, 'btn-primary')
        # sign in
        driver.get(url_for('auth_bp.orcid', _external=True))
        orcid_signin(driver, wait, **kwargs)
        wait_load(wait, By.ID, 'about-nav')
        # Try with existing email (FAIL)
        driver.get(url_for(ROOT_SET, page='pref', _external=True))
        wait_load(wait, By.ID, 'emailChange').click()
        wait_load(wait, By.ID, 'emailInput').send_keys(EMAIL)
        wait_load(wait, By.ID, 'confirm-btn').click()
        sleep(1)
        wait_load(wait, By.ID, 'btn-confirm').click()
        wait_load(wait, By.CLASS_NAME, 'btn-primary')
        assert 'successfully!' not in driver.page_source
        assert 'already registered' in driver.page_source
        # Try with new email
        driver.get(url_for(ROOT_SET, page='pref', _external=True))
        wait_load(wait, By.ID, 'emailChange').click()
        wait_load(wait, By.ID, 'emailInput').send_keys('tester5@mailinator.com')
        wait_load(wait, By.ID, 'confirm-btn').click()
        sleep(1)
        wait_load(wait, By.ID, 'btn-confirm').click()
        wait_load(wait, By.CLASS_NAME, 'btn-primary')
        assert 'successfully!' in driver.page_source

    @check_orcid_credits
    def test_orcid_failed_unlink(self, driver, **kwargs):
        """Test ORCID link/unlink."""
        wait = WebDriverWait(driver, 10)
        # sign out
        driver.get(url_for(ROOT_LOGOUT, _external=True))
        wait_load(wait, By.CLASS_NAME, 'btn-primary')
        # sign in
        driver.get(url_for('auth_bp.orcid', _external=True))
        orcid_signin(driver, wait, **kwargs)
        wait_load(wait, By.ID, 'about-nav')

        # try to unlink (FAIL)
        driver.get(url_for(ROOT_SET, page='pref', _external=True))
        wait_load(wait, By.ID, 'orcidAuthButton').click()
        wait_load(wait, By.ID, 'logout')
        assert 'ERROR' in driver.page_source
        assert 'Could not unlink' in driver.page_source
        # delete account
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        sleep(1)
        driver.find_element(By.ID, 'deleteAcc').click()
        sleep(1)
        wait_load(wait, By.ID, 'btn-confirm').click()
        wait_load(wait, By.CLASS_NAME, 'btn-primary')

    @check_orcid_credits
    def test_orcid_unlink(self, driver, **kwargs):
        """Check successful ORCID unlink."""
        wait = WebDriverWait(driver, 10)
        driver.get(url_for(ROOT, _external=True))
        signin(driver, wait, login=EMAIL, passw=PASS)
        wait_load(wait, By.ID, 'about-nav')

        driver.get(url_for(ROOT_SET, page='pref', _external=True))
        wait_load(wait, By.ID, 'orcidAuthButton').click()
        orcid_signin(driver, wait, **kwargs)
        sleep(3)
        assert 'ORCID linked successfully' in driver.page_source
        driver.get(url_for(ROOT_SET, page='pref', _external=True))
        wait_load(wait, By.ID, 'orcidAuthButton').click()
        sleep(1)
        assert 'ORCID unlinked successfully' in driver.page_source
