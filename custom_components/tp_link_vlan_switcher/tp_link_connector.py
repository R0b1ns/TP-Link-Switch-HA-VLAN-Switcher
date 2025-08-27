import logging
import requests
from typing import Dict, Any, Optional, Literal

_LOGGER = logging.getLogger(__name__)

Phase = Literal["turn_on", "turn_off"]

class TPLinkConnector:
    """Handles TP-Link login, VLAN and PVID configuration with clean session management."""

    def __init__(self, ip: str, username: str, password: str):
        self._ip = ip
        self._user = username
        self._pwd = password
        self._session: Optional[requests.Session] = None

    # ---------------------- Session Management ----------------------
    def _start_session(self) -> None:
        if self._session is None:
            self._session = requests.Session()

    def _close_session(self) -> None:
        if self._session:
            try:
                self._session.get(f"http://{self._ip}/Logout.htm", timeout=5)
            except Exception:
                pass
            finally:
                self._session.close()
                self._session = None

    # ---------------------- Login / Logout ----------------------
    def login(self) -> bool:
        self._start_session()
        try:
            resp = self._session.post(
                f"http://{self._ip}/logon.cgi",
                data={"username": self._user, "password": self._pwd, "cpassword": "", "logon": "Login"},
                timeout=8,
            )
            if resp.status_code != 200:
                _LOGGER.error("Login failed (%s): HTTP %s", self._ip, resp.status_code)
                return False
            return True
        except Exception as e:
            _LOGGER.exception("Login exception for %s: %s", self._ip, e)
            return False

    def logout(self) -> None:
        self._close_session()

    # ---------------------- VLAN ----------------------
    def apply_vlan(self, vlans: Dict[Phase, list[Dict[str, Any]]], phase: Phase) -> None:
        """Apply VLAN settings based on the given phase."""
        vlan_list = vlans.get(phase, [])
        if not vlan_list:
            return

        for vlan in vlan_list:
            vid = vlan.get("vid")
            vname = vlan.get("vname")
            ports = vlan.get("ports", {})

            params = {"vid": vid, "vname": vname, "qvlan_add": "Add/Modify"}
            for port, state in ports.items():
                params[f"selType_{port}"] = state

            url = f"http://{self._ip}/qvlanSet.cgi"
            _LOGGER.debug("Setting VLAN (%s/%s) GET %s params=%s", vid, vname, url, params)
            try:
                self._session.get(url, params=params, timeout=8)
            except Exception as e:
                _LOGGER.exception("Failed setting VLAN %s/%s on %s: %s", vid, vname, self._ip, e)

    # ---------------------- PVID ----------------------
    def apply_pvid(self, pvid: Dict[Phase, Dict[str, list[int]]], phase: Phase) -> None:
        """Apply PVID settings based on the given phase."""
        pvid_cfg = pvid.get(phase, {})
        if not pvid_cfg:
            return

        for pvid_str, ports in pvid_cfg.items():
            pbm = 0
            for p in ports:
                if isinstance(p, int) and p >= 1:
                    pbm |= (1 << (p - 1))
            url = f"http://{self._ip}/vlanPvidSet.cgi"
            params = {"pbm": str(pbm), "pvid": str(pvid_str)}
            _LOGGER.debug("Setting PVID (%s): GET %s params=%s", self._ip, url, params)
            try:
                self._session.get(url, params=params, timeout=8)
            except Exception as e:
                _LOGGER.exception("Failed setting PVID %s on %s: %s", pvid_str, self._ip, e)

    # ---------------------- Apply Profile ----------------------
    def apply_profile(self, vlans: Dict[Phase, list[Dict[str, Any]]],
                      pvid: Dict[Phase, Dict[str, list[int]]], phase: Phase) -> bool:
        """High-level method to apply VLAN and PVID for a given phase."""
        try:
            if not self.login():
                return False
            self.apply_vlan(vlans, phase)
            self.apply_pvid(pvid, phase)
            return True
        finally:
            self.logout()
