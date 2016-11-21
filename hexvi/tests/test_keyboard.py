from io import BytesIO
import pytest
from typing import cast, Any
from hexvi.keyboard import (
    tokenize, StaticInputToken, NumberInputToken, BindingList)


def test_tokenize_with_simple_text() -> None:
    result = tokenize('abc')
    assert len(result) == 3
    assert isinstance(result[0], StaticInputToken)
    assert isinstance(result[1], StaticInputToken)
    assert isinstance(result[2], StaticInputToken)
    assert cast(StaticInputToken, result[0]).char == 'a'
    assert cast(StaticInputToken, result[1]).char == 'b'
    assert cast(StaticInputToken, result[2]).char == 'c'


def test_tokenize_with_escaped_text() -> None:
    result = tokenize('a\<\>')
    assert len(result) == 3
    assert isinstance(result[0], StaticInputToken)
    assert isinstance(result[1], StaticInputToken)
    assert isinstance(result[2], StaticInputToken)
    assert cast(StaticInputToken, result[0]).char == 'a'
    assert cast(StaticInputToken, result[1]).char == '<'
    assert cast(StaticInputToken, result[2]).char == '>'


def test_tokenize_with_simple_variables() -> None:
    result = tokenize('a<name:number>b')
    assert len(result) == 3
    assert isinstance(result[0], StaticInputToken)
    assert isinstance(result[1], NumberInputToken)
    assert isinstance(result[2], StaticInputToken)
    assert cast(StaticInputToken, result[0]).char == 'a'
    assert cast(StaticInputToken, result[2]).char == 'b'
    assert cast(NumberInputToken, result[1]).var_name == 'name'


def test_tokenize_with_escaped_variables() -> None:
    result = tokenize('<\x5C\x5Cname:number>')
    assert len(result) == 1
    assert isinstance(result[0], NumberInputToken)
    assert cast(NumberInputToken, result[0]).var_name == '\x5Cname'


def test_tokenize_with_variables_using_braces() -> None:
    result = tokenize('<\x5C<name\x5C>:number>')
    assert len(result) == 1
    assert isinstance(result[0], NumberInputToken)
    assert cast(NumberInputToken, result[0]).var_name == '<name>'


@pytest.mark.parametrize('text', [
    '<variable_with:unknown_type>',
    '<unnamed_variable>',
    '<unclosed:brace',
    '<unclosed_variable_backslash\\',
    'unclosed_plaintext_backslash\\',
])
def test_tokenize_with_erroreous_input(text: str) -> None:
    with pytest.raises(ValueError):
        result = tokenize(text)


def test_binding_single_key() -> None:
    result = None

    def command(**kwargs: Any) -> None:
        nonlocal result
        result = 'executed'

    binding_list = BindingList()
    binding_list.bind('a', command)

    assert result is None
    binding_list.accept_char('a')
    assert result == 'executed'


def test_accepting_unknown_key() -> None:
    result = None

    def command(**kwargs: Any) -> None:
        nonlocal result
        result = 'executed'

    binding_list = BindingList()
    binding_list.bind('q', command)

    assert result is None
    binding_list.accept_char('a')
    binding_list.accept_char('q')
    assert result == 'executed'


def test_binding_key_chain() -> None:
    result = None

    def command(**kwargs: Any) -> None:
        nonlocal result
        result = 'executed'

    binding_list = BindingList()
    binding_list.bind('abc', command)

    binding_list.accept_char('a')
    assert result is None
    binding_list.accept_char('b')
    assert result is None
    binding_list.accept_char('c')
    assert result == 'executed'


def test_binding_ambiguous_prefix() -> None:
    result = None

    def command1(**kwargs: Any) -> None:
        nonlocal result
        result = 'command1'

    def command2(**kwargs: Any) -> None:
        nonlocal result
        result = 'command2'

    binding_list = BindingList()
    binding_list.bind('abc', command1)
    binding_list.bind('acd', command2)

    binding_list.accept_char('a')
    assert result is None
    binding_list.accept_char('b')
    assert result is None
    binding_list.accept_char('c')
    assert result == 'command1'


@pytest.mark.parametrize('input,expected_result', [
    ('abc', None),
    ('acd', 'command2'),
    ('a1c', ('command1', {'test': 1})),
    ('a2c', ('command1', {'test': 2})),
    ('a22c', ('command1', {'test': 22})),
    ('a0c', ('command1', {'test': 0})),
    ('a0xc', None),
    ('a0x1c', ('command1', {'test': 1})),
    ('a0x10c', ('command1', {'test': 16})),
])
def test_binding_number_variables(input: str, expected_result: Any) -> None:
    result = None  # type: Any

    def command1(**kwargs: Any) -> None:
        nonlocal result
        result = 'command1', kwargs

    def command2(**kwargs: Any) -> None:
        nonlocal result
        result = 'command2'

    binding_list = BindingList()
    binding_list.bind('a<test:number>c', command1)
    binding_list.bind('acd', command2)

    for char in list(input):
        binding_list.accept_char(char)
    assert result == expected_result


@pytest.mark.parametrize('input,expected_result', [
    ('1c', ('command1', {'test': 1})),
    ('2c', ('command1', {'test': 2})),
    ('22c', ('command1', {'test': 22})),
    ('0c', ('command1', {'test': 0})),
    ('0x', ('command2', {'test': 0})),
    ('0xc', ('command2', {'test': 0})),
    ('0x1c', ('command1', {'test': 1})),
    ('0x10c', ('command1', {'test': 16})),
])
def test_binding_variable_conflicts(input: str, expected_result: Any) -> None:
    result = None  # type: Any

    def command1(**kwargs: Any) -> None:
        nonlocal result
        result = 'command1', kwargs

    def command2(**kwargs: Any) -> None:
        nonlocal result
        result = 'command2', kwargs

    binding_list = BindingList()
    binding_list.bind('<test:number>c', command1)
    binding_list.bind('<test:number>x', command2)

    for char in list(input):
        binding_list.accept_char(char)
    assert result == expected_result
