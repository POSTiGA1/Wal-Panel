import json
from typing import Any

from sqlalchemy.orm import Session

from backend.schema._input import ClientInput, ClientUpdateInput
from backend.services.sanaei import APIService
from backend.db import crud
from backend.utils.logger import logger


class AdminTaskService:
    def __init__(self, admin_username: str, db: Session):
        self.admin_username = admin_username
        self.db = db

        self.admin = crud.get_admin_by_username(
            db,
            username=admin_username
        )

        panel = crud.get_panel_by_name(
            db,
            name=self.admin.panel
        )

        self.api_service = APIService(
            url=panel.url,
            token=panel.token if panel.token else ""
        )

    async def get_all_users(self) -> Any:
        try:
            inbounds = await self.api_service.get_all_inbounds()

            inbound = next(
                (
                    i for i in inbounds
                    if i.get("id") == self.admin.inbound_id
                ),
                None
            )
            
            if not inbound:
                logger.warning(
                    f"Inbound not found for admin "
                    f"{self.admin_username} "
                    f"with inbound_id {self.admin.inbound_id}"
                )
                return []

            client_stats = inbound.get("clientStats", [])
            settings_raw = inbound.get("settings", "{}")
            settings = json.loads(settings_raw)

            settings_clients = settings.get("clients", [])
            online_clients = (
                await self.api_service.get_all_online_clients()
            )

            result = []

            for stat in client_stats:

                client_setting = next(
                    (
                        c for c in settings_clients
                        if c.get("email") == stat.get("email")
                    ),
                    {}
                )

                client_data = {
                    **stat,

                    "totalGB": client_setting.get("totalGB", 0),
                    "flow": client_setting.get("flow", ""),
                    "created_at": client_setting.get("created_at"),
                    "updated_at": client_setting.get("updated_at"),

                    "isOnline": (
                        stat.get("email") in online_clients
                    )
                }

                result.append(client_data)

            return result

        except Exception as e:
            logger.error(
                f"Error retrieving users for admin "
                f"{self.admin_username}: {str(e)}"
            )

            return []

    async def get_client_by_email(self, email: str):
        try:
            client = await self.api_service.get_client_by_email(email)
            return client

        except Exception as e:
            logger.error(
                f"Error retrieving client by email "
                f"{email}: {str(e)}"
            )
            return False

    async def add_client_to_panel(
        self,
        client: ClientInput
    ) -> bool:
        try:
            await self.api_service.add_client(
                self.admin.inbound_id,
                self.admin.inbound_flow
                if self.admin.inbound_flow
                else None,
                client,
            )

            logger.info(
                f"Client {client.email} added "
                f"to panel by admin "
                f"{self.admin_username}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to add client "
                f"{client.email} by admin "
                f"{self.admin_username}: {str(e)}"
            )

            return False

    async def update_client_in_panel(
        self,
        uuid: str,
        client_data: ClientUpdateInput
    ) -> bool:
        try:
            await self.api_service.update_client(
                uuid,
                self.admin.inbound_id,
                self.admin.inbound_flow,
                client_data
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to update client "
                f"{client_data.email} by admin "
                f"{self.admin_username}: {str(e)}"
            )

            return False

    async def reset_client_usage(
        self,
        email: str
    ) -> bool:
        try:
            await self.api_service.reset_client_usage(
                self.admin.inbound_id,
                email
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to reset usage for client "
                f"{email} by admin "
                f"{self.admin_username}: {str(e)}"
            )

            return False

    async def delete_client_from_panel(
        self,
        uuid: str
    ) -> bool:
        try:
            await self.api_service.delete_client(
                self.admin.inbound_id,
                uuid
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to delete client "
                f"{uuid} by admin "
                f"{self.admin_username}: {str(e)}"
            )

            return False