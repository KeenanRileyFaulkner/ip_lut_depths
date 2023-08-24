"""Calculate the depth of all luts in a given IP"""
from argparse import ArgumentParser
from pathlib import Path

import jpype
import jpype.imports

_STARTED = False
RAPIDWRIGHT_PATH = Path("/home/keenanrf/research/ipPropTests/third_party/RapidWright")


def start_jvm():
    """Start the jpype JVM"""
    global _STARTED  # pylint: disable=global-statement
    if _STARTED:  # pylint: disable=used-before-assignment
        return

    jpype.startJVM(
        classpath=[
            str(RAPIDWRIGHT_PATH / "bin"),
            *(str(s) for s in (RAPIDWRIGHT_PATH / "jars").glob("*.jar")),
        ]
    )

    _STARTED = True


start_jvm()
from com.xilinx.rapidwright.device import SiteTypeEnum
from com.xilinx.rapidwright.design import Design, Unisim
from com.xilinx.rapidwright.edif import EDIFDirection, EDIFNet, EDIFPropertyValue, EDIFValueType
from java.lang import System
from java.io import PrintStream, File


class Calculator:
    """Calculate the depth of all luts in a given IP"""

    def __init__(self, edf, dcp):
        self.edf = edf
        self.dcp = dcp
        self.rw_design = None
        self.rw_netlist = None

    def calculate_lut_depths(self):
        """Calculate the depth of all luts in a given IP"""
        self.rw_design = Design.readCheckpoint(self.dcp, self.edf)
        self.rw_design.flattenDesign()

        # First thing first, get the inputs to the top module as EDIFPort objects
        top_level_inputs = self.__get_top_level_inputs()

        # Next, get the nets connected to those inputs as EDIFNet objects
        top_level_input_nets = self.__get_top_level_input_nets(top_level_inputs)

        # Now get all the LUTs that are placed in the design
        luts = self.__get_luts()

        # Keep track of which luts we have assigned a depth to
        assigned_luts = set()

        # Get a map of all EDIFPortInsts to which the top_level_input nets are connected
        connections = self.__get_top_level_input_connections(top_level_input_nets)
        print("\n\nconnections:\n", "\t")
        for net, port_insts in connections.items():
            print(
                "\t",
                net,
                "\tport 0 is input:",
                port_insts[0].isInput(),
                "\tport 1 is input:",
                port_insts[1].isInput(),
            )

        # lut6s = self.__get_lut6s()
        # lut6s_inputs = list(map(self.__get_lut6_inputs, lut6s))
        # print("input pins:")
        # for pin in lut6s_inputs:
        #     print(f"\t{pin.getName()}")

    def __get_top_level_inputs(self):
        """Get the top level inputs on a given IP"""
        top_cell = self.rw_design.getTopEDIFCell()
        top_ports = top_cell.getPorts()
        inputs = []
        for port in top_ports:
            if port.isInput():
                inputs.append(port)
        return inputs

    def __get_top_level_input_nets(self, top_level_inputs):
        """Get the EDIFNets that are connected to the top level inputs"""
        all_nets = []
        print("\n\ntop level inputs:\n")
        for tl_input in top_level_inputs:
            nets = tl_input.getInternalNets()
            print("\t", tl_input, nets, "\n")
            all_nets.extend(nets)
        return all_nets

    def __get_luts(self):
        """Get all the lut bels that are used in the design"""
        lut6s = []
        for site_inst in self.rw_design.getSiteInsts():
            for cell in site_inst.getCells():
                if "LUT" in cell.getType() and cell.isPlaced():
                    lut6s.append(cell.getEDIFCellInst())

        return lut6s

    def __get_top_level_input_connections(self, top_level_input_nets):
        """Get the ports connected to the top level input nets"""
        connections = {}
        for net in top_level_input_nets:
            sinks = []
            for port in net.getPortInsts():
                if port.isInput():
                    sinks.append(port)
            connections[net] = sinks

        return connections


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-edf",
        type=Path,
        required=True,
        help="the path to the edf file containing a single IP for which to calculate lut depths",
    )
    parser.add_argument(
        "-dcp",
        type=Path,
        required=True,
        help="the path to the dcp file containing a single IP for which to calculate lut depths",
    )
    args = parser.parse_args()
    calc = Calculator(args.edf, args.dcp)
    calc.calculate_lut_depths()
