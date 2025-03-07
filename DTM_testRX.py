# DTM_testRX.py

import serial
import time

# Configuration
TX_PORT = "COM10"  # Change to match TX device's COM port (e.g., /dev/ttyUSB1 on Linux)
RX_PORT = "COM9"  # Change to match RX device's COM port (e.g., /dev/ttyUSB2 on Linux)
BAUD_RATE = 115200  # Typical HCI baud rate for BLE chips

# Test Parameters
RF_CHANNEL = 0x0F  # BLE RF channel 15 (2422 MHz)
PACKET_TYPE = 0x00  # PRBS9 (typical test payload)
DATA_LENGTH = 0x25  # 37 bytes (standard BLE test size)
NUM_PACKETS = 1500  # Number of packets to send

# HCI Commands (DTM)
HCI_LE_RECEIVER_TEST = bytes([0x01, 0x1D, 0x20, 0x01, RF_CHANNEL])
HCI_LE_TRANSMITTER_TEST = bytes([0x01, 0x1E, 0x20, 0x03, RF_CHANNEL, DATA_LENGTH, PACKET_TYPE])
HCI_LE_TEST_END = bytes([0x01, 0x1F, 0x20, 0x00])

# HCI LE Reset Command (Opcode: 0x103C)
# Format: 01 03 0C 00
HCI_LE_RESET = bytes([0x01, 0x03, 0x0C, 0x00])

def send_hci_command(ser, command, expected_response_length=7):
    """Send an HCI command and read the response."""
    ser.write(command)
    time.sleep(0.1)
    response = ser.read(expected_response_length)
    return response


#test_duration = NUM_PACKETS / 1500  # Assuming 1500 packets/sec transmission rate
#test_duration = 0.9375 # in seconds. 1500packet * 625us/packet
test_duration = 0.9 # fudge the number to account for function overhead
test_duration = 0.85 # fudge the number to account for function overhead

try:
    # Open connections to both TX and RX devices
    with serial.Serial(TX_PORT, BAUD_RATE, timeout=1) as tx_ser, serial.Serial(RX_PORT, BAUD_RATE, timeout=1) as rx_ser:
        print("Sending HCI Reset command...")
        response = send_hci_command(rx_ser, HCI_LE_RESET)
        print("Received:", response.hex())
        print("Sending HCI Reset command...")
        response = send_hci_command(tx_ser, HCI_LE_RESET)
        print("Received:", response.hex())

        print(f"Setting up RX DUT on {RX_PORT} (Channel {RF_CHANNEL})...")
        rx_response = send_hci_command(rx_ser, HCI_LE_RECEIVER_TEST)
        print("RX Response:", rx_response.hex())

        print(f"Starting TX on {TX_PORT} (Sending {NUM_PACKETS} packets)...")
        tx_response = send_hci_command(tx_ser, HCI_LE_TRANSMITTER_TEST)
        time_TXstart = time.perf_counter()
        #print("TX Response:", tx_response.hex())

        # Allow time for packets to transmit
        time.sleep(test_duration/1)

        # Stop the test on both TX and RX
        #print("Stopping TX and RX test...")
        tx_end_response = send_hci_command(tx_ser, HCI_LE_TEST_END, expected_response_length=9)
        time_TXstop = time.perf_counter()

        print("TX End Response:", tx_end_response.hex())
        FUDGE_FACTOR_FOR_TX_PACKETS_SENT = 11
        NUM_PACKETS_ACTUAL = (time_TXstop - time_TXstart)/0.000625 - FUDGE_FACTOR_FOR_TX_PACKETS_SENT
        rx_end_response = send_hci_command(rx_ser, HCI_LE_TEST_END, expected_response_length=9)
        print("RX End Response:", rx_end_response.hex())

        # Extract number of received packets
        if len(rx_end_response) == 9:
            num_packets_received = int.from_bytes(rx_end_response[7:9], byteorder='little')
            print(f"Packets received by DUT: {num_packets_received}/{NUM_PACKETS_ACTUAL}")

except serial.SerialException as e:
    print("Serial error:", e)
except Exception as e:
    print("Error:", e)
