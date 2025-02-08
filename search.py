from tkinter import OptionMenu, StringVar, Spinbox, colorchooser
from tkinter.ttk import Label, Frame, Button, Checkbutton
from common import start_main, Config, flatten_dict
from openrgb.utils import RGBColor
from ttkthemes import ThemedStyle
from openrgb import OpenRGBClient
from typing import Any, Callable
import threading
from time import sleep

start_main(__name__)


class GUI:
    def __init__(self, root: Frame, client: OpenRGBClient, get_hwinfo_values: Callable) -> None:
        self.run: bool = True
        self.root: Frame = root
        self.client: OpenRGBClient = client
        self.style: ThemedStyle = ThemedStyle(root)
        self.leds: int = 1
        self.selected_color: str = '#FF0000'
        self.cfg: Config = Config()
        self.get_hwinfo_values: Callable = get_hwinfo_values

        self.param_label: Label = Label(self.root, text='Params')
        self.param_label.pack(pady=(10, 0))
        self.param_var: StringVar = StringVar(self.root)

        self.param_var.set(
            next(iter(self.cfg.get_value_from_path('params/')), ''))
        self.param_menu: OptionMenu = OptionMenu(
            self.root, self.param_var, *self.cfg.get_value_from_path('params/'), command=self.load)
        self.param_menu.pack(pady=(0, 10))

        self.value_display_label: Label = Label(self.root, text='Value')
        self.value_display_label.pack(pady=(10, 0))
        self.value_display: Label = Label(self.root, text='')
        self.value_display.pack(pady=(0, 10))

        self.max_label: Label = Label(self.root, text='Max')
        self.max_label.pack(pady=(10, 0))
        self.max: Spinbox = Spinbox(self.root, from_=1, to=999999)
        self.max.pack(pady=(0, 10))

        self.start_label: Label = Label(self.root, text='Start')
        self.start_label.pack(pady=(10, 0))
        self.start: Spinbox = Spinbox(
            self.root, from_=0, to=self.leds, command=self.update)
        self.start.pack(pady=(0, 10))

        self.end_label: Label = Label(self.root, text='End')
        self.end_label.pack(pady=(10, 0))
        self.end: Spinbox = Spinbox(
            self.root, from_=0, to=self.leds, command=self.update)
        self.end.pack(pady=(0, 10))

        self.device_label: Label = Label(self.root, text='Device')
        self.device_label.pack(pady=(10, 0))
        self.device: Spinbox = Spinbox(
            self.root, from_=0, to=client.device_num-1, command=self.reset)
        self.device.pack(pady=(0, 10))

        self.inverted: Checkbutton = Checkbutton(
            self.root, text='Inverted', command=self.update)
        self.inverted.pack(pady=(10, 0))

        self.enabled: Checkbutton = Checkbutton(
            self.root, text='Enabled', command=self.update)
        self.enabled.pack(pady=(10, 0))

        self.color: Button = Button(
            self.root, text='Color', command=self.set_color)
        self.color.pack(pady=(10, 0))

        self.confirm: Button = Button(
            self.root, text='Confirm', command=self.save)
        self.confirm.pack(pady=(10, 10))
        self.load()
        self.start_update_thread()

    def _reload(self) -> None:
        self.param_menu['menu'].delete(0, 'end')
        self.cfg.read()
        for param in self.cfg.get_value_from_path('params/'):
            self.param_menu['menu'].add_command(
                label=param, command=lambda param=param: self.param_var.set(param))
        self.param_var.set(
            next(iter(self.cfg.get_value_from_path('params/')), ''))

    def start_update_thread(self) -> None:
        update_thread = threading.Thread(
            target=self.update_value_loop, name='SEARCH_UPDATE_THREAD')
        update_thread.daemon = True
        update_thread.start()

    def update_value_loop(self) -> None:
        sleep(3)
        while True:
            self.value_display.config(
                text=f'{flatten_dict(self.get_hwinfo_values()).get(self.param_var.get(), 'N/A')}')
            sleep(1)

    def update(self, *args) -> None:
        self.leds = len(list(self.client.devices[int(self.device.get())].leds))
        self.start.config(to=min(self.leds, int(self.end.get())))
        self.end.config(to=self.leds)
        out: list[RGBColor] = [RGBColor(255, 255, 255)
                               for _ in range(self.leds)]
        for i in range(int(self.start.get()), int(self.end.get())):
            out[i] = RGBColor.fromHEX(self.selected_color)
        self.client.devices[int(self.device.get())].set_colors(out)
        self.run = False

    def reset(self, *args) -> None:
        for device in self.client.devices:
            leds: int = len(list(device.leds))
            out: list[RGBColor] = [RGBColor(255, 255, 255)
                                   for _ in range(leds)]
            device.set_colors(out)
        self.update()

    def load(self, *args) -> None:
        cfg: Config = Config()
        try:
            data: dict[str, Any] = cfg.get_value_from_path(
                f'values/{self.param_var.get()}')
        except:
            data = {
                'start': 0,
                'end': 0,
                'device': 0,
                'enabled': 0,
                'inverted': 0,
                'color': self.selected_color,
                'max': 100
            }
        self.start.delete(0, 'end')
        self.start.insert(0, str(data['start']))
        self.end.delete(0, 'end')
        self.end.insert(0, str(data['end']))
        self.device.delete(0, 'end')
        self.device.insert(0, str(data['device']))
        self.max.delete(0, 'end')
        self.max.insert(0, str(data['max']))
        self.enabled.state(
            ['!selected'] if not data['enabled'] else ['selected'])
        self.inverted.state(
            ['!selected'] if not data['inverted'] else ['selected'])
        self.reset()

    def save(self, *args) -> None:
        cfg: Config = Config()
        cfg.write_value_to_path(f'values/{self.param_var.get()}', {
            'start': int(self.start.get()),
            'end': int(self.end.get()),
            'device': int(self.device.get()),
            'enabled': int(self.enabled.instate(['selected'])),
            'inverted': int(self.inverted.instate(['selected'])),
            'color': self.selected_color,
            'max': float(self.max.get())
        })
        self.run = True

    def set_color(self) -> None:
        self.selected_color = colorchooser.askcolor()[1] or self.selected_color
