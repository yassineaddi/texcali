import typing
from dataclasses import dataclass, field

import yaml


@dataclass(kw_only=True, eq=True, order=True)
class Ticket:
    id: str
    title: str
    points: float = None
    ac: typing.Union[str, typing.List[str]] = None  # acceptance criteria
    desc: str = None
    card_id: str = field(init=False, compare=False, default=None)
    short_url: str = field(init=False, compare=False, default=None)
    dependents: typing.Set = field(
        init=False, compare=False, repr=False, default_factory=set
    )
    depends_on: typing.Set = field(
        init=False, compare=False, repr=False, default_factory=set
    )

    def __hash__(self):
        return hash(self.id)

    def add_dependency(self, ticket) -> None:
        self.depends_on.add(ticket)
        ticket.dependents.add(self)

    def to_trello_card(self, list_id: str = None) -> typing.Dict:
        card_dict = {"idList": list_id, "desc": self.desc if self.desc else ""}
        card_dict["name"] = (
            f"({self.points}) {self.title}" if self.points is not None else self.title
        )
        return card_dict


def create_tickets(state: typing.Dict) -> typing.List[Ticket]:
    text_elements = filter(
        lambda el: el["type"] == "text" and el["text"][:4] == "---\n",
        state.get("elements", []),
    )

    id_to_ticket = {}
    for el in text_elements:
        data = yaml.safe_load(el["text"])
        if isinstance(data, str):
            data = dict(title=data)
        # check that AC is a sequence
        if data.get("ac") and not isinstance(data.get("ac"), list):
            raise ValueError("AC should be a YAML sequence")
        if data.get("id"):
            del data["id"]
        id_to_ticket[el["id"]] = Ticket(id=el["id"], **data)

    arrow_elements = filter(
        lambda el: el["type"] == "arrow"
        and el.get("startBinding")
        and el.get("startBinding").get("elementId"),
        state.get("elements", []),
    )
    for el in arrow_elements:
        from_ticket = id_to_ticket.get(el["startBinding"]["elementId"])
        to_ticket = id_to_ticket.get(el["endBinding"]["elementId"])
        if from_ticket and to_ticket:
            to_ticket.add_dependency(from_ticket)

    return list(id_to_ticket.values())
