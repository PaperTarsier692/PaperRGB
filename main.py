from common import ensure_venv, fix_res, Config, flatten_dict
from openrgb.utils import RGBColor, ModeData
from ttkthemes import ThemedTk, ThemedStyle
from tkinter.ttk import Notebook, Frame
from openrgb import OpenRGBClient
from hwinfo import HWInfo
from typing import Any
from time import sleep
import threading
import config
import search
ensure_venv(__file__)


fix_res()


class GUI:
    def __init__(self, theme: str) -> None:
        self.theme: str = theme
        self.root: ThemedTk = ThemedTk(theme=self.theme)
        self.root.geometry('1200x1200')
        self.style: ThemedStyle = ThemedStyle(self.root, theme=self.theme)
        self.hwinfo: HWInfo = HWInfo()
        self.hwinfo_values: dict[str, dict[str, Any]
                                 ] = self.hwinfo.get_values()

        self.notebook: Notebook = Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)

        self.client: OpenRGBClient = OpenRGBClient(
            '127.0.0.1', 6742, 'Python Client')
        self.client.connect()
        for device in self.client.devices:
            print(f'{device.name} - {device.type}')
            per_led_mode: ModeData = next(
                (mode for mode in device.modes if mode.name == 'Direct'))
            if per_led_mode:
                device.set_mode(per_led_mode)

        self.search_frame: Frame = Frame(self.notebook)
        self.search: search.GUI = search.GUI(
            self.search_frame, self.client, lambda: self.hwinfo_values)
        self.search_frame.pack(fill='both', expand=True)
        self.notebook.add(self.search_frame, text='Search', state='normal')
        print('Search added')

        self.config_frame: Frame = Frame(self.notebook)
        self.config: config.GUI = config.GUI(
            self.config_frame)
        self.config_frame.pack(fill='both', expand=True)
        self.notebook.add(self.config_frame, text='Config', state='normal')
        print('Config added')

        print('Finished adding categories')
        self.notebook.bind('<<NotebookTabChanged>>', self.set_name)
        self.apply_theme(self.theme)
        self.start_update_thread()
        self.root.mainloop()

    def return_hwinfo_values(self) -> dict[str, dict[str, Any]]:
        return self.hwinfo_values

    def start_update_thread(self) -> None:
        update_thread = threading.Thread(
            target=self.update_value_loop, name='MAIN_UPDATE_THREAD')
        update_thread.daemon = True
        update_thread.start()

    def update_value_loop(self) -> None:
        sleep(5)
        while True:
            self.update()
            sleep(cfg.smart_get2(2000, 'update_ms') / 1000)

    def set_name(self, *args) -> None:
        self.root.title(
            f'{self.notebook.tab(self.notebook.index("current"), "text")} - {self.theme.capitalize()}')
        self.search.run = self.notebook.index('current') == 0

    def apply_theme(self, theme: str) -> None:
        self.theme = theme
        self.root.set_theme(theme)
        self.style.theme_use(theme)
        bg_color = self.style.lookup('TFrame', 'background') or '#000'
        fg_color = self.style.lookup('TLabel', 'foreground') or '#FFF'
        self.apply_theme_widgets(self.root, bg_color, fg_color)
        self.set_name()

    def apply_theme_widgets(self, widget, bg_color, fg_color) -> None:
        try:
            if widget.cget('background') != '#800':
                widget.config(background=bg_color)
        except:
            pass
        try:
            widget.config(foreground=fg_color)
        except:
            pass
        for child in widget.winfo_children():
            self.apply_theme_widgets(child, bg_color, fg_color)

    def update(self) -> None:
        cfg: Config = Config()
        self.hwinfo_values = self.hwinfo.get_values()
        self.values = flatten_dict(self.hwinfo_values)
        if self.search.run:
            for device in self.client.devices:
                colors: list[RGBColor] = [
                    RGBColor(255, 255, 255) for _ in range(len(device.leds))]
                for param, values in cfg.get_value_from_path('values').items():
                    param: str
                    values: dict[str, Any]
                    if not values['enabled'] or not values['device'] == device.id:
                        continue
                    light: int = round(
                        (self.values.get(param, 100) / values['max']) * (values['end'] - values['start']))

                    if values['inverted']:
                        for i in range(values['end'] - light, values['end']):
                            colors[i] = RGBColor.fromHEX(values['color'])
                    else:
                        for i in range(values['start'], values['start'] + light):
                            colors[i] = RGBColor.fromHEX(values['color'])

                if device.colors == colors:
                    print('Skip')
                    continue
                print('Set')
                device.set_colors(colors, True)


cfg: Config = Config()
try:
    assert len(list(cfg.get_value_from_path('values').keys())) > 0
except:
    temp: HWInfo = HWInfo()
    first_sensor_path: str = list(flatten_dict(temp.get_values()).items())[
        0][0]
    temp.computer.Close()
    cfg.write_value_to_path(
        f'values/{first_sensor_path}', {'start': 0, 'end': 0, 'device': 0, 'enabled': 0, 'inverted': 0, 'color': '#FFFFFF', 'max': 100})

try:
    assert len(list(cfg.get_value_from_path('params').keys())) > 0
except:
    temp: HWInfo = HWInfo()
    cfg.write_value_to_path('params/', {list(flatten_dict(temp.get_values()).items())[
        0][0]: True})
    temp.computer.Close()

try:
    gui: GUI = GUI(cfg.smart_get2('equilux', 'theme'))
finally:
    try:
        gui.hwinfo.computer.Close()  # type: ignore
    except:
        pass
