import pytest
from project.gost_checker.checker import GOSTDocumentChecker

@pytest.fixture
def checker():
    return GOSTDocumentChecker(rules_file="app/gost_checker/rules/manual_rules.json")

def test_checker_init(checker):
    assert len(checker.rule_checker.get_all_rules()) > 0