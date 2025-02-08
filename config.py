from tkinter import Canvas, Scrollbar
from typing import Callable
from papertools import File, Timer
from ttkthemes import ThemedStyle
from tkinter import Text, BooleanVar
from tkinter.ttk import Button, Label, Radiobutton, Frame, Checkbutton
from common import start_main, Config
from hwinfo import HWInfo
start_main(__name__)


class GUI:
    def __init__(self, root: Frame, themes: list[str], save_callback: Callable) -> None:
        self.root: Frame = root
        self.themes: list[str] = themes
        self.style: ThemedStyle = ThemedStyle(root)
        self.save_callback: Callable = save_callback
        self.params: dict[str, bool]
        self.hwinfo: HWInfo = HWInfo()

        self.canvas: Canvas = Canvas(self.root)
        self.scrollbar: Scrollbar = Scrollbar(
            self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame: Frame = Frame(self.canvas)

        self.canvas.create_window(
            (0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind("<MouseWheel>", self.update_scrollregion)
        self.canvas.bind("<Button-4>", self.update_scrollregion)  # For Linux
        self.canvas.bind("<Button-5>", self.update_scrollregion)  # For Linux

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.cfg: Config = Config()
        self.entries: dict = {}

        for key, value in self.cfg.cfg.items():
            self.add_option(key, value, type(value))

        self.add_params()

        self.button_frame: Frame = Frame(self.root)
        self.button_frame.pack(side='bottom', fill='x')

        self.button1: Button = Button(
            self.button_frame, text="Save", command=self.save)
        self.button1.pack(fill='x')

    def update_scrollregion(self, event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def add_params(self) -> None:
        def add_checkbox(name: str, full_name: str) -> None:
            def callback(checkbox: Checkbutton) -> None:
                value: bool = checkbox.instate(['selected'])
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

    def add_option(self, name: str, value: str, type: type) -> None:
        if type == dict:
            return
        frame: Frame = Frame(self.scrollable_frame)
        frame.pack(fill='x', padx=20, pady=1)

        label: Label = Label(frame, text=name)
        label.pack(side='left')

        if type == bool:
            var = BooleanVar(value=bool(value))
            true_button = Radiobutton(
                frame, text="True", variable=var, value=True)
            false_button = Radiobutton(
                frame, text="False", variable=var, value=False)
            true_button.pack(side='left', padx=5)
            false_button.pack(side='left', padx=5)
            self.entries[name] = var
        else:
            text_field: Text = Text(frame, height=1, width=20)
            text_field.insert('1.0', value)
            text_field.pack(side='left', padx=5, fill='x', expand=True)
            self.entries[name] = text_field

    def add_group(self, name: str) -> None:
        frame: Frame = Frame(self.scrollable_frame)
        frame.pack(fill='x', padx=5, pady=5)

        label: Label = Label(frame, text=name)
        label.pack(side='left')

    def save(self) -> None:
        for name, _ in self.cfg.cfg.items():
            if isinstance(self.entries[name], BooleanVar):
                self.cfg.cfg[name] = self.entries[name].get()
            elif name == 'theme':
                if self.entries[name].get(
                        '1.0', 'end-1c') in self.themes:
                    self.cfg.cfg[name] = self.entries[name].get(
                        '1.0', 'end-1c')
                    self.entries[name].config(bg=self.style.lookup(
                        'TFrame', 'background') or '#000')
                else:
                    self.entries[name].config(bg='#800')
            else:
                self.cfg.cfg[name] = self.entries[name].get(
                    '1.0', 'end-1c')
        File('config.json').json_w(self.cfg.cfg)
        self.save_callback(self.cfg)
