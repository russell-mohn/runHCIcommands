For the most up-to-date reference documentation on the HCI commands:
See https://inplay-inc.github.io/docs/in6xxe/getting-started/testing/hci_command.html

Hardware setup:
This script was used with IN628 F0 Series QFN48 Development Kit Version F0 12122023.
This script was also used with the IN6XX series development kit DK Version D0-07102021.
It is not necessary to use the Jlink SWD interface to interact with the DUT in this setup. All the necessary
communication is done over the UART. The USB to UART1 is used for the communication.
If using the IN628 F0 Series DK, it is necessary to put 3 jumpers on H16.UART1, to connect the VDD, RX, and TX from
the USB-UART bridge to the UART1 pins of the DUT.

The firmware project used \in-dev_hci_ver0x16\proj\misc\proj_ate_test_hci_no_os\build\mdk\proj_trx_test_hci. The
binary file output from that project is downloaded to the DUT using the 'inplay_programmer.exe' application. Be
sure that the 2 files 'JTAGDLL.dll' and 'UARTDLL.dll' are in the same location as the 'inplay_programmer.exe' directory
when it is executed.
The programmer must download a binary (.bin) image to the DUT's memory.

Other possibly necessary drivers: USB2UART_Driver\CH341SER which can be downloaded from the internet. This is the
driver used by the host PC to the USB-UART bridge chip.

The script's goal is to easily configure the DUT to make some of the measurements in the System Power Consumption (ie
Table 22) of InPlay's IN6xx datasheets. The script can make the following measurements:
* 2.4GHz RX mode - 1Mbps (LNA IBIAS=4, default)
* 2.4GHz RX mode - 1Mbps (LNA IBIAS=7, highest current, lowest noise figure)
* 2.4GHz RX mode - 2Mbps
* 2.4GHz TX mode - 1Mbps, Pout=0dBm (using TX power table)
* 2.4GHz TX mode - 2Mbps, Pout=0dBm (using TX power table)

It is necessary to connect a multimeter in current measuring mode on the VBAT input to the DUT. For the IN628E DK
that could be H17 pins 9-10.
Initial development of this script used an ammeter with no connectivity, but an instrument with IP-network,
USB, serial, or GPIB connectivity could easily be configured to do the data collection automatically.
