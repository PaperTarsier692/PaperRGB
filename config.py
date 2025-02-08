from tkinter.ttk import Label, Frame, Checkbutton
from tkinter import Canvas, Scrollbar
from common import start_main, Config
from tkinter import BooleanVar
from hwinfo import HWInfo
start_main(__name__)


class GUI:
    def __init__(self, root: Frame) -> None:
        self.root: Frame = root
        self.params: dict[str, bool]
        self.hwinfo: HWInfo = HWInfo()
        self.changes: bool = False

        self.canvas: Canvas = Canvas(self.root)
        self.scrollbar: Scrollbar = Scrollbar(
            self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame: Frame = Frame(self.canvas)

        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<MouseWheel>", self.update_scrollregion)
        self.canvas.bind("<Button-4>", self.update_scrollregion)
        self.canvas.bind("<Button-5>", self.update_scrollregion)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="both")

        self.cfg: Config = Config()
        self.add_params()

    def update_scrollregion(self, event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_params(self) -> None:
        def add_checkbox(name: str, full_name: str) -> None:
            def callback(checkbox: Checkbutton) -> None:
                value: bool = checkbox.instate(['selected'])
                self.changes = True
                if value:
                    self.cfg.write_value_to_path(
                        f'params/{full_name}', True)
                else:
                    self.cfg.remove_value_from_path(
                        f'params/{full_name}')
            if '/' in name:
                return
            checkbox: Checkbutton = Checkbutton(
                self.scrollable_frame, text=name, command=lambda: callback(checkbox))
            checkbox.pack(fill='x', padx=20, pady=1)
            checkbox.config(
                variable=BooleanVar(value=self.cfg.get_value_from_path(f'params/{full_name}', True) or False))

        for device, values in self.hwinfo.get_values().items():
            self.add_group(device)
            for subdevice in values:
                if not isinstance(values[subdevice], dict):
                    continue
                self.add_group(subdevice)
                for sensor in values[subdevice]:  # type: ignore
                    add_checkbox(sensor, f'{device}\\{subdevice}\\{sensor}')
            for sensor in values:
                if isinstance(values[sensor], dict):
                    continue
                add_checkbox(sensor, f'{device}\\{sensor}')

    def add_group(self, name: str) -> None:
        frame: Frame = Frame(self.scrollable_frame)
        frame.pack(fill='x', padx=5, pady=5)

        label: Label = Label(frame, text=name)
        label.pack(side='left')
