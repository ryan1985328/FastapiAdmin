"""Reuse the App-owned address model instead of declaring a second table model."""

from app.plugin.module_app.address.model import AppUserAddressModel

__all__ = ["AppUserAddressModel"]
