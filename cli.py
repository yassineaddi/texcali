import argparse
import json
import pathlib
import sys
import textwrap
import typing
from time import sleep

import colored
import emoji
from colored import stylize
from simple_term_menu import TerminalMenu

import excalidraw
import trello_client
from config import cfg

trello_cfg = cfg["trello"]


def extract_tickets_from_excalidraw(
    excalidraw_path: pathlib.Path,
) -> typing.List[excalidraw.Ticket]:
    excalidraw_str = pathlib.Path(excalidraw_path).read_text(encoding="utf-8")
    try:
        state = json.loads(excalidraw_str)
        tickets = excalidraw.create_tickets(state)
        assert state.get("type") == "excalidraw"
        assert state.get("version") == 2
    except Exception as e:
        print(stylize(e, colored.fg("red")))
        sys.exit()
    if not tickets:
        print(stylize("Couldn't find any tickets", colored.fg("yellow")))
        sys.exit()
    print(
        emoji.emojize(
            f":sparkles: Found {len(tickets)} ticket{'s' if len(tickets) > 1 else ''}!",
            language="alias",
        )
    )
    return tickets


def select_board() -> typing.Dict:
    boards = trello_client.get_boards()
    terminal_menu = TerminalMenu(
        map(lambda board: board["name"], boards), title="Boards"
    )
    menu_entry_index = terminal_menu.show()
    if menu_entry_index is None:
        print(stylize("abort", colored.fg("dark_gray")))
        sys.exit()
    return boards[menu_entry_index]


def select_board_list(board_id: str) -> typing.Dict:
    board_lists = trello_client.get_board_lists(board_id)
    terminal_menu = TerminalMenu(
        map(lambda board_list: board_list["name"], board_lists),
        title="Lists",
    )
    menu_entry_index = terminal_menu.show()
    if menu_entry_index is None:
        print(stylize("abort", colored.fg("dark_gray")))
        sys.exit()
    return board_lists[menu_entry_index]


def print_tickets(tickets: typing.List[excalidraw.Ticket]) -> None:
    print(
        "\n"
        + "\n".join(
            textwrap.shorten(
                "- " + ticket.to_trello_card().get("name"), width=60, placeholder="..."
            )
            for ticket in tickets
        )
    )
    sys.exit()


def create_tickets(board_list_id: str, tickets: typing.List[excalidraw.Ticket]) -> None:
    for index, ticket in enumerate(tickets):
        payload = ticket.to_trello_card(board_list_id)
        response = trello_client.create_card(board_list_id, payload)
        card = response.json()
        ticket.card_id = card.get("id")
        ticket.short_url = card.get("shortUrl")
        print(
            emoji.emojize(
                f":white_check_mark: [{response.status_code}] Created ticket '{textwrap.shorten(card.get('name'), width=60, placeholder='...')}'",
                language="alias",
            )
        )
        if not ticket.ac:
            continue
        sleep(0.5)
        checklist = trello_client.create_checklist_on_card(
            card.get("id"), trello_cfg.get("ac_checklist_title", "Acceptance Criteria")
        )
        for item in ticket.ac:
            sleep(0.5)
            trello_client.create_checkitem_on_checklist(checklist.get("id"), item)
        if index != len(tickets) - 1:
            sleep(1)
    print("")


def create_ticket_dependencies(tickets: typing.List[excalidraw.Ticket]) -> None:
    print(stylize(f"Creating dependencies...", colored.fg("light_gray")), end="\r")
    for index, ticket in enumerate(tickets):
        if not ticket.dependents and not ticket.depends_on:
            continue
        if ticket.depends_on:
            checklist = trello_client.create_checklist_on_card(
                ticket.card_id,
                trello_cfg.get("prerequisites_checklist_title", "Pre-requisite Cards"),
            )
            checklist_id = checklist.get("id")
            for inner_ticket in ticket.depends_on:
                sleep(0.5)
                trello_client.create_checkitem_on_checklist(
                    checklist_id, inner_ticket.short_url
                )
        if ticket.dependents:
            checklist = trello_client.create_checklist_on_card(
                ticket.card_id,
                trello_cfg.get("dependents_checklist_title", "Dependent Cards"),
            )
            checklist_id = checklist.get("id")
            for inner_ticket in ticket.dependents:
                sleep(0.5)
                trello_client.create_checkitem_on_checklist(
                    checklist_id, inner_ticket.short_url
                )
        if index != len(tickets) - 1:
            sleep(1)
    print(emoji.emojize(":zap: Created dependencies!", language="alias"), end="\n\n")


def main(
    excalidraw_path: pathlib.Path, print_only: bool = False, ignore_deps: bool = False
):
    tickets = extract_tickets_from_excalidraw(excalidraw_path)
    if print_only:
        print_tickets(tickets)
    selected_board = select_board()
    print(stylize(selected_board.get("name"), colored.fg("light_gray")))
    selected_board_list = select_board_list(selected_board.get("id"))
    print(
        stylize(selected_board_list.get("name"), colored.fg("light_gray")), end="\n\n"
    )
    create_tickets(selected_board_list.get("id"), tickets)
    if not ignore_deps:
        create_ticket_dependencies(tickets)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="texcali")
    parser.add_argument("excalidraw_path", type=pathlib.Path)
    parser.add_argument(
        "--print", dest="print_only", help="only print tickets", action="store_true"
    )
    parser.add_argument(
        "--ignore-deps",
        dest="ignore_deps",
        help="ignores dependencies between tickets, thus they will not be created",
        action="store_true",
    )
    args = parser.parse_args()
    try:
        main(args.excalidraw_path, args.print_only, args.ignore_deps)
    except KeyboardInterrupt:
        print(stylize("Interrupted.", colored.fg("dark_gray")))
