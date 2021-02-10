# import time
#
# import numpy as np
#
# from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils
from tanager_feeder.command_handlers.get_position_handler import GetPositionHandler


class ConfigHandler(GetPositionHandler):
    def __init__(
        self,
        controller,
        title="Configuring pi...",
        label="Configuring pi based on input\ngoniometer position...",
        timeout=utils.PI_BUFFER + 60,
    ):
        super().__init__(controller, title, label, timeout)
        self.success_message = "piconfigsuccess"
