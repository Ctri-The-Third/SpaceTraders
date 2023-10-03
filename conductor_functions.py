from straders_sdk import SpaceTraders
from straders_sdk.contracts import Contract
from straders_sdk.utils import try_execute_select, try_execute_upsert, waypoint_slicer
from straders_sdk.local_response import LocalSpaceTradersRespose

import logging
import json
import hashlib


def process_contracts(client: SpaceTraders):
    contracts = client.view_my_contracts()
    need_to_negotiate = True
    for con in contracts:
        con: Contract
        should_we_complete = False

        if con.accepted and not con.fulfilled:
            should_we_complete = True

            need_to_negotiate = False
            for deliverable in con.deliverables:
                if deliverable.units_fulfilled < deliverable.units_required:
                    should_we_complete = False
        if should_we_complete:
            client.contracts_fulfill(con)

        if not con.accepted:
            need_to_negotiate = False
            if should_we_accept_contract(client, con):
                client.contract_accept(con.id)
    if need_to_negotiate:
        # get ships at the HQ, and have one do the thing
        ships = client.ships_view()
        satelite = [ship for ship in ships.values() if ship.role == "SATELLITE"][0]
        client.ship_negotiate(satelite)


def should_we_accept_contract(client: SpaceTraders, contract: Contract):
    deliverable_goods = [deliverable.symbol for deliverable in contract.deliverables]
    for dg in deliverable_goods:
        if "ORE" in dg:
            return True

    # get average and best price for deliverael
    total_value = contract.payment_completion + contract.payment_upfront
    total_cost = 0
    for deliverable in contract.deliverables:
        cost = get_prices_for(client, deliverable.symbol)
        if not cost:
            logging.warning(
                "Couldn't find a market for %s, I don't think we should accept this contract %s ",
                deliverable.symbol,
                contract.id,
            )
            return False
        total_cost += cost[0] * deliverable.units_required
    if total_cost < total_value:
        return True
    elif total_cost < total_value * 2:
        logging.warning(
            "This contract is borderline, %scr to earn %scr - up to you boss [%s]",
            total_cost,
            total_value,
            contract.id,
        )
        return False

    logging.warning("I don't think we should accept this contract %s", contract.id)

    return False


def get_prices_for(connection, tradegood: str):
    sql = """select * from market_prices where trade_symbol = %s"""
    rows = try_execute_select(connection, sql, (tradegood,))
    if rows:
        row = rows[0]
        average_price_buy = row[1]
        average_price_sell = row[2]
        return [average_price_buy, average_price_sell]
    return None


def set_behaviour(connection, ship_symbol, behaviour_id, behaviour_params=None):
    sql = """INSERT INTO ship_behaviours (ship_symbol, behaviour_id, behaviour_params)
    VALUES (%s, %s, %s)
    ON CONFLICT (ship_symbol) DO UPDATE SET
        behaviour_id = %s,
        behaviour_params = %s
    """
    cursor = connection.cursor()
    behaviour_params_s = (
        json.dumps(behaviour_params) if behaviour_params is not None else None
    )

    try:
        cursor.execute(
            sql,
            (
                ship_symbol,
                behaviour_id,
                behaviour_params_s,
                behaviour_id,
                behaviour_params_s,
            ),
        )
    except Exception as err:
        logging.error(err)
        return False


def log_task(
    connection,
    behaviour_id: str,
    requirements: list,
    target_system: str,
    priority=5,
    agent_symbol=None,
    behaviour_params=None,
    expiry=None,
    specific_ship_symbol=None,
):
    behaviour_params = {} if not behaviour_params else behaviour_params
    param_s = json.dumps(behaviour_params)
    hash_str = hashlib.md5(
        f"{behaviour_id}-{target_system}-{priority}-{behaviour_params}-{expiry}-{specific_ship_symbol}".encode()
    ).hexdigest()
    sql = """ INSERT INTO public.ship_tasks(
	task_hash, requirements, expiry, priority, agent_symbol, claimed_by, behaviour_id, target_system, behaviour_params)
	VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    on conflict(task_hash) DO NOTHING
    """

    resp = try_execute_upsert(
        connection,
        sql,
        (
            hash_str,
            requirements,
            expiry,
            priority,
            agent_symbol,
            specific_ship_symbol,
            behaviour_id,
            target_system,
            param_s,
        ),
    )
    return resp or True


def maybe_buy_ship_hq_sys(client: SpaceTraders, ship_symbol) -> "Ship" or None:
    system_symbol = waypoint_slicer(client.view_my_self().headquarters)

    shipyard_wps = client.find_waypoints_by_trait(system_symbol, "SHIPYARD")
    if not shipyard_wps:
        logging.warning("No shipyards found yet - can't scale.")
        return

    if len(shipyard_wps) == 0:
        return False
    agent = client.view_my_self()

    shipyard = client.system_shipyard(shipyard_wps[0])
    return _maybe_buy_ship(client, shipyard, ship_symbol)


def _maybe_buy_ship(client: SpaceTraders, shipyard: "Shipyard", ship_symbol: str):
    agent = client.view_my_self()

    if not shipyard:
        return False
    for _, detail in shipyard.ships.items():
        detail: "ShipyardShip"
        if detail.ship_type == ship_symbol:
            if not detail.purchase_price:
                return LocalSpaceTradersRespose(
                    f"We don't have price information for this shipyard. {shipyard.waypoint}",
                    0,
                    0,
                    "conductorWK7.maybe_buy_ship",
                )
            if agent.credits > detail.purchase_price:
                resp = client.ships_purchase(ship_symbol, shipyard.waypoint)
                if resp:
                    return resp[0]


def register_and_store_user(
    username, logger=logging.getLogger("Conductor_functions")
) -> str:
    "returns the token"
    try:
        user = json.load(open("user.json", "r"))
    except FileNotFoundError:
        json.dump(
            {"email": "", "faction": "COSMIC", "agents": []},
            open("user.json", "w"),
            indent=2,
        )
        return
    logging.info("Starting up empty ST class to register user - expect warnings")
    st = SpaceTraders()
    resp = st.register(username, faction=user["faction"], email=user["email"])
    if not resp:
        # Log an error message with detailed information about the failed claim attempt
        logger.error(
            "Could not claim username %s, %d %s \n error code: %s",
            username,
            resp.status_code,
            resp.error,
            resp.error_code,
        )
        return
    found = False
    for agent in user["agents"]:
        if resp.data["token"] == agent["token"]:
            found = True
    if not found:
        user["agents"].append({"token": resp.data["token"], "username": username})
    json.dump(user, open("user.json", "w"), indent=2)
    if not resp:
        return resp
    return resp.data["token"]
