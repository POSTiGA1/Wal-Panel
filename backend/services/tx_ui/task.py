import json
from typing import Any
from sqlalchemy.orm import Session

from backend.schema._input import ClientInput, ClientUpdateInput
from backend.services.tx_ui.api import APIService
from backend.db import crud
from backend.utils.logger import logger


class AdminTaskService:
    def __init__(self, admin_username: str, db: Session):
        self.admin_username = admin_username
        self.db = db
        self.admin = crud.get_admin_by_username(db, username=admin_username)
        panel = crud.get_panel_by_name(db, name=self.admin.panel)
        self.api_service = APIService(
            url=panel.url, username=panel.username, password=panel.password
        )

    async def get_all_users(self) -> list[dict]:
        try:
            inbounds = await self.api_service.get_inbounds()

            inbound = next(
                (inb for inb in inbounds if inb["id"] == self.admin.inbound_id), None
            )

            if not inbound:
                return []

            settings = json.loads(inbound["settings"])
            clients = settings.get("clients", [])

            client_stats = inbound.get("clientStats", [])

            stats_map = {c["email"]: c for c in client_stats}

            online_clients = await self.api_service.get_online_clients()

            result = []

            for c in clients:
                client_dict = c.copy()

                stat = stats_map.get(c["email"], {})

                client_dict["up"] = stat.get("up", 0)
                client_dict["down"] = stat.get("down", 0)
                client_dict["total"] = stat.get("total", 0)

                client_dict["is_online"] = c["email"] in online_clients

                result.append(client_dict)
            return result

        except Exception as e:
            logger.error(f"Error retrieving all users: {str(e)}")
            return []

    async def get_client_by_email(self, email: str) -> dict | bool:
        try:
            client = await self.api_service.get_client_by_email(email)
            return client
        except Exception as e:
            logger.error(f"Error retrieving client by email {email}: {str(e)}")
            return False

    async def add_client_to_panel(self, client: ClientInput) -> bool:
        try:
            result = await self.api_service.create_client(
                self.admin.inbound_id,
                self.admin.inbound_flow if self.admin.inbound_flow else None,
                client,
            )
            logger.info(
                f"Client {client.email} added to panel by admin {self.admin_username}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Failed to add client {client.email} by admin {self.admin_username}: {str(e)}"
            )
            return False

    async def update_client_in_panel(
        self, uuid: str, client_data: ClientUpdateInput
    ) -> bool:
        try:
            result = await self.api_service.update_client(
                uuid,
                self.admin.inbound_id,
                self.admin.inbound_flow if self.admin.inbound_flow else None,
                client_data,
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to update client {client_data.email} by admin {self.admin_username}: {str(e)}"
            )
            return False

    async def reset_client_usage(self, email: str) -> bool:
        try:
            result = await self.api_service.reset_client_usage(
                self.admin.inbound_id, email
            )
            return result
        except Exception as e:
            logger.error(
                f"Failed to reset usage for client {email} by admin {self.admin_username}: {str(e)}"
            )
            return False

    async def delete_client_from_panel(self, uuid: str) -> bool:
        try:
            result = await self.api_service.delete_client(self.admin.inbound_id, uuid)
            return result
        except Exception as e:
            logger.error(
                f"Failed to delete client {uuid} by admin {self.admin_username}: {str(e)}"
            )
            return False
