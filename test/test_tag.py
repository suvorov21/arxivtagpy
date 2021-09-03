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
    assert tag_test(simple_paper, 'ti{awesome}') == True
    assert tag_test(simple_paper, 'abs{breakthrough}') == True
    assert tag_test(simple_paper, 'au{Au1}') == True


def test_and_or_outside(simple_paper):
    """Test logic operators in between the simple rules."""
    assert tag_test(simple_paper, 'ti{awesome}&abs{breakthrough}') == True
    assert tag_test(simple_paper, 'ti{awesome}&abs{awesome}') == False
    assert tag_test(simple_paper, 'ti{awesome}|abs{awesome}') == True

def test_and_or_inside(simple_paper):
    """Test logic operators in inside the simple rules."""
    assert tag_test(simple_paper, 'ti{awesome&title}') == True
    assert tag_test(simple_paper, 'ti{awesome|breakthrough}') == True

def test_tricky_logic_and():
    """Test logic end versus sequence."""
    paper = {'abstract': 'Look for neutrino with heavy detector'}
    rule = 'abs{heavy&neutrino|HNL}|ti{heavy&neutrino|HNL}'

    assert tag_test(paper, rule) == True

    paper = {'abstract': 'Look for neutrino with heavy detector'}
    rule = 'abs{heavy neutrino|HNL}|ti{heavy neutrino|HNL}'

    assert tag_test(paper, rule) == False
