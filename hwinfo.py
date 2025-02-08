from HardwareMonitor.Hardware import IVisitor, IComputer, IHardware, IParameter, ISensor, Computer
from common import start_main
from typing import Union
start_main(__name__)


class UpdateVisitor(IVisitor):
    __namespace__ = "TestHardwareMonitor"

    def VisitComputer(self, computer: IComputer) -> None:
        computer.Traverse(self)  # type: ignore

    def VisitHardware(self, hardware: IHardware) -> None:
        hardware.Update()
        for subHardware in hardware.SubHardware:
            subHardware.Update()

    def VisitParameter(self, parameter: IParameter) -> None: pass
    def VisitSensor(self, sensor: ISensor) -> None: pass


class HWInfo:
    def __init__(self) -> None:
        self.computer: Computer = Computer()
        self.computer.IsMotherboardEnabled = True
        self.computer.IsControllerEnabled = True
        self.computer.IsCpuEnabled = True
        self.computer.IsGpuEnabled = True
        self.computer.IsMemoryEnabled = True
        self.computer.IsNetworkEnabled = True
        self.computer.IsStorageEnabled = True
        self.computer.IsPsuEnabled = True
        self.computer.Open()

    def get_values(self) -> dict[str, dict[str, Union[dict[str, float], float]]]:
        try:
            self.computer.Accept(UpdateVisitor())
            out: dict[str, dict[str, Union[dict[str, float], float]]] = {}
            # Read and display sensor data
            for hardware in self.computer.Hardware:
                hardware_dict = {}
                for subhardware in hardware.SubHardware:
                    subhardware_dict = {}
                    for sensor in subhardware.Sensors:
                        subhardware_dict[sensor.Name] = float(
                            sensor.Value) if sensor.Value is not None else -1.0  # type: ignore
                    hardware_dict[subhardware.Name] = subhardware_dict
                for sensor in hardware.Sensors:
                    hardware_dict[sensor.Name] = float(
                        sensor.Value) if sensor.Value is not None else -1.0  # type: ignore
                out[hardware.Name] = hardware_dict
            return out

        except Exception as e:
            print(f"Error: {e}")
            self.computer.Close()
            return {}
