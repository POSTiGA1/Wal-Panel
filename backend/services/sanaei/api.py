import json
import httpx

from backend.schema._input import ClientInput, ClientUpdateInput


class APIService:
    def __init__(self, url: str, token: str):
        self.url = url.rstrip("/")
        self.token = token

        self.client = httpx.AsyncClient(
            base_url=self.url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def test_connection(self) -> bool:
        try:
            response = await self.client.get("/panel/api/server/status")

            if response.status_code != 200:
                return False

            data = response.json()

            if not data.get("success"):
                return False

            return True

        except Exception:
            return False

    async def get_inbound(self, inbound_id: int):

        response = await self.client.get(
            f"/panel/api/inbounds/get/{inbound_id}"
        )

        response.raise_for_status()

        data = response.json()

        return data.get("obj")

    async def get_all_inbounds(self):

        response = await self.client.get(
            "/panel/api/inbounds/list"
        )

        response.raise_for_status()

        data = response.json()

        return data.get("obj", [])

    async def get_all_online_clients(self):
        response = await self.client.post(
            "/panel/api/inbounds/onlines"
        )

        response.raise_for_status()

        data = response.json()

        return data.get("obj", [])

    async def add_client(
        self,
        inbound_id: int,
        inbound_flow: str,
        client: ClientInput
    ):

        payload = {
            "id": inbound_id,
            "settings": {
                "clients": [
                    {
                        "id": client.id,
                        "email": client.email,
                        "enable": client.enable,
                        "expiryTime": client.expiry_time,
                        "totalGB": client.total,
                        "flow": inbound_flow if inbound_flow else client.flow,
                        "subId": client.sub_id,
                    }
                ]
            }
        }

        payload["settings"] = json.dumps(
            payload["settings"]
        )

        response = await self.client.post(
            "/panel/api/inbounds/addClient",
            json=payload,
        )

        response.raise_for_status()

        return response.json()

    async def get_client_by_email(self, email: str):
        response = await self.client.get(
            f"/panel/api/inbounds/getClientTraffics/{email}"
        )

        response.raise_for_status()

        data = response.json()

        return data.get("obj")

    async def update_client(
        self,
        uuid: str,
        inbound_id: int,
        inbound_flow: str,
        client: ClientUpdateInput
    ):

        payload = {
            "id": inbound_id,
            "settings": {
                "clients": [
                    {
                        "id": uuid,
                        "email": client.email,
                        "enable": client.enable,
                        "expiryTime": client.expiry_time,
                        "totalGB": client.total,
                        "flow": inbound_flow if inbound_flow else client.flow,
                        "subId": client.sub_id,
                    }
                ]
            }
        }

        payload["settings"] = json.dumps(
            payload["settings"]
        )

        response = await self.client.post(
            f"/panel/api/inbounds/updateClient/{uuid}",
            json=payload,
        )

        response.raise_for_status()

        return response.json()

    async def reset_client_usage(
        self,
        inbound_id: int,
        email: str
    ):

        response = await self.client.post(
            f"/panel/api/inbounds/{inbound_id}/resetClientTraffic/{email}"
        )

        response.raise_for_status()

        return response.json()

    async def delete_client(
        self,
        inbound_id: int,
        uuid: str
    ):

        response = await self.client.post(
            f"/panel/api/inbounds/{inbound_id}/delClient/{uuid}"
        )

        response.raise_for_status()

        return response.json()

    async def close(self):
        await self.client.aclose()