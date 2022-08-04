from tanager_feeder import utils
from tanager_feeder.command_handlers.get_position_handler import GetPositionHandler


class ConfigHandler(GetPositionHandler):
    def __init__(
        self,
        controller,
        title: str = "Configuring pi...",
        label: str = "Configuring pi based on input\ngoniometer position...",
        timeout: int = utils.PI_BUFFER + 80,
    ):
        super().__init__(controller, title, label, timeout)
        self.success_message = "piconfigsuccess"
