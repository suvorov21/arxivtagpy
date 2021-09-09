"""Test paper tagging feature."""
# pylint: disable=redefined-outer-name, unused-argument

from flask import url_for
import pytest

from app.papers import tag_test

@pytest.fixture(scope='function')
def simple_paper():
    """Fixture with a simple paper."""
    paper = {'title': 'Awesome title',
             'author': 'Au1, Au2',
             'abstract': 'Breakthrough is coming'
             }
    yield paper

def test_base(simple_paper):
    """Check if the simple rules are working."""
    assert tag_test(simple_paper, 'ti{awesome}')
    assert tag_test(simple_paper, 'abs{breakthrough}')
    assert tag_test(simple_paper, 'au{Au1}')


def test_and_or_outside(simple_paper):
    """Test logic operators in between the simple rules."""
    assert tag_test(simple_paper, 'ti{awesome}&abs{breakthrough}')
    assert not tag_test(simple_paper, 'ti{awesome}&abs{awesome}')
    assert tag_test(simple_paper, 'ti{awesome}|abs{awesome}')

def test_and_or_inside(simple_paper):
    """Test logic operators in inside the simple rules."""
    assert tag_test(simple_paper, 'ti{awesome&title}')
    assert tag_test(simple_paper, 'ti{awesome|breakthrough}')

def test_tricky_logic_and():
    """Test logic end versus sequence."""
    paper = {'abstract': 'Look for neutrino with heavy detector'}
    rule = 'abs{heavy&neutrino|HNL}|ti{heavy&neutrino|HNL}'

    assert tag_test(paper, rule)

    paper = {'abstract': 'Look for neutrino with heavy detector'}
    rule = 'abs{heavy neutrino|HNL}|ti{heavy neutrino|HNL}'

    assert not tag_test(paper, rule)

def test_tag_endpoint(client, login):
    """Test the tag test endpoint."""
    response = client.get(url_for('main_bp.test_tag',
                                  title='Awesome title',
                                  rule='ti{awesome}')
                          )
    assert 'true' in response.get_data(as_text=True)
