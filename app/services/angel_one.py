from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings


class AngelOneService:
    @staticmethod
    def _build_headers(
        api_key: str,
        client_code: Optional[str] = None,
        access_token: Optional[str] = None,
        client_local_ip: Optional[str] = None,
        client_public_ip: Optional[str] = None,
        mac_address: Optional[str] = None,
        source_id: str = "WEB",
        user_type: str = "USER",
    ) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": user_type,
            "X-SourceID": source_id,
            "X-PrivateKey": api_key,
            "X-ClientLocalIP": client_local_ip or "127.0.0.1",
            "X-ClientPublicIP": client_public_ip or (client_local_ip or "127.0.0.1"),
            "X-MACAddress": mac_address or "00:00:00:00:00:00",
        }

        if client_code:
            headers["X-ClientCode"] = client_code
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers

    @staticmethod
    async def login(
        api_key: str,
        client_code: str,
        pin: str,
        totp: str,
        client_local_ip: Optional[str] = None,
        client_public_ip: Optional[str] = None,
        mac_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "clientcode": client_code,
            "password": pin,
            "totp": totp,
        }

        headers = AngelOneService._build_headers(
            api_key=api_key,
            client_code=client_code,
            client_local_ip=client_local_ip,
            client_public_ip=client_public_ip,
            mac_address=mac_address,
        )

        for base_url in [settings.ANGEL_ONE_BASE_URL, settings.ANGEL_ONE_BASE_URL_ALT]:
            if not base_url:
                continue
            url = f"{base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    return response.json()

        return {"status": False, "message": "Login failed", "data": None}

    @staticmethod
    async def fetch_holdings(
        api_key: str,
        client_code: str,
        access_token: str,
        client_local_ip: Optional[str] = None,
        client_public_ip: Optional[str] = None,
        mac_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        headers = AngelOneService._build_headers(
            api_key=api_key,
            client_code=client_code,
            access_token=access_token,
            client_local_ip=client_local_ip,
            client_public_ip=client_public_ip,
            mac_address=mac_address,
        )

        endpoints = [
            "/rest/secure/angelbroking/portfolio/v1/getAllHolding",
            "/rest/secure/angelbroking/portfolio/v1/getHolding",
        ]

        for base_url in [settings.ANGEL_ONE_BASE_URL, settings.ANGEL_ONE_BASE_URL_ALT]:
            if not base_url:
                continue
            async with httpx.AsyncClient(timeout=30) as client:
                for endpoint in endpoints:
                    url = f"{base_url}{endpoint}"
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        return response.json()

        return {"status": False, "message": "Unable to fetch holdings", "data": None}
