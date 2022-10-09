import typing
import requests
from config import cfg

base_url = "https://api.trello.com/1"

headers = {"Accept": "application/json"}

query = {"key": cfg["trello"]["api_key"], "token": cfg["trello"]["token"]}


def get_boards() -> typing.List[typing.Dict]:
    q = {**query, "fields": "id,name"}
    response = requests.get(f"{base_url}/members/me/boards", headers=headers, params=q)
    return response.json()


def get_board_lists(board_id: str) -> typing.List[typing.Dict]:
    q = {**query, "fields": "id,name"}
    response = requests.get(
        f"{base_url}/boards/{board_id}/lists", headers=headers, params=q
    )
    return response.json()


def create_card(list_id: str, card_dict: typing.Dict) -> requests.Response:
    q = {**query, **card_dict}
    response = requests.post(f"{base_url}/cards", headers=headers, params=q)
    return response


def create_checklist_on_card(
    card_id: str, checklist_name: str, position: str = "top"
) -> typing.Dict:
    q = {**query, "name": checklist_name, "pos": position}
    response = requests.post(
        f"{base_url}/cards/{card_id}/checklists", headers=headers, params=q
    )
    return response.json()


def create_checkitem_on_checklist(checklist_id: str, checkitem_name: str):
    q = {**query, "name": checkitem_name}
    response = requests.post(
        f"{base_url}/checklists/{checklist_id}/checkItems", headers=headers, params=q
    )
    return response.json()
