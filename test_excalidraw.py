import pytest
import excalidraw
import nanoid


@pytest.fixture
def base_element_fixture_factory():
    def _generate_fixture():
        return {"id": nanoid.generate()}

    return _generate_fixture


@pytest.fixture
def text_element_fixture(base_element_fixture_factory):
    return {
        **base_element_fixture_factory(),
        "type": "text",
        "text": "---\nticket",
        "originalText": "---\nticket",
    }


@pytest.fixture
def text_element_fixture_factory(text_element_fixture, base_element_fixture_factory):
    def _generate_fixture():
        return {**text_element_fixture, **base_element_fixture_factory()}

    return _generate_fixture


@pytest.fixture
def arrow_element_fixture(base_element_fixture_factory):
    return {
        **base_element_fixture_factory(),
        "type": "arrow",
        "startBinding": {
            "elementId": None,
        },
        "endBinding": {
            "elementId": None,
        },
    }


@pytest.fixture
def empty_state_fixture():
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": [],
        "appState": {
            "viewBackgroundColor": "#ffffff",
            "gridSize": None,
        },
        "files": {},
    }


@pytest.fixture
def simple_state_fixture(
    empty_state_fixture, text_element_fixture_factory, arrow_element_fixture
):
    (text_element1, text_element2) = [text_element_fixture_factory() for _ in range(2)]
    arrow_element_fixture["startBinding"]["elementId"] = text_element1["id"]
    arrow_element_fixture["endBinding"]["elementId"] = text_element2["id"]

    return {
        **empty_state_fixture,
        "elements": [text_element1, text_element2, arrow_element_fixture],
    }


def test_create_tickets_returns_two_tickets(simple_state_fixture):
    expected = [
        excalidraw.Ticket(id=el["id"], title="ticket")
        for el in simple_state_fixture["elements"][:2]
    ]

    actual = excalidraw.create_tickets(simple_state_fixture)

    assert sorted(actual) == sorted(expected)


def test_create_tickets_returns_tickets_that_begin_with_three_hyphens(
    simple_state_fixture, text_element_fixture_factory
):
    state_elements = simple_state_fixture["elements"]
    expected = [
        excalidraw.Ticket(id=el["id"], title="ticket") for el in state_elements[:2]
    ]

    state_elements.append(
        {
            **text_element_fixture_factory(),
            "text": "foo bar\n",
            "originalText": "foo bar\n",
        }
    )

    actual = excalidraw.create_tickets(simple_state_fixture)

    assert sorted(actual) == sorted(expected)


def test_create_tickets_creates_dependency_between_two_tickets(
    simple_state_fixture,
):
    [ticket1, ticket2] = excalidraw.create_tickets(simple_state_fixture)

    assert list(ticket1.dependents) == [ticket2]
    assert list(ticket2.depends_on) == [ticket1]


def test_create_tickets_maps_text_as_title_when_given_no_keys(
    empty_state_fixture, text_element_fixture
):
    title = "AaDev I have an ADR for Foobar"
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": f"---\n{title}",
            "originalText": f"---\n{title}",
        }
    )

    [ticket] = excalidraw.create_tickets(empty_state_fixture)

    assert ticket.title == title


def test_create_tickets_maps_title_key(empty_state_fixture, text_element_fixture):
    title = "AAFoo I want to bar so that baz"
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": f"---\ntitle: {title}",
            "originalText": f"---\ntitle: {title}",
        }
    )

    [ticket] = excalidraw.create_tickets(empty_state_fixture)

    assert ticket.title == title


def test_create_tickets_maps_other_keys(empty_state_fixture, text_element_fixture):
    title = "title"
    points = 5
    ac = "  - abc\n  - xyz"
    desc = "description"
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": f"---\ntitle: {title}\npoints: {points}\nac:\n{ac}\ndesc: {desc}",
            "originalText": f"---\ntitle: {title}\npoints: {points}\nac: {ac}\ndesc: {desc}",
        }
    )

    [ticket] = excalidraw.create_tickets(empty_state_fixture)

    assert ticket.title == title
    assert ticket.points == points
    assert ticket.ac == ["abc", "xyz"]
    assert ticket.desc == desc


def test_create_tickets_raises_value_error_when_ac_is_not_a_list(
    empty_state_fixture, text_element_fixture
):
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": "---\ntitle: abc\nac: |-\n  - first\n  - second",
            "originalText": "---\ntitle: abc\nac: |-\n  - first\n  - second",
        }
    )

    try:
        excalidraw.create_tickets(empty_state_fixture)
    except ValueError:
        pass
    else:
        assert False, "Should raise a ValueError"


def test_create_tickets_raises_attribute_error(
    empty_state_fixture, text_element_fixture
):
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": "---\ntitle: abc\nx: y",
            "originalText": "---\ntitle: abc\nx: y",
        }
    )

    try:
        excalidraw.create_tickets(empty_state_fixture)
    except TypeError:
        pass
    else:
        assert False, "Should raise a TypeError"


def test_create_tickets_ignores_id(empty_state_fixture, text_element_fixture):
    id = "123"
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": f"---\nid: {id}\ntitle: abc",
            "originalText": f"---\nid: {id}\ntitle: abc",
        }
    )

    [ticket] = excalidraw.create_tickets(empty_state_fixture)
    assert ticket.id != id


def test_ticket_to_trello_card_appends_points_to_card_title(
    empty_state_fixture, text_element_fixture
):
    empty_state_fixture["elements"].append(
        {
            **text_element_fixture,
            "text": f"---\ntitle: >-\n  foo\n  bar\npoints: 3.5",
            "originalText": f"---\ntitle: >-\n  foo\n  bar\npoints: 3.5",
        }
    )

    expected_title = "(3.5) foo bar"

    [ticket] = excalidraw.create_tickets(empty_state_fixture)
    card_dict = ticket.to_trello_card()
    assert card_dict.get("name") == expected_title
