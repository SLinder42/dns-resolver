# Part 2 — Parse the response
# (decode the header, questions, and resource records, including DNS name compression)

from DNSquery import build_query, DNSQuestion, DNSHeader
from dataclasses import dataclass
import struct
from io import BytesIO
from typing import List
import socket

TYPE_A = 1

# Define DNSRecord class


@dataclass
class DNSRecord:
	name: bytes # Domain name
	type_: int # Type of record encoded as integer
	class_: int
	ttl: int
	data: bytes # Content of record

def parse_header(reader):
	items = struct.unpack("!HHHHHH", reader.read(12))
	return DNSHeader(*items)

# Parse domain with DNS compression
def decode_name(reader):
	parts = []
	while (length := reader.read(1)[0]) != 0:
		# Check if first 2 bits are 1s
		if length & 0b1100_0000:
			parts.append(decode_compressed_name(length, reader))
			break
		else:
			parts.append(reader.read(length))
	return b".".join(parts)

def decode_compressed_name(length, reader):
	# Take bottom 6 bits of length byte plus next byte
	pointer_bytes = bytes([length & 0b0011_1111]) + reader.read(1)
	# Convert bytes to integer
	pointer = struct.unpack("!H", pointer_bytes)[0]
	# Save current position in reader
	current_pos = reader.tell()
	# Move to pointer position in DNS packet
	reader.seek(pointer)
	# Decodes this segment
	result = decode_name(reader)
	# Restores current position in reader
	reader.seek(current_pos)
	# Return the name
	return result

# Parse question
def parse_question(reader):
	name = decode_name(reader)
	data = reader.read(4)
	type_, class_ = struct.unpack("!HH", data)
	return DNSQuestion(name, type_, class_)

# Test input
reader = BytesIO(response)
parse_header(reader)
parse_question(reader)

# Expected output
# DNSQuestion(name=b'www.example.com', type_=1, class_=1)

# Parse record
def parse_record(reader):
	name = decode_name(reader)
	data = reader.read(10) # Type, class, TTL, and data length are 10 bytes
	# HHIH stands for 2 byte int, 2 byte int, 4 byte int, 2 byte int
	type_, class_, ttl, data_len = struct.unpack("!HHIH", data)
	data = reader.read(data_len)
	return DNSRecord(name, type_, class_, ttl, data)

# Test input
reader = BytesIO(response)
parse_header(reader)
parse_question(reader)
parse_record(reader)

# Test output
# DNSRecord(name=b'www.example.com', type_=1, class_=1, ttl=21147, data=b']\xb8\xd8"')

# Parse DNS Packet

# Define contents of DNS packet

@dataclass
class DNSPacket:
	header: DNSHeader
	questions: List[DNSQuestion]
	answers: List[DNSRecord]
	authorities: List[DNSRecord]

def parse_dns_packet(data):
	reader = BytesIO(data)
	header = parse_header(reader)
	questions = [parse_questions(reader) for _ in range(header.num_questions)]
	answers = [parse_record(reader) for _ in range(header.num_answers)]
	authorities = [parse_record(reader) for _ in range(header.num_authorities)]
	additionals = [parse_record(reader) for _ in range(header.num_additionals)]

	return DNSPacket(header, questions, answers, authorities, additionals)

# Test input
# packet = parse_dns_packet(response)
# packet

# Test output
# DNSPacket(header=DNSHeader(id=24662, flags=33152, num_questions=1, num_answers=1, num_authorities=0, num_additionals=0), questions=[DNSQuestion(name=b'www.example.com', type_=1, class_=1)], answers=[DNSRecord(name=b'www.example.com', type_=1, class_=1, ttl=21147, data=b']\xb8\xd8"')], authorities=[], additionals=[])

# Convert IP address to string
def ip_to_string(ip):
	return ".".join([str(x) for x in ip])

# Function to look up domain name and print out IP address



def lookup_domain(domain_name):
	query = build_query(domain_name, TYPE_A)
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.sendto(query, ("8.8.8.8", 53))
	# Get response
	data, _ = sock.revfrom(1024)
	response = parse_dns_packet(data)
	return ip_to_string(response.answers[0].data)

# Test Input 1
lookup_domain("example.com")
# Test Output 1
# 93.184.216.34

# Test Input 2
lookup_domain("recurse.com")
# Test Output 2
# 13.225.195.117

# Test Input 3
lookup_domain("metafilter.com")
# Test Output 3
# 54.203.56.158

# Test Input 4
lookup_domain("facebook.com")
# Test Output 4
# 9.115.116.97.114.45.109.105.110.105.4.99.49.48.114.192.16
# Wrong record type

# Test Input 5
lookup_domain("metafilter.com")
# Test Output 5
# 192.16
# Wrong record type