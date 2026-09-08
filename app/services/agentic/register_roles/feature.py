"""Lifecycle for Agentic role contributions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.contracts.agentic.capabilities import MANDATE_CAPABILITY, ROLES_CAPABILITY
from app.contracts.plugins.capabilities import REGISTER_CONTRIBUTIONS_CAPABILITY
from app.services.agentic.register_roles.config import RegisterRolesConfig, from_dict
from app.services.agentic.register_roles.manifest import SPEC
from app.services.agentic.register_roles.register_roles import RegisterRolesService

if TYPE_CHECKING:
    from app.kernel.context import FeatureContext


class RegisterRolesFeature:
    spec = SPEC

    async def mount(self, context: FeatureContext, config: object) -> None:
        if config is None or isinstance(config, dict):
            from_dict(config)
        elif not isinstance(config, RegisterRolesConfig):
            raise TypeError("register-roles config must be mapping, RegisterRolesConfig, or None")
        context.require(REGISTER_CONTRIBUTIONS_CAPABILITY)
        service = RegisterRolesService(context.require(MANDATE_CAPABILITY))
        context.register_callback(service.close)
        context.provide(ROLES_CAPABILITY, service)


def feature() -> RegisterRolesFeature:
    return RegisterRolesFeature()
