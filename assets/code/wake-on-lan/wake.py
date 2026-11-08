"""Send a standard Wake-on-LAN magic packet using Python 3."""

import argparse
import ipaddress
import re
import socket
import time


def make_magic_packet(mac):
    if not re.fullmatch(r"[0-9A-Fa-f]{2}([:-])[0-9A-Fa-f]{2}(?:\1[0-9A-Fa-f]{2}){4}", mac):
        raise ValueError("Use a MAC such as 02:11:22:33:44:55")
    raw_mac = bytes.fromhex(mac.replace(":", "").replace("-", ""))
    return b"\xff" * 6 + raw_mac * 16


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mac", help="Target Ethernet adapter MAC address")
    parser.add_argument("broadcast", help="LAN IPv4 broadcast, e.g. 192.168.0.255")
    parser.add_argument("--port", type=int, default=9)
    parser.add_argument("--source-ip", help="Sender's LAN IPv4 address (optional)")
    args = parser.parse_args()

    try:
        packet = make_magic_packet(args.mac)
        destination = str(ipaddress.IPv4Address(args.broadcast))
        source = str(ipaddress.IPv4Address(args.source_ip)) if args.source_ip else None
        if not 1 <= args.port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
    except ValueError as error:
        parser.error(str(error))

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if source:
            sock.bind((source, 0))
        for attempt in range(1, 4):
            sent = sock.sendto(packet, (destination, args.port))
            print(f"Sent {sent} bytes to {destination}:{args.port} ({attempt}/3)")
            if attempt < 3:
                time.sleep(0.2)


if __name__ == "__main__":
    main()
