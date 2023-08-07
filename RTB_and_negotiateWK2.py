import sys
import json

from straders_sdk import SpaceTraders
from straders_sdk.utils import set_logging, sleep


def master(st: SpaceTraders):
    contracts = st.view_my_contracts()
    agent = st.view_my_self()
    ships = st.ships_view()

    ship = ships["CTRI-1"]
    for contract in contracts.values():
        if not contract.accepted:
            print("There is a pending contract! Accepted it for you.")
            st.contract_accept(contract.id)
            exit(0)
        if contract.accepted and not contract.fulfilled:
            for deliverable in contract.deliverables:
                print(
                    f"Delivering {deliverable.symbol} to {deliverable.destination_symbol}: {deliverable.units_fulfilled}/{deliverable.units_required} units"
                )
            st.ship_move(ship, agent.headquaters)
            sleep(ship.nav.travel_time_remaining + 1)
            resp = st.contracts_fulfill(contract)
            if resp:
                print("Contract fulfilled!")

    st.ship_move(ship, agent.headquaters)
    sleep(ship.nav.travel_time_remaining + 1)
    new_contract = st.ship_negotiate(ship)
    if new_contract:
        st.contract_accept(new_contract.id)


if __name__ == "__main__":
    tar_username = sys.argv[1] if len(sys.argv) > 1 else None

    out_file = f"procure-quest.log"
    set_logging(out_file)

    with open("user.json", "r") as j_file:
        users = json.load(j_file)
    found_user = users["agents"][0]
    for user in users["agents"]:
        if user["username"] == tar_username:
            found_user = user
    st = SpaceTraders(
        found_user["token"],
        db_host=users["db_host"],
        db_name=users["db_name"],
        db_user=users["db_user"],
        db_pass=users["db_pass"],
        db_port=users["db_port"],
    )

    master(st)
