# main.py of runHCICommands
#
# For the most up-to-date reference documentation on the HCI commands:
# See https://inplay-inc.github.io/docs/in6xxe/getting-started/testing/hci_command.html
#
# Note: When working with byte arrays, the representation can be VERY CONFUSING. If python deems the value to be a
# printable ASCII character, ie in the range decimal ~30 - ~126, it will show up as THAT ASCII character in the
# debugger.
# For example, 0x30 (48) shows up as '0'.
# Another example, 0x46 (106) shows up as 'F'.
# Looking at ASCII '0' and 'F' intermixed with hex numbers that use 0 and F as numeric representations is VERY
# CONFUSING! So beware.
#
# Hardware setup:
# This script was used with IN628 F0 Series QFN48 Development Kit Version F0 12122023.
# This script was also used with the IN6XX series development kit DK Version D0-07102021.
# It is not necessary to use the Jlink SWD interface to interact with the DUT in this setup. All the necessary
# communication is done over the UART. The USB to UART1 is used for the communication.
# If using the IN628 F0 Series DK, it is necessary to put 3 jumpers on H16.UART1, to connect the VDD, RX, and TX from
# the USB-UART bridge to the UART1 pins of the DUT.
#
# The firmware project used \in-dev_hci_ver0x16\proj\misc\proj_ate_test_hci_no_os\build\mdk\proj_trx_test_hci. The
# binary file output from that project is downloaded to the DUT using the 'inplay_programmer.exe' application. Be
# sure that the 2 filed 'JTAGDLL.dll' and 'UARTDLL.dll' are in the same location as the 'inplay_programmer.exe' directory
# when it is executed.
# The programmer must download a binary (.bin) image to the DUT's memory.
#
# Other possibly necessary drivers: USB2UART_Driver\CH341SER which can be downloaded from the internet. This is the
# driver used by the host PC to the USB-UART bridge chip.
#
# The script's goal is to easily configure the DUT to make some of the measurements in the System Power Consumption (ie
# Table 22) of InPlay's IN6xx datasheets. The script can make the following measurements:
# 2.4GHz RX mode - 1Mbps (LNA IBIAS=4, default)
# 2.4GHz RX mode - 1Mbps (LNA IBIAS=7, highest current, lowest noise figure)
# 2.4GHz RX mode - 2Mbps
# 2.4GHz TX mode - 1Mbps, Pout=0dBm (using TX power table)
# 2.4GHz TX mode - 2Mbps, Pout=0dBm (using TX power table)
# It is necessary to connect a multimeter in current measuring mode on the VBAT input to the DUT. For the IN628E DK
# that could be H17 pins 9-10.
# Initial development of this script used an ammeter with no connectivity, but an instrument with IP-network,
# USB, serial, or GPIB connectivity could easily be configured to do the data collection automatically.


import serial
import time

# Configure the serial port
#SERIAL_PORT = "COM8"    # Change to the correct port (eg "/dev/cu.*" on MacOS)
#SERIAL_PORT = "COM9"    # Change to the correct port (eg "/dev/cu.*" on MacOS)
SERIAL_PORT = "COM10"    # Change to the correct port (eg "/dev/cu.*" on MacOS)
BAUD_RATE = 115200      # Typical for HCI UART

# RF channel (0x00 - 0x27, corresponds to 2402 MHz - 2480 MHz in 2 MHz steps)
RF_CHANNEL          = 0x00  # Example: Channel 15 (2432 MHz)

PACKET_TYPE         = 0x0
DATA_LENGTH         = 0x25
PHY_2M              = 0x2       # 1: 1M, 2: 2M, 3: LE coded PHY
PHY_1M              = 0x1       # 1: 1M, 2: 2M, 3: LE coded PHY
CONT_TX             = 0x1       # 0: not continuous, 1: continuous TX
TX_GAIN             = 0x0       # 0: don't change TX power setting. Use Set TX Power command.

TX_POWER            = 0x0F    # see Table 3 on github doc: 0x00:Max Power, 0x01:7dBm, 0x0F:0dBm, 0x1A:-20dBm
TX_POWER_TABLE      = 0x01    # Default is 1 (low power mode), 4 is for high power mode
MOD_INDEX           = 0x0     # 0: assume TRX has standard modulation index

HCI_GET_VERSION             = bytes([0x01, 0x5B, 0xFC, 0x00])
HCI_GET_HW_ID               = bytes([0x01, 0x50, 0xFC, 0x00])
HCI_SET_TX_POWER            = bytes([0x01, 0x07, 0xFC, 0x01, TX_POWER])
HCI_LE_VENDOR_TX_COMMAND    = bytes([0x01, 0x0D, 0xFC, 0x08, RF_CHANNEL, DATA_LENGTH, PACKET_TYPE, PHY_2M, 0x0, CONT_TX, 0x0, 0x0])
HCI_LE_VENDOR_TX_TEST_END   = bytes([0x01, 0x53, 0xFC, 0x00])  # deprecated by Naimin, use HCI_LE_TEST_END
HCI_LE_CARRIER_TX           = bytes([0x01, 0x01, 0xFC, 0x02, RF_CHANNEL, TX_GAIN])
HCI_LE_STOP_CARRIER_TX      = bytes([0x01, 0x04, 0xFC, 0x00])  # deprecated by Naimin, use HCI_LE_TEST_END

HCI_LE_RECEIVER_TEST        = bytes([0x01, 0x1D, 0x20, 0x01, RF_CHANNEL])
HCI_LE_ENH_RX_TEST          = bytes([0x01, 0x33, 0x20, 0x03, RF_CHANNEL, PHY_2M, MOD_INDEX])
HCI_LE_TRANSMITTER_TEST     = bytes([0x01, 0x1E, 0x20, 0x03, RF_CHANNEL, DATA_LENGTH, PACKET_TYPE])
HCI_LE_ENH_TX_TEST          = bytes([0x01, 0x34, 0x20, 0x04, RF_CHANNEL, DATA_LENGTH, PACKET_TYPE, PHY_2M])
HCI_LE_TEST_END             = bytes([0x01, 0x1F, 0x20, 0x00])

HCI_LE_RESET                = bytes([0x01, 0x03, 0x0C, 0x00])
HCI_ENTER_DEEP_SLEEP        = bytes([0x01, 0x54, 0xFC, 0x00])

ADDRESS                     = 0x46A030B4
#ADDRESS                     = 0x46A030C4
#ADDRESS                     = 0x46A030B8
#ADDRESS                     = 0x46A030E0
#byte_array = ADDRESS.to_bytes(4, byteorder='big')

ADDRESS_BYTE0               = ADDRESS & 0xFF
ADDRESS_BYTE1               = (ADDRESS >> 8) & 0xFF
ADDRESS_BYTE2               = (ADDRESS >> 16) & 0xFF
ADDRESS_BYTE3               = (ADDRESS >> 24) & 0xFF

HCI_READ_REGISTER           = bytes([0x01, 0x0E, 0xFC, 0x04, ADDRESS_BYTE0, ADDRESS_BYTE1, ADDRESS_BYTE2, ADDRESS_BYTE3])
HCI_WRITE_REGISTER          = bytearray([0x01, 0x0F, 0xFC, 0x08])
HCI_WRITE_REGISTER.append(ADDRESS_BYTE0)
HCI_WRITE_REGISTER.append(ADDRESS_BYTE1)
HCI_WRITE_REGISTER.append(ADDRESS_BYTE2)
HCI_WRITE_REGISTER.append(ADDRESS_BYTE3)

def send_hci_command(ser, command, expected_response_length=7):
    """Send an HCI command and read the response."""
    ser.write(command)
    time.sleep(0.1)  # Small delay to allow response
    response = ser.read(expected_response_length)
    return response

try:
    # Open serial connection
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        test_duration = 5  # [s] Adjust as needed
        #send_hci_command(ser, HCI_LE_RESET)

        print(f"Sending HCI_GET_VERSION command...")
        response = send_hci_command(ser, HCI_GET_VERSION, expected_response_length=11)
        print("Received:", response.hex())
        fw_ver = response[10:6:-1]
        print(f"FW Ver: {fw_ver.hex()}")

        print(f"Sending HCI_GET_HW_ID command...")
        response = send_hci_command(ser, HCI_GET_HW_ID, expected_response_length=11)
        print("Received:", response.hex())
        hw_id = response[10:6:-1]
        print(f"HW ID: {hw_id}")

        print(f"Sending HCI_READ_REGISTER {HCI_READ_REGISTER.hex()} to {ADDRESS:#x}...")
        response = send_hci_command(ser, HCI_READ_REGISTER, expected_response_length=11)
        #reg_val = int.from_bytes(response[7:11], byteorder='little')
        #reg_val = response[10:6:-1]
        reg_val = response[7:11]
        print("Received:", response.hex())
        print("reg_val.hex():", reg_val.hex())

        HCI_WRITE_REGISTER.append(0x24)     # lower [2:0] represent LNA bias, 0: lowest current, 4: default, 7: highest current (lowest NF)
        #HCI_WRITE_REGISTER.append(reg_val[0])
        HCI_WRITE_REGISTER.append(reg_val[1])
        HCI_WRITE_REGISTER.append(reg_val[2])
        HCI_WRITE_REGISTER.append(reg_val[3])
        #print("HCI_WRITE_REGISTER:", HCI_WRITE_REGISTER.hex())
        print(f"Sending HCI_WRITE_REGISTER {HCI_WRITE_REGISTER}...")
        response = send_hci_command(ser, HCI_WRITE_REGISTER)
        print("Received:", response.hex())

        print(f"Sending HCI_LE_RECEIVER_TEST command on channel {RF_CHANNEL}...")
        response = send_hci_command(ser, HCI_LE_RECEIVER_TEST)
        print("Received:", response.hex())

        # Let the test run for a few seconds
        print(f"Receiving packets for {test_duration} seconds...")
        time.sleep(test_duration)

        # Send HCI LE Test End command
        print("Sending HCI_LE_TEST_END and retrieving packet count...")
        response = send_hci_command(ser, HCI_LE_TEST_END, expected_response_length=9)
        print("Received:", response.hex())

        print(f"Sending HCI_LE_ENH_RX_TEST command on channel {RF_CHANNEL}...")
        response = send_hci_command(ser, HCI_LE_ENH_RX_TEST)
        print("Received:", response.hex())

        # Let the test run for a few seconds
        test_duration = 5  # Adjust as needed
        print(f"Receiving packets for {test_duration} seconds...")
        time.sleep(test_duration)

        # Send HCI LE Test End command
        print("Sending HCI_LE_TEST_END and retrieving packet count...")
        response = send_hci_command(ser, HCI_LE_TEST_END, expected_response_length=9)
        print("Received:", response.hex())

        # Send HCI transmitter test command
        print(f"Sending HCI_SET_TX_POWER to {TX_POWER}...")
        response = send_hci_command(ser, HCI_SET_TX_POWER)
        print("Received:", response.hex())

        print(f"Sending HCI_LE_VENDOR_TX_COMMAND (modulated 2M PHY, continuous TX) on channel {RF_CHANNEL}...")
        response = send_hci_command(ser, HCI_LE_VENDOR_TX_COMMAND)
        print("Received:", response.hex())
        print(f"Transmitting on channel {RF_CHANNEL} for {test_duration} seconds...")
        time.sleep(test_duration)

        print("Sending HCI_LE_TEST_END command")
        response = send_hci_command(ser, HCI_LE_TEST_END, expected_response_length=8)
        print("Received:", response.hex())

        #print("Sending HCI LE VENDOR TX TEST END COMMAND")
        #response = send_hci_command(ser, HCI_LE_VENDOR_TX_TEST_END)
        #print("Received:", response.hex())

        # Send HCI LE Carrier TX command
        print(f"Sending HCI_LE_CARRIER_TX (LO tone only) on channel {RF_CHANNEL}...")
        response = send_hci_command(ser, HCI_LE_CARRIER_TX)
        print("Received:", response.hex())
        print(f"Transmitting on channel {RF_CHANNEL} for {test_duration} seconds...")
        time.sleep(test_duration)

        print("Sending HCI_LE_TEST_END command...")
        response = send_hci_command(ser, HCI_LE_TEST_END, expected_response_length=8)
        print("Received:", response.hex())

        print("Sending ENTER_DEEP_SLEEP command...")
        response = send_hci_command(ser, HCI_ENTER_DEEP_SLEEP)
        print("Received:", response.hex())

        ser.close()

except serial.SerialException as e:
    print("Serial error:", e)
except Exception as e:
    print("Error:", e)