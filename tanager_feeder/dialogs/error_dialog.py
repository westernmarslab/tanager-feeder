from typing import Dict, Optional

from tanager_feeder.dialogs.dialog import Dialog


class ErrorDialog(Dialog):
    def __init__(
        self,
        controller,
        title: str = "Error",
        label: str = "Error!",
        buttons: Optional[Dict] = None,
        info_string: Optional[str] = None,
        topmost: bool = True,
        button_width: int = 30,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        if buttons is None:
            buttons = {"ok": {}}
        self.listener = None
        if info_string is None:
            self.info_string = label + "\n"
        else:
            self.info_string = info_string
        if width is None or height is None:
            super().__init__(
                controller, title, label, buttons, allow_exit=False, info_string=None, button_width=button_width
            )
        else:
            super().__init__(
                controller,
                title,
                label,
                buttons,
                allow_exit=False,
                info_string=None,
                button_width=button_width,
                width=width,
                height=height,
            )
        if topmost:
            self.top.attributes("-topmost", True)
