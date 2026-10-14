"""Instance settings.

Every value here comes from the environment (see .env). Extend this class with
fields that belong to this service alone; anything shared with other IFDD
services belongs in ifdd.be.core.CoreSettings instead.
"""

from ifdd.be.core import CoreSettings


class Settings(CoreSettings):
    pass


settings = Settings()
