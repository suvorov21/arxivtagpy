"""Test module with selenium."""
# pylint: disable=redefined-outer-name, no-self-use, unused-argument

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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException

import pytest

from app.model import db, User

ROOT = 'main_bp.root'
ROOT_PAPERS = 'main_bp.papers_list'
ROOT_SET = 'settings_bp.settings_page'
ROOT_LOGOUT = 'auth_bp.logout'
ROOT_ORCID = 'auth_bp.orcid'


@pytest.fixture(scope='module')
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
    driver.get(url_for(ROOT, _external=True))
    element = wait_load(wait, By.CLASS_NAME, 'btn-primary')
    try:
        if 'sleep' in kwargs:
            sleep(kwargs['sleep'])
        driver.find_element(By.NAME, 'i_login').send_keys(kwargs['login'])
        driver.find_element(By.NAME, 'i_pass').send_keys(kwargs['passw'])
        element.click()
    except NoSuchElementException:
        pass


def signout(driver, wait):
    """Sigh out function."""
    driver.get(url_for(ROOT_LOGOUT, _external=True))
    wait_load(wait, By.CLASS_NAME, 'btn-primary')


@pytest.mark.usefixtures('live_server')
class TestBasicViews:
    """Class for tests with visual driver."""
    def test_login(self, user, driver):
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
        signout(driver, wait)

    def test_paper_view(self, papers, user, driver):
        """Test paper view."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_PAPERS, _external=True))
        element = wait_load(wait, By.ID, 'paper-num-0')
        assert element.text == '1'

    def test_paper_selector(self, papers, user, driver):
        """Test paper selector href."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        # look at the last 3 days (in case of holidays, etc.
        recent_papers_exists = []
        for i in range(3):
            driver.get(url_for('main_bp.paper_land', _external=True))
            wait_load(wait, By.CLASS_NAME, 'paper-day')
            # go to DAY-2 as the last days may be holidays with no submissions
            driver.execute_script(f"document.getElementsByClassName('paper-day')[{i}].click()")
            element = wait_load(wait, By.ID, 'paper-num-0')
            recent_papers_exists.append(element.text == '1')

        assert any(recent_papers_exists)

    def test_paper_view_month(self, papers, user, driver):
        """Test paper view month."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT, _external=True) + '/papers?date=month')
        element = wait_load(wait, By.ID, 'paper-num-0')
        assert element.text == '1'

    def test_bookshelf_view(self, user, driver):
        """Test bookshelf page load properly."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for('main_bp.bookshelf', _external=True))
        element = wait_load(wait, By.ID, 'paper-list-title')
        load = driver.find_element(By.ID, 'loading-papers')
        display_load = load.value_of_css_property('display')
        assert element.text == 'Favourite'
        assert display_load == 'none'


@pytest.mark.usefixtures('live_server')
class TestSettingsUpdate:
    """Test settings modifications."""
    def test_settings_view(self, driver, user):
        """Test settings page load properly."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_SET,
                           page='cat',
                           _external=True
                           )
                   )
        element = wait_load(wait, By.ID, 'cat-name-hep-ex')
        assert element.text == 'High Energy Physics - Experiment'

    def test_delete_cat(self, driver, user):
        """Test category delete."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_SET,
                           page='cat',
                           _external=True))
        element = wait_load(wait, By.ID, 'close_hep-ex')
        element.click()
        sleep(1)
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        element = wait_load(wait, By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_tag(self, driver, user):
        """Test tag modifications."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_SET,
                           page='tag',
                           _external=True
                           ))
        element = wait_load(wait, By.CLASS_NAME, 'tag-label')
        element.click()
        element = wait_load(wait, By.ID, 'tag-name')
        element.send_keys('test_test')
        driver.find_element(By.CLASS_NAME, 'btn-success').click()
        sleep(1)
        element = wait_load(wait, By.CLASS_NAME, 'tag-label')
        element.click()
        new_val = driver.find_element(By.ID, 'tag-name').get_attribute("value")
        assert new_val == 'exampletest_test'

    def test_del_tag(self, driver, user):
        """Test tag modifications."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_SET,
                           page='tag',
                           _external=True
                           ))
        element = wait_load(wait, By.CLASS_NAME, 'tag-label')
        element.click()
        element = wait_load(wait, By.ID, 'btn-del')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'btn-success')
        element.click()
        element = wait_load(wait, By.CLASS_NAME, 'alert-dismissible')
        assert 'success' in element.get_attribute('class')

    def test_mod_pref(self, driver, user):
        """Test preference modifications."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
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

    def test_mod_book(self, user, driver):
        """Test bookmarks modifications."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
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

    def test_add_book(self, driver, user):
        """Test add bookmarks."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_SET,
                           page='bookshelf',
                           _external=True
                           ))
        element = wait_load(wait, By.ID, 'new-list')
        element.send_keys('new_list')
        driver.find_element(By.ID, 'add-book-btn').click()
        sleep(1)

        assert 'new_list' in driver.page_source

    def test_btn_save(self, driver, user):
        """Test if save button become active on change on settings page."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
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

    def test_cookies(self, driver, user):
        """Test cookies."""
        wait = WebDriverWait(driver, 10)
        signin(driver, wait, login=EMAIL, passw=PASS)
        driver.get(url_for(ROOT_PAPERS, _external=True))
        element = wait_load(wait, By.ID, 'check-nov-1')
        assert element.is_selected()
        element.click()
        driver.get(url_for(ROOT_PAPERS, _external=True))
        element = wait_load(wait, By.ID, 'check-nov-1')
        assert not element.is_selected()

    # def test_csrf(self, client, user, driver):
    #     wait = WebDriverWait(driver, 10)
    #     client.application.config['WTF_CSRF_ENABLED'] = True
    #     client.application.config['WTF_CSRF_TIME_LIMIT'] = 1
    #     signout(driver, wait)
    #     signin(driver, wait, login=EMAIL, passw=PASS, sleep=10)
    #     wait_load(wait, By.CLASS_NAME, 'btn-primary')
    #     assert 'About' not in driver.page_source
    #     client.application.config['WTF_CSRF_ENABLED'] = False


# @pytest.mark.usefixtures('live_server')
# class TestOrcid:
#     """Test ORCID authorization."""
#     @check_orcid_credits
#     def test_orcid_auth(self, driver, user, **kwargs):
#         """Test ORCID authentication."""
#         wait = WebDriverWait(driver, 20)
#         signout(driver, wait)
#
#         # register new user with ORCID
#         driver.get(url_for(ROOT_ORCID, _external=True))
#         orcid_signin(driver, wait, **kwargs)
#         element = wait_load(wait, By.ID, 'about-nav')
#         assert element is not None
#         # tear down
#         User.query.filter(User.orcid is not None).delete()
#         db.session.commit()
#
#     @check_orcid_credits
#     def test_orcid_second_registration(self, driver, user, tmp_user, **kwargs):
#         """Try to link existing ORCID."""
#         wait = WebDriverWait(driver, 10)
#         signout(driver, wait)
#
#         # register new user with ORCID
#         driver.get(url_for(ROOT_ORCID, _external=True))
#         orcid_signin(driver, wait, **kwargs)
#         wait_load(wait, By.ID, 'about-nav')
#         signout(driver, wait)
#
#         # sign in other user credentials
#         signin(driver, wait, login=TMP_EMAIL, passw=TMP_PASS)
#         wait_load(wait, By.ID, 'about-nav')
#
#         # Try to link existing orcid
#         driver.get(url_for(ROOT_ORCID, _external=True))
#         orcid_signin(driver, wait, **kwargs)
#         wait_load(wait, By.ID, 'about-nav')
#
#         assert 'already registered!' in driver.page_source
#         assert 'successfully' not in driver.page_source
#         assert 'ERROR' in driver.page_source
#         # tear down
#         User.query.filter(User.orcid is not None).delete()
#         db.session.commit()
#
#     @check_orcid_credits
#     def test_email_creation(self, driver, user, **kwargs):
#         """Test email creation for the record with ORCID registration."""
#         wait = WebDriverWait(driver, 10)
#         signout(driver, wait)
#         # sign in (create a bew user)
#         driver.get(url_for(ROOT_ORCID, _external=True))
#         orcid_signin(driver, wait, **kwargs)
#         wait_load(wait, By.ID, 'about-nav')
#         # Try with existing email (FAIL)
#         driver.get(url_for(ROOT_SET, page='pref', _external=True))
#         wait_load(wait, By.ID, 'emailChange').click()
#         wait_load(wait, By.ID, 'emailInput').send_keys(EMAIL)
#         wait_load(wait, By.ID, 'confirm-btn').click()
#         sleep(1)
#         wait_load(wait, By.ID, 'btn-confirm').click()
#         wait_load(wait, By.CLASS_NAME, 'btn-primary')
#         assert 'successfully!' not in driver.page_source
#         assert 'already registered' in driver.page_source
#         # Try with new email
#         driver.get(url_for(ROOT_SET, page='pref', _external=True))
#         wait_load(wait, By.ID, 'emailChange').click()
#         wait_load(wait, By.ID, 'emailInput').send_keys('tester5@mailinator.com')
#         wait_load(wait, By.ID, 'confirm-btn').click()
#         sleep(1)
#         wait_load(wait, By.ID, 'btn-confirm').click()
#         wait_load(wait, By.CLASS_NAME, 'btn-primary')
#         assert 'successfully!' in driver.page_source
#         # tear down
#         User.query.filter_by(email='tester5@mailinator.com').delete()
#         User.query.filter(User.orcid is not None).delete()
#         db.session.commit()
#
#     @check_orcid_credits
#     def test_orcid_failed_unlink(self, driver, user, **kwargs):
#         """Test ORCID link/unlink."""
#         wait = WebDriverWait(driver, 10)
#         signout(driver, wait)
#         # sign in (create new user)
#         driver.get(url_for(ROOT_ORCID, _external=True))
#         orcid_signin(driver, wait, **kwargs)
#         wait_load(wait, By.ID, 'about-nav')
#
#         # try to unlink (FAIL)
#         driver.get(url_for(ROOT_SET, page='pref', _external=True))
#         wait_load(wait, By.ID, 'orcidAuthButton').click()
#         wait_load(wait, By.ID, 'logout')
#         assert 'ERROR' in driver.page_source
#         assert 'Could not unlink' in driver.page_source
#         # tear down
#         User.query.filter(User.orcid is not None).delete()
#         db.session.commit()
#
#     @check_orcid_credits
#     def test_orcid_unlink(self, driver, user, **kwargs):
#         """Check successful ORCID unlink."""
#         User.query.filter_by(email=EMAIL).first().orcid = None
#         db.session.commit()
#
#         wait = WebDriverWait(driver, 10)
#         signout(driver, wait)
#         signin(driver, wait, login=EMAIL, passw=PASS)
#         wait_load(wait, By.ID, 'about-nav')
#
#         driver.get(url_for(ROOT_SET, page='pref', _external=True))
#         wait_load(wait, By.ID, 'orcidAuthButton').click()
#         orcid_signin(driver, wait, **kwargs)
#         sleep(3)
#         assert 'ORCID linked successfully' in driver.page_source
#         driver.get(url_for(ROOT_SET, page='pref', _external=True))
#         wait_load(wait, By.ID, 'orcidAuthButton').click()
#         sleep(1)
#         assert 'ORCID unlinked successfully' in driver.page_source
