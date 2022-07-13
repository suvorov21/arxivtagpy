"""Test paper tagging feature."""
# pylint: disable=redefined-outer-name, unused-argument

from copy import copy
from typing import Generator
from flask import url_for
import pytest

from app.papers import tag_suitable
from app.interfaces.data_structures import PaperInterface


@pytest.fixture(scope='function')
def simple_paper() -> Generator[PaperInterface, None, None]:
    """Fixture with a simple paper."""
    paper = PaperInterface.for_tests('Awesome title',
                                     ['Au1', 'Au2'],
                                     'Breakthrough is coming'
                                     )
    yield paper


def test_base(simple_paper):
    """Check if the simple rules are working."""
    assert tag_suitable(simple_paper, 'ti{awesome}')
    assert tag_suitable(simple_paper, 'abs{breakthrough}')
    assert tag_suitable(simple_paper, 'au{Au1}')


def test_and_or_outside(simple_paper):
    """Test logic operators in between the simple rules."""
    assert tag_suitable(simple_paper, 'ti{awesome}&abs{breakthrough}')
    assert not tag_suitable(simple_paper, 'ti{awesome}&abs{awesome}')
    assert tag_suitable(simple_paper, 'ti{awesome}|abs{awesome}')


def test_and_or_inside(simple_paper):
    """Test logic operators in inside the simple rules."""
    assert tag_suitable(simple_paper, 'ti{awesome&title}')
    assert tag_suitable(simple_paper, 'ti{awesome|breakthrough}')


def test_tricky_logic_and(simple_paper):
    """Test logic end versus sequence."""
    simple_paper.abstract = 'Look for neutrino with heavy detector'
    rule = 'abs{heavy&neutrino|HNL}|ti{heavy&neutrino|HNL}'

    assert tag_suitable(simple_paper, rule)

    simple_paper.abstract = 'Look for neutrino with heavy detector'
    rule = 'abs{heavy neutrino|HNL}|ti{heavy neutrino|HNL}'

    assert not tag_suitable(simple_paper, rule)

def test_negation(simple_paper):
    """Test negation in the tag rule."""
    paper_good = copy(simple_paper)
    paper_bad = copy(simple_paper)

    paper_good.author = ['Myself']

    rule = 'abs{Breakthrough}&au{!Au2}'
    assert tag_suitable(paper_good, rule)
    assert not tag_suitable(paper_bad, rule)


def test_tag_endpoint(client, login):
    """Test the tag test endpoint."""
    response = client.get(url_for('main_bp.test_tag',
                                  title='Awesome title',
                                  rule='ti{awesome}')
                          )
    assert 'true' in response.get_data(as_text=True)
