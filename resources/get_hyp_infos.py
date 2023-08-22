import sys
from lxml import etree

"""This module can be imported to use the Hypervisor class"""

def _hz_to_ghz(hz: int) -> float:
    """Convert hertz to gigahertz
    
    Parameters
    ----------
        hz : int
            Number of hertz to convert to gigahertz

    Returns
    -------
    float
        Input as GhZ

    """
    return round(float(hz)/1000**3, 2)

def _bi_to_gbi(kib : int) -> int:
    """Convert kibibytes (KiB) to gibibytes (GiB)
    
    Parameters
    ----------
        byte : int
            Number of kibibytes to convert to gibibytes

    Returns
    -------
    int
        Input as GiB

    """
    return int(int(kib)/1024**3)

class _Printable:

    def __str__(self):
        return "\n".join(["{0} : {1}".format(i, self.__dict__[i]) for i in self.__dict__.keys()])


class _HWBase():
    
    def __init__(self, hwid, hwclass, product, vendor, description):
        self.id = hwid
        self.hwclass = hwclass
        self.product = product
        self.vendor = vendor
        self.description = description


class _Machine(_HWBase, _Printable):

    def __init__(self, hwid, hwclass, product, vendor, description, serial, product_id):
        self.id = hwid
        self.hwclass = hwclass
        self.product = product
        self.vendor = vendor
        self.description = description
        self.serial = serial
        self.product_id = product_id


class _CPU(_HWBase, _Printable):

    def __init__(self, hwid, hwclass, product, vendor, description, slot, size, capacity, architecture, cores, threads):
        self.id = hwid
        self.hwclass = hwclass
        self.product = product
        self.vendor = vendor
        self.description = description
        self.slot = slot
        self.clock_min = size
        self.clock_max = capacity
        self.architecture = architecture
        self.cores = cores
        self.threads = threads


class _Memory(_HWBase, _Printable):

    def __init__(self, hwid, hwclass, description, slot, size, clock):
        self.id = hwid
        self.hwclass = hwclass
        self.description = description
        self.slot = slot
        self.size = size
        self.clock = clock


class _VG(_Printable):

    def __init__(self, name, pv, size, free):
        self.name = name
        self.pv = pv
        self.size = int(size)
        self.free = int(free)


class _PV(_Printable):

    def __init__(self, name, size, free):
        self.name = name
        self.size = int(size)
        self.free = int(free)


class _Power(_Printable):
    def __init__(self):
        super().__init__()
        pass


class _Network(_Printable):
    def __init__(self):
        pass


class _VirtualMachine(_Printable):
    def __init__(self, name, state, cpu, memory, autoboot):
        self.name = name
        self.autoboot = autoboot
        self.state = state
        self.cpu = cpu
        self.memory = int(memory) * 1024


class Hypervisor:
    """Represents a hypervisor, its characteristics, resources, virtual machines, etc.
    
    Attributes
    ----------
    machine : _Machine
        "_Machine" Object
    cpu : List[_CPU]
        "_CPU" object list
    memory : List[_Memory]
        "_Memory" object list
    vm : List[_VM]
        "_VM" object list
    pv : List[_PV]
        "_PV" object list

    Methods
    --------
    get_cpu_slots()
        Returns the CPU slots count
    get_cpu_installed()
        Returns the count of used CPU slots
    get_cpu_threads()
        Returns the total count of threads
    get_memory_slots()
        Returns the memory slots count
    get_memory_installed()
        Returns the count of memory slots used
    get_memory_total_size_installed()
        Returns the size of memories installed (in GiB)
    to_html()
        Return the hypervisor data as an HTML page
    _init_cpu(node)
        Build the CPU objects from the lshw XML file
    _init_memory(node)
        Build the Memory objects from the the lshw XML file
    _init_pv()
        Build the PV objects from the pvs output file
    _init_vm()
        Build the VirtualMachine objects from the virsh output file
    _html_gen_machine()
        Generates the part of the HTML page about the hypervisor itself
    _html_gen_vm()
        Generates the part of the HTML page about the virtual machines
    _html_gen_cpu()
        Generates the part of the HTML page about the CPUs
    _html_gen_memory()
        Generates the part of the HTML page about the memory
    _html_gen_pv()
        Generates the part of the HTML page about the PVs
    """
    def __init__(self, directory):
        """
        Parameters
        ----------
        directory : str
            Path of the directory that contains raw data
        """
        self.directory = directory
        self.debug = None
        self._tree = etree.parse(directory + "/hw")
        self._root = self._tree.getroot()
        product_code = None
        for field in self._tree.xpath("/list/node/configuration/setting"):
            if field.get("id") == "sku":
                product_code = field.get("value") 
        self.machine = _Machine(
            self._tree.xpath("/list/node")[0].get("id"),
            self._tree.xpath("/list/node")[0].get("class"),
            self._tree.xpath("/list/node/product")[0].text,
            self._tree.xpath("/list/node/vendor")[0].text,
            self._tree.xpath("/list/node/description")[0].text,
            self._tree.xpath("/list/node/serial")[0].text,
            product_code
            )
        self.cpu = []
        self.memory = []
        self.power = []
        self.network = []
        self.vm = []
        self._init_vm()
        self.pv = []
        self._init_pv()
        for node in self._root.iter("node"):
            if node.get("class") == "processor" and node.get("id").startswith("cpu"):
                self._init_cpu(node)
            if node.get("class") == "memory" and node.get("id").startswith("bank"):
                self._init_memory(node)

    def _init_cpu(self, node):
        """Build the _CPU objects from the lshw XML file
        
        Parameters
        ----------
        node : str
            CPU node from the lshw xml file

        """
        cpu = {child.tag: [child.text, child] for child in node.getchildren()}
        if "configuration" in cpu:
            configuration = {child.get("id"): child.get("value") for child in cpu["configuration"][1].getchildren()}
        else: # without else, raise key error, keys MUST exists
            configuration = {}
            cpu["size"] = [0, None]
            cpu["capacity"] = [0, None]
            cpu["width"] = [0, None]
            cpu["product"] = ["", None]
            cpu["vendor"] = ["", None]
            configuration["cores"] = None
            configuration["threads"] = None
        self.cpu.append(_CPU(
            node.get("id"),
            node.get("class"),
            cpu["product"][0],
            cpu["vendor"][0],
            cpu["description"][0],
            cpu["slot"][0],
            cpu["size"][0],
            cpu["capacity"][0],
            cpu["width"][0],
            configuration["cores"],
            configuration["threads"],
        ))
        
    def _init_memory(self, node):
        """Build the _Memory objects from the lshw XML file
        
        Parameters
        ----------
        node : str
            Memory node from the lshw xml file
        """
        memory = {child.tag: [child.text, child] for child in node.getchildren()}
        if not memory.get("size"):
            memory["size"] = ["0", None]
        if not memory.get("clock"):
            memory["clock"] = ["0", None]    
        self.memory.append(_Memory(
            node.get("id"),
            node.get("class"),
            memory["description"][0],
            memory["slot"][0],
            memory["size"][0],
            memory["clock"][0]
        ))

    def _init_pv(self):
        """Build the _PV objects from pvs output"""
        file = open(self.directory + "/pv", "r")
        file = file.readlines()
        for line in file:
            self.pv.append((_PV(*line.strip().split(","))))

    def _init_vm(self):
        """Build the _VirtualMachine objects from virsh output"""
        file = open(self.directory + "/vm", "r")
        file = file.readlines()
        for line in file:
            if line.strip():
                self.vm.append((_VirtualMachine(*line.strip().split(","))))

    def get_cpu_slots(self) -> int:
        """Returns the CPU slots count

        Returns
        -------
        int
            Number of CPU slots
        """
        return len(self.cpu)

    def get_cpu_installed(self) -> int:
        """Returns the count of used CPU slots

        Returns
        -------
        int
            Number of used CPU slot
        """
        total = 0
        for cpu in self.cpu:
            if "[empty]" not in cpu.description:
                total += 1
        return total

    def get_cpu_threads(self) -> int:
        """Returns the total count of threads

        Returns
        -------
        int
            Number of threads
        """
        total=0
        for cpu in self.cpu:
            if "[empty]" not in cpu.description:
                total += int(cpu.threads)
        return total

    def get_memory_slots(self) -> int:
        """Returns the memory slots count

        Returns
        -------
        int
            Number of memory slots
        """
        return len(self.memory)

    def get_memory_installed(self) -> int:
        """Returns the count of memory slots used

        Returns
        -------
        int
            Number of memory slots used
        """
        total = 0
        for memory in self.memory:
            if "[empty]" not in memory.description:
                total += 1
        return total
    
    def get_memory_total_size_installed(self) -> int:
        """Returns the total size of installed memories (unit : byte)

        Returns
        -------
        int
            Total size of installed memories (unit : byte)
        """
        total = 0
        for memory in self.memory:
            total += int(memory.size)
        return total

    def _html_gen_machine(self) -> str:
        """Generates the part of the HTML page about the hypervisor itself

        Returns
        -------
        str
            HTML part
        """
        vm_running=0
        vm_totalcpu=0
        vm_totalmemory=0
        for vm in self.vm:
            if vm.state == "running":
                vm_running += 1
            vm_totalcpu += int(vm.cpu)
            vm_totalmemory += int(vm.memory)

        html = """<h1 style="text-align: center; justify-content: center; align-items: center; padding-right: 370px;">{hostname}</h1>
<p style="border: 1px solid black; justify-content: center; align-items: center; text-align: center;">
{vendor} {product} ({description})<br>
serial : {serial}<br>
product id : {product_id}<br>
-----<br>
processor slots : {processors_slots}<br>
installed processor : {installed_processors}<br>
memory slots : {memory_slots}<br>
installed memory : {installed_memory}<br>
total memory amount : {memory_amount}GiB<br>
-----<br>
running virtual machines : {vm_running}/{vm_total}<br>
cpu used by virtual machines : {vm_totalcpu}/{vm_cpu}<br>
memory used by virtual machines : {vm_totalmemory}/{vm_memory}<br>
</p>""".format(
    hostname=self.machine.id,
    vendor=self.machine.vendor,
    product=self.machine.product,
    description=self.machine.description,
    serial=self.machine.serial,
    product_id=self.machine.product_id,
    processors_slots=self.get_cpu_slots(),
    installed_processors=self.get_cpu_installed(),
    memory_slots=self.get_memory_slots(),
    installed_memory = self.get_memory_installed(),
    memory_amount = _bi_to_gbi(self.get_memory_total_size_installed()),
    vm_running = vm_running,
    vm_total = len(self.vm),
    vm_totalcpu = vm_totalcpu,
    vm_cpu = self.get_cpu_threads(),
    vm_totalmemory=_bi_to_gbi(vm_totalmemory),
    vm_memory = _bi_to_gbi(self.get_memory_total_size_installed()),
    )
        return html

    def _html_gen_vm(self) -> str:
        """Generates the part of the HTML page about the virtual machines
        Returns
        -------
        str
            HTML part
        """
        html = ""
        for vm in self.vm:
            if vm.state == "running":
                background = "green"
            else:
                background = "red"
            html += """<div style="float: left; padding: 20px;">
<h2>{name}</h2>
<p style="padding: 5px; border: 1px solid black; border-radius: 5px;background-color: {background}">
state : {state}<br>
autoboot : {autoboot}<br>
cpu : {cpu}<br>
memory : {memory}GiB<br>
</p>
</div>""".format(
    background=background,
    name=vm.name,
    state=vm.state,
    autoboot=vm.autoboot,
    cpu=vm.cpu,
    memory=_bi_to_gbi(vm.memory),
    )
        return html

    def _html_gen_cpu(self) -> str:
        """Generates the part of the HTML page about the CPUs

        Returns
        -------
        str
            HTML part
        """
        html = ""
        for cpu in self.cpu:
            if "[empty]" in cpu.description:
                background = "red"
            else:
                background = "green"
            html += """<div style="float: left; padding: 20px;">
<h2>{id}</h2>
<p style="padding: 5px; border: 1px solid black; border-radius: 5px;background-color: {background}">
product : {product}<br>
vendor : {vendor}<br>
description : {description}<br>
slot : {slot}<br>
clock_min : {clock_min}GHz<br>
clock_max : {clock_max}GHz<br>
architecture : {architecture}Bits<br>
cores : {cores}<br>
threads : {threads}<br>
</p>
</div>""".format(
    id=cpu.id, 
    product=cpu.product,
    vendor=cpu.vendor,
    description=cpu.description,
    slot=cpu.slot,
    clock_min=_hz_to_ghz(cpu.clock_min),
    clock_max=_hz_to_ghz(cpu.clock_max),
    architecture=cpu.architecture,
    cores=cpu.cores,
    threads=cpu.threads,
    background=background
    )
        return html

    def _html_gen_memory(self) -> str:
        """Generates the part of the HTML page about the memory

        Returns
        -------
        str
            HTML part
        """
        html = ""
        for memory in self.memory:
            if "[empty]" in memory.description:
                background = "red"
            else:
                background = "green"
            html += """
<div style="float: left; padding: 20px;">
<h2>{id}</h2>
<p style="padding: 5px; border: 1px solid black; border-radius: 5px;background-color: {background}">
description : {description}<br>
slot : {slot}<br>
size : {size}GiB<br>
clock : {clock}GHz<br>
</p>
</div>""".format(
    id = memory.id,
    description = memory.description,
    slot = memory.slot,
    size = _bi_to_gbi(memory.size),
    clock = _hz_to_ghz(memory.clock),
    background = background
    )
        return html

    def _html_gen_pv(self) -> str:
        """Generates the part of the HTML page about the PVs

        Returns
        -------
        str
            HTML part
        """
        html = ""
        for pv in self.pv:
            html += """<h2>{disk}</h2>
<p>
Size : {size}GiB<br>
Free : {free}GiB ({percent_free}%)<br>
</p>
<div style="background-color: black; border-radius: 9px; padding: 3px;text-align: center;text="#ffffff">
<div style="background-color: orange; width: {percent_full}%; height: 20px; border-radius: 5px; text-align: center"></div>
</div>""".format(
    disk=pv.name,
    percent_full=int((pv.size-pv.free)/pv.size*100),
    percent_free=int(pv.free/pv.size*100),
    size=int(_bi_to_gbi(pv.size)),
    free=int(_bi_to_gbi(pv.free))
    )
        return html

    def to_html(self) -> str:
        """Returns all of the hypervisor data as an HTML page

        Returns
        -------
        str
            HTML page
        """
        html = """<html>
<head>
<meta content="text/html;charset=utf-8" http-equiv="Content-Type">
<meta content="utf-8" http-equiv="encoding">
</head>
<tt><a href="../report.html" style="font-size:20px;float:left;width=370px;">↪ Retour à la liste des serveurs</a></tt>"""
        html += self._html_gen_machine()
        html += self._html_gen_pv()
        html += self._html_gen_vm()
        html += """<div style="clear: both;"></div>"""
        html += self._html_gen_cpu()
        html += """<div style="clear: both;"></div>"""
        html += self._html_gen_memory()
        html += "</html>"
        return html

    @staticmethod
    def get_vm_headers():
        return "hypervisor,name;autoboot;state;cpu;memory"

    def hyp_to_csv(self) -> str:
        pass

    def vm_to_csv(self, header=False) -> str:
        if header :
            csv = [self.get_vm_headers()]
        else :
            csv = []
        for vm in self.vm:
            csv.append("{hypervisor};{name};{autoboot};{state};{cpu};{memory}".format(
                hypervisor = self.machine.id,
                name = vm.name,
                autoboot = vm.autoboot,
                state=vm.state,
                cpu = vm.cpu,
                memory = str(_bi_to_gbi(vm.memory))
            ))
        return csv

def main():
    print(Hypervisor(sys.argv[1]).to_html())

if __name__ == '__main__':
    main()