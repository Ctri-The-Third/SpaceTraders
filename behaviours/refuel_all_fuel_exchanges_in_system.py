import sys
import time

sys.path.append(".")

from behaviours.generic_behaviour import Behaviour
import logging
from straders_sdk.utils import try_execute_select, set_logging, waypoint_slicer
from straders_sdk.models import Waypoint, System, Market, MarketTradeGoodListing

BEHAVIOUR_NAME = "REFUEL_ALL_IN_SYSTEM"
SAFETY_PADDING = 60


class RefuelAllExchanges(Behaviour):
    """Expects a parameter blob containing 'asteroid_wp'"""

    def __init__(
        self,
        agent_name,
        ship_name,
        behaviour_params: dict = ...,
        config_file_name="user.json",
        session=None,
        connection=None,
    ) -> None:
        super().__init__(
            agent_name,
            ship_name,
            behaviour_params,
            config_file_name,
            session,
            connection,
        )
        self.target_system = behaviour_params.get("target_system", None)
        self.agent = self.st.view_my_self()

    def run(self):
        self.st.logging_client.log_beginning(
            BEHAVIOUR_NAME, self.ship.name, self.agent.credits
        )
        st = self.st
        ship = st.ships_view_one(self.ship.name, True)
        if not self.target_system:
            self.target_system = ship.nav.system_symbol
        # find an export market
        # find all markets that have exchanges
        # travel to each market
        #   sell fuel until it's ABUNDANT
        #   if necessary, rtb and refuel.
        all_markets = st.find_waypoints_by_trait(self.target_system, "MARKETPLACE")
        fuel_market = None
        supply_price = 9999999

        for w in all_markets:
            w = st.system_market(w)
            w: Market
            for l in w.listings:
                if (
                    l.symbol == "FUEL"
                    and l.purchase_price < supply_price
                    and l.type == "EXPORT"
                ):
                    fuel_market = w
                    supply_price = l.purchase_price

        if not fuel_market:
            logging.warning(f"Couldn't find a fuel market in {self.target_system}")

            self.end()
            time.sleep(SAFETY_PADDING)
            return
        needing_refueled = []
        for w in all_markets:
            w = st.system_market(w)
            for t in w.listings:
                t: MarketTradeGoodListing
                if (
                    t.symbol == "FUEL"
                    and t.supply != "ABUNDANT"
                    and t.type == "EXCHANGE"
                    and t.sell_price > supply_price
                ):
                    needing_refueled.append(w)
                    break

        for w in needing_refueled:
            # travel to market
            # sell fuel until abundant
            # rtb and refuel
            # repeat
            m = self.st.system_market(w)
            fuel = m.get_tradegood("FUEL")
            trips = 0
            while fuel.supply != "ABUNDANT" or trips < 5:
                self.ship_intrasolar(fuel_market.symbol)

                self.buy_cargo("FUEL", self.ship.cargo_space_remaining)
                w: Waypoint
                self.ship_intrasolar(w.symbol)
                self.sell_all_cargo([])
                m = self.st.system_market(w, True)
                fuel = m.get_tradegood("FUEL")
                trips += 1
        self.end()


if __name__ == "__main__":
    from dispatcherWK16 import lock_ship

    set_logging(level=logging.DEBUG)
    agent = sys.argv[1] if len(sys.argv) > 2 else "CTRI-U-"
    ship_number = sys.argv[2] if len(sys.argv) > 2 else "1"
    ship = f"{agent}-{ship_number}"
    bhvr = RefuelAllExchanges(agent, ship, {})
    lock_ship(ship_number, "MANUAL", bhvr.st.db_client.connection, 60 * 24)
    bhvr.run()
    lock_ship(ship_number, "MANUAL", bhvr.st.db_client.connection, 0)
