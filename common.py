import os
import sys
from typing import Any, Union

venv: bool = hasattr(sys, 'real_prefix') or (
    hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
current_path: str = os.path.abspath(
    os.path.join(os.path.abspath(__file__), os.pardir))
windows: bool = os.name == 'nt'


def y_n(inp: str, allow_empty: bool = False) -> bool:
    if inp is not None:
        print(inp, end=' ')
    res: str = input().strip().lower()
    if allow_empty and res == '':
        return False
    return res == 'y' or res == 'j'


def ensure_venv(file: str, args: list[str] = []) -> None:
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        pass
    else:
        if windows:
            os.system(
                f'.\\.venv\\Scripts\\activate.bat && python "{file}" {" ".join(args)}')
        else:
            os.system(
                f'source .venv/bin/activate && python "{file}" {" ".join(args)}')


def better_input(prompt: str, min_len: int = 0, max_len: int = 0, allow_spaces: bool = True, silent: bool = False, allow_empty: bool = False) -> str:
    inp: Union[str, None] = None
    while not check_str(inp, min_len, max_len, allow_spaces, silent, allow_empty):
        inp = input(prompt).strip()
    return str(inp)


def better_getpass(prompt: str, min_len: int = 0, max_len: int = 0, allow_spaces: bool = True, silent: bool = False, allow_empty: bool = False) -> str:
    from getpass import getpass
    inp: Union[str, None] = None
    while not check_str(inp, min_len, max_len, allow_spaces, silent, allow_empty):
        inp = getpass(prompt).strip()
    return str(inp)


def check_str(inp: Union[str, None], min_len: int = 0, max_len: int = 0, allow_spaces: bool = True, silent: bool = False, allow_empty: bool = False) -> bool:
    if inp is None:
        return False

    if inp == '' and allow_empty:
        return True

    if len(inp) < min_len:
        if not silent:
            print('Input too short')
        return False

    if max_len > 0 and len(inp) > max_len:
        if not silent:
            print('Input too long')
        return False

    if not allow_spaces and ' ' in inp:
        if not silent:
            print('Input contains spaces')
        return False

    return True


def type_input(prompt: str, type: type, allow_empty: bool = False) -> Any:
    inp: str = input(prompt).strip()
    if allow_empty and inp == '':
        return False
    try:
        return type(inp)
    except ValueError:
        return type_input(prompt, type)


def popup(title: str, prompt: str) -> None:
    if windows:
        import ctypes
        ctypes.windll.user32.MessageBoxW(  # type: ignore
            None, prompt, title, 0)
    else:
        import subprocess
        applescript: str = f"""
        display dialog "{prompt}" ¬
        with title "{title}" ¬
        with icon caution ¬
        buttons {{"OK"}}
        """
        subprocess.call(f"osascript -e '{applescript}'", shell=True)


def fix_res() -> None:
    import ctypes
    if windows:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # type: ignore


def generate_random_string(length: int) -> str:
    import string
    import random
    letters: str = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def start_main(name: str) -> None:
    if name != '__main__':
        return
    if windows:
        os.system(f'python gui.py')
    else:
        os.system(f'python3 gui.py')


class Config:
    def __init__(self) -> None:
        from papertools import File
        self.file: File = File('config.json')
        self.check_cfg()
        self.cfg: dict[str, Any] = self.file.json_r()

    def check_cfg(self) -> None:
        if not self.file.exists():
            print('Config file not found, generating new one')
            self.file.json_w({})
        try:
            self.cfg: dict[str, Any] = self.file.json_r()
        except Exception as e:
            print(f'Error while reading the config: {e}')
            input()
            exit()

    def read(self) -> dict[str, Any]:
        self.cfg = self.file.json_r()
        return self.cfg

    def write(self, cfg: Union[dict[str, Any], None] = None) -> None:
        if cfg is not None:
            self.cfg = cfg
        self.file.json_w(self.cfg)

    def smart_get(self, inp: str, path: str, **kwargs) -> Any:
        if inp.strip() == '':
            try:
                return self.get_value_from_path(path)
            except:
                if kwargs.get('error_callback') != None:
                    kwargs['error_callback'](**kwargs)
                return ''

        else:
            try:
                self.get_value_from_path(path)
            except:
                self.write_value_to_path(path, inp)
            return inp

    def smart_get2(self, inp: Any, path: str, **kwargs) -> Any:
        try:
            return self.get_value_from_path(path)
        except:
            if kwargs.get('error_callback') != None:
                kwargs['error_callback'](**kwargs)
                return ''
            self.write_value_to_path(path, inp)
            return inp

    def get_value_from_path(self, path: str) -> Any:
        keys: list[str] = path.strip('/').split('/')
        value: Any = self.cfg
        for key in keys:
            value = value[key]
        return value

    def write_value_to_path(self, path: str, value: Any, save: bool = True) -> None:
        keys: list[str] = path.strip('/').split('/')
        d: dict[str, Any] = self.cfg
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                d[key] = {}
            d = d[key]
        d[keys[-1]] = value
        if save:
            self.write()

    def remove_value_from_path(self, path: str, save: bool = True) -> None:
        keys: list[str] = path.strip('/').split('/')
        d: dict[str, Any] = self.cfg
        for key in keys[:-1]:
            if key not in d or not isinstance(d[key], dict):
                return
            d = d[key]
        d.pop(keys[-1])
        if save:
            self.write()


def flatten_dict(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in d.items():
        if isinstance(value, dict):
            for k, v in flatten_dict(value).items():
                out[f'{key}\\{k}'] = v
        else:
            out[key] = value
    return out
