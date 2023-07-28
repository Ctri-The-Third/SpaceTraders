from typing import Protocol, runtime_checkable
from .models import Waypoint, Survey, Market, Shipyard
from .responses import SpaceTradersResponse
from abc import abstractmethod


class SpaceTradersInteractive(Protocol):
    token: str = None

    def __init__(self, token) -> None:
        self.token = token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"}

    def update(self, json_data: dict):
        pass


@runtime_checkable
class SpaceTradersClient(Protocol):
    token: str = None

    @abstractmethod
    def __init__(self, token) -> None:
        pass

    @abstractmethod
    def _headers(self) -> dict:
        pass

    @abstractmethod
    def update(self, update_obj):
        pass

    def waypoints_view(
        self, system_symbol: str
    ) -> dict[str:list] or SpaceTradersResponse:
        """view all waypoints in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoints in.

        Returns:
            Either a dict of Waypoint objects or a SpaceTradersResponse object on failure.
        """
        pass

    @abstractmethod
    def waypoints_view_one(
        self, system_symbol, waypoint_symbol, force=False
    ) -> Waypoint or SpaceTradersResponse:
        """view a single waypoint in a system. Uses cached values by default.

        Args:
            `system_symbol` (str): The symbol of the system to search for the waypoint in.
            `waypoint_symbol` (str): The symbol of the waypoint to search for.
            `force` (bool): Optional - Force a refresh of the waypoint. Defaults to False.

        Returns:
            Either a Waypoint object or a SpaceTradersResponse object on failure."""
        pass

    @abstractmethod
    def find_waypoint_by_coords(
        self, system_symbol: str, x: int, y: int
    ) -> Waypoint or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_waypoints_by_trait(
        self, system_symbol: str, trait: str
    ) -> list[Waypoint] or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_waypoints_by_trait_one(
        self, system_symbol: str, trait: str
    ) -> Waypoint or SpaceTradersResponse:
        pass

    @abstractmethod
    def find_waypoint_by_type(
        self, system_wp, waypoint_type
    ) -> Waypoint or SpaceTradersResponse:
        pass

    @abstractmethod
    def ship_orbit(self, ship: "Ship") -> SpaceTradersResponse:
        """my/ships/:miningShipSymbol/orbit takes the ship name or the ship object"""
        pass

    @abstractmethod
    def ship_change_course(self, ship: "Ship", dest_waypoint_symbol: str):
        """my/ships/:shipSymbol/course"""
        pass

    @abstractmethod
    def ship_move(
        self, ship: "Ship", dest_waypoint_symbol: str
    ) -> SpaceTradersResponse:
        """my/ships/:shipSymbol/navigate"""

        pass

    @abstractmethod
    def ship_extract(self, ship: "Ship", survey: Survey = None) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/extract"""

        pass

    @abstractmethod
    def ship_dock(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/dock"""
        pass

    @abstractmethod
    def ship_refuel(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/refuel"""
        pass

    @abstractmethod
    def ship_sell(
        self, ship: "Ship", symbol: str, quantity: int
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/sell"""

        pass

    @abstractmethod
    def ship_survey(self, ship: "Ship") -> list[Survey] or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/survey"""

        pass

    @abstractmethod
    def ship_transfer_cargo(
        self, ship: "Ship", trade_symbol, units, target_ship_name
    ) -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/transfer"""

        pass

    @abstractmethod
    def system_market(self, wp: Waypoint) -> Market or SpaceTradersResponse:
        """/game/systems/{symbol}/marketplace"""

        pass

    @abstractmethod
    def systems_list_all(self) -> dict[str:"System"] or SpaceTradersResponse:
        """/game/systems"""

        pass

    @abstractmethod
    def system_shipyard(self, waypoint: Waypoint) -> Shipyard or SpaceTradersResponse:
        """/game/locations/{symbol}/shipyard"""

        pass

    @abstractmethod
    def ship_negotiate(self, ship: "Ship") -> "Contract" or SpaceTradersResponse:
        """/my/ships/{shipSymbol}/negotiate/contract"""
        pass

    @abstractmethod
    def ship_cooldown(self, ship: "Ship") -> SpaceTradersResponse:
        """/my/ships/{shipSymbol}/cooldown"""
        pass

    @abstractmethod
    def ships_view(self) -> list["Ship"] or SpaceTradersResponse:
        """/my/ships"""

        pass

    @abstractmethod
    def ships_view_one(self, symbol: str) -> "Ship" or SpaceTradersResponse:
        pass

    @abstractmethod
    def ships_purchase(
        self, ship_type: str, shipyard_waypoint: str
    ) -> tuple["Ship", "Agent"] or SpaceTradersResponse:
        pass

    @abstractmethod
    def contracts_deliver(
        self, contract: "Contract", ship: "Ship", trade_symbol: str, units: int
    ) -> SpaceTradersResponse:
        pass

    @abstractmethod
    def contracts_fulfill(self, contract: "Contract") -> SpaceTradersResponse:
        pass
