"""Instance-specific routers.

This is the extension point for endpoints that exist only in this service.
Add a module next to this one, import its router here and list it below; a
cruft update will not touch what you add.
"""

from fastapi import APIRouter

instance_routers: list[APIRouter] = []
