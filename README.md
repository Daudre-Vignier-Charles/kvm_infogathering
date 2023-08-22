# kvm infogathering

## Infos

This script connects to KVM servers and uses **lshw**, **virsh** and **lvm** to retrieve target information. They are then downloaded locally to be transformed into an HTML page to view them more easily.

minimum requirements :
- Bash >=4.0
- Python >=3.9 (3.x is mandatory and I have not tested with previous versions : 3.5<VERSION<3.9)

## Warning

This script is using **lshw** on the remote hypervisor. If **lshw** is not installed, it will be installed using **yum**. You may want to edit the **remote.sh** script and replace **yum** with **apt**.

## Help
Usage: start.sh [OPTION]...

Start gathering information from listed servers.

| so | lo        | help                                                                                                                         |
|----|-----------|------------------------------------------------------------------------------------------------------------------------------|
| -h | --help    | display this help                                                                                                            |
| -o | --offline | perform only the generation of the html files from downloaded data<br>in offline mode no connection to a server will be made |

Configuration is first loaded from config.sh but this can be overridden with one of these following options :
| so | lo                 | arg            | help                                                       |
|----|--------------------|----------------|------------------------------------------------------------|
| -r | --report-directory | PATH           | raw data and html files location                           |
| -s | --servers          | SRV1[,SRV2]... | comma separated list of KVM servers                        |
| -i | --ssh-cert         | CERT           | path of the certificate used to connect to the KVM servers |
| -u | --ssh-user         | USER           | remote user used to connect to the KVM servers             |


## Output (example)
![1684842304547](https://github.com/Daudre-Vignier-Charles/kvm_infogathering/assets/17654421/db84699c-a9ad-44b8-a3e8-f6929f39b08a)


