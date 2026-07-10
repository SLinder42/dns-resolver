# A program that takes a domain name on the command line and prints the resolved IP address, e.g.:

# $ python resolver.py example.com
# 104.20.23.154
# (the exact address may differ — example.com is served from multiple IPs)


# Phase 1 — Build the baseline.
# Follow the "Implement DNS in a Weekend" guide to implement a toy recursive resolver
# that can look up an A record by talking directly to the root, TLD,
# and authoritative name servers.

# https://implement-dns.wizardzines.com/

# Part 1 — Build a DNS query
# (construct the header + question, encode a domain name, send a UDP packet)

# Write the DNS Header
from dataclasses import dataclass
import dataclasses
import struct

@dataclass
class DNSHeader:
	id: int # Query ID
	flags: int
	num_questions: int = 0 # records to expect in each section of a DNS packet
	num_answers: int = 0 # records to expect in each section of a DNS packet
	num_authorities: int = 0 # records to expect in each section of a DNS packet
	num_additionals: int = 0 # records to expect in each section of a DNS packet

# Write the DNS Question
@dataclass
class DNSQuestion:
	name: bytes
	type_: int # type is built in Python function
	class_: int # class is reserved word

# Functions to convert DNSHeader and DNSQuestion to bytes

def header_to_bytes(header):
	fields = dataclasses.astuple(header)
	return struct.pack("!HHHHHH", *fields) #Header has 6 fields

def question_to_bytes(question):
	return question.name + struct.pack("!HH", question.type_, question.class_)

# Encode the domain name
def encode_dns_name(domain_name):
	encoded = b""
	for part in domain_name.encode("ascii").split(b"."): # Split URL into sections based on period
		encoded += bytes([len(part)]) + part # Append length of section to part
	return encoded + b"\x00"

# Build the query
import random
random.seed(1)

# Encodings for query types and classes defined in RFC 1035 sections 3.2.2 to 3.2.4
TYPE_A = 1
CLASS_IN = 1

def build_query(domain_name, record_type):
	name = encode_dns_name(domain_name)
	id = random.randint(0, 65535) # Pick random ID for query
	# Encoding for the flags defined in RFC 1035 Section 4.1.1
	# Recursion Desired bit is 9th bit from right in flags field
	RECURSION_DESIRED = 1 << 8 # 100000000 in binary
	header = DNSHeader(id=id, num_questions=1, flags=RECURSION_DESIRED)
	question = DNSQuestion(name=name, type_=record_type, class_=CLASS_IN)
	# Combine header and question for query
	return header_to_bytes(header) + question_to_bytes(question)

# Test the code
import socket
query = build_query("www.example.com", 1)
# socket.AF_INET is connection to internet
# socket.SOCK_DGRAM is UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Send query to DNS server 8.8.8.8 at DNS port 53
sock.sendto(query, ("8.8.8.8", 53))
# Read the response from 1024 bytes
response, _ = sock.recvfrom(1024)

# To check run "sudo tcpdump -ni any port 53" then open new cmd window and run resolver.py

# Sample input: build_query("www.example.com", TYPE_A).hex()
# Sample output: 3c5f0100000100000000000003777777076578616d706c6503636f6d0000010001

# Part 2 — Parse the response
# (decode the header, questions, and resource records, including DNS name compression)

# from part_1 import build_query, DNSQuestion, DNSHeader

# Define DNSRecord class

# from dataclasses import dataclass

@dataclass
class DNSRecord:
	name: bytes # Domain name
	type_: int # Type of record encoded as integer
	class_: int
	ttl: int
	data: bytes # Content of record

# import struct

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
from io import BytesIO
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
from typing import List

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

# import socket
# TYPE_A = 1

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

# Part 3 — Implement the resolver
# (start at a root server and follow referrals down to the authoritative server for the domain)

# Import previous functions
# from part_1 import header_to_bytes, question_to_bytes, encode_dns_name
# from part_2 import DNSHeader, DNSQuestion, DNSRecord, DNSPacket
# from part_2 import decode_name, parse_header, parse_question, parse_dns_packet
# from part_2 import ip_to_string

# TYPE_A = 1
# CLASS_IN = 1
# import random

# Build query without recursion
def build_query(domain_name, record_type):
	name = encode_dns_name(domain_name)
	id = random.randint(0, 65535)
	header = DNSHeader(id=id, num_questions=1, flags=0)
	question = DNSQuestion(name=name, type_=record_type, class_=CLASS_IN)
	return header_to_bytes(header) + question_to_bytes(question)

# import socket

# Send the query
def send_query(ip_address, domain_name, record_type):
	query = build_query(domain_name, record_type)
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.sendto(query, (ip_address, 53))
	data, _ = sock.recvfrom(1024)
	return parse_dns_packet

# Test input 1
send_query("8.8.8.8", "example.com", TYPE_A).answers[0]
# Test output 1
# DNSRecord(name=b'example.com', type_=1, class_=1, ttl=18366, data=b']\xb8\xd8"')

# Test input 2
TYPE_TXT = 16
send_query("8.8.8.8", "example.com", TYPE_TXT).answers
# Test output 2
# []

# Modify parsing to include NS records
# TYPE_A = 1
TYPE_NS = 2
# import struct

def parse_record(reader):
	name = decode_name(reader)
	data = reader.read(10)
	type_, class_, ttl, data_len = struct. unpack("!HHIH", data)
	if type_ == TYPE_NS:
		data = decode_name(reader)
	elif type_ == TYPE_A:
		data = ip_to_string(reader.read(data_len))
	else:
		data = reader.read(data_len)
	return DNSRecord(name, type_, class_, ttl, data)

# Update parse_dns_packet for new parse_record

# from io import BytesIO
# from part_2 import parse_header, parse_question, decode_name
def parse_dns_packet(data):
	reader = BytesIO(data)
	header = parse_header(reader)
	questions = [parse_questions(reader) for _ in range(header.num_questions)]
	answers = [parse_record(reader) for _ in range(header.num_answers)]
	authorities = [parse_record(reader) for _ in range(header.num_authorities)]
	additionals = [parse_record(reader) for _ in range(header.num_additionals)]

	return DNSPacket(header, questions, answers, authorities, additionals)

# Return first A record in Answer section
def get_answer(packet):
	for x in packet.answers:
		if x.type_ == TYPE_A:
			return x.data

# Return first A record in Additional section
def get_nameserver_ip(packet):
	for x in packet.additionals:
		if x.type_ == TYPE_A:
			return x.data

# Return first NS record in Authority session
def get_nameserver(packet):
	for x in packet.authorities:
		if x.type_ == TYPE_NS:
			return x.data

def resolve(domain_name, record_type):
	nameserver = "198.41.0.4"
	while True:
		print(f"Querying {nameserver} for {domain_name}")
		response = send_query(nameserver, domain_name, record_type)
		if ip := get_answer(response):
			return ip
		elif nsIP := get_nameserver_ip(response):
			nameserver = nsIP
		# Check for IP address of nameserver
		elif ns_domain := get_nameserver(response):
			nameserver = resolve(ns_domain, TYPE_A)
		else:
			raise Exception("Something went wrong")

# Exercise 1: make it work with CNAME records
# Some domain don’t have an A record: instead they have a CNAME record
# redirecting to another domain name.
# Modify the code so that it works with CNAME records.

# Exercise 2. support other record types by name
# Right now to query for an A record,
# you need to pass the number of the “A” record type (TYPE_A = 1)
# It would be way more usable if you could pass in a string like "A"
# and have it translated to the correct number.
# There are some mappings in section 3.2.2 of the RFC,
# as well as some newer ones you might need hunt down
# that were invented after 1987.

# Also the way you parse the contents (the data) of a DNS record
# depends on the type, so you could implement parsing for
# NS records, AAAA records, TXT records, etc.

# Exercise 3. don’t allow loops in DNS compression
# A malicious actor could exploit our DNS compression code
# by sending a DNS response with a DNS compression entry
# that points to itself,
# so that read_domain_name would end up in an infinite loop
# Fix it to avoid that attack.

# For example, here’s the code that avoids loops in miekg/dns
# https://github.com/miekg/dns/blob/b3dfea07155dbe4baafd90792c67b85a3bf5be23/msg.go#L430-L435

# Exercise 4. cache DNS records
# Real DNS resolvers implement caching,
# so that if you make a second query 1 second later,
# it doesn’t need to go make a million DNS queries to figure out the answer.
# One thing to keep in mind here is that DNS is case insensitive.

# Exercise 5. implement EDNS0 (extended DNS)
# In the original DNS spec, response sizes were limited to 512 bytes
# But if you implement EDNS0, you can get a larger response.

# One way you could approach this is by using tcpdump or Wireshark
# to look at the DNS request dig is sending, and the mimicking what it does.
# The specification is RFC 2671 (try starting by mimicking dig)

# You can test whether this works by running
# send_query("198.41.0.4", "google.com", TYPE_A)
# and checking if the total size of the response you get
# is more than 512 bytes.
# You can also use the DNS Reply Size Test Server to test.
# https://www.dns-oarc.net/oarc/services/replysizetest

# Exercise 6. implement TCP DNS
# To get really big DNS responses, you can implement DNS over TCP
# This is mostly the same as DNS over UDP, you just open a TCP socket instead
# You can run dig +tcp example.com if you want to capture
# some TCP DNS traffic with Wireshark to see what it should look like
# The length field is handled differently than it is with UDP
# see the RFC for more.


# Exercise 7: make your resolver into a DNS server
# Instead of running your toy resolver as a command line program,
# you can run it as a UDP server and listen on port 5353 or something
# You can test it like this:

# dig @127.0.0.1 -p 5353 example.com

# By the end of Phase 1 your program should resolve a name such as example.com
# to an IP address by performing the full recursive walk yourself
# do not use your operating system's resolver, getaddrinfo,
# or a library like dnspython to do the lookup
# You may use only the standard socket and struct modules
# (or the equivalents in another language, if approved)

# Test cases
# In your README, document how you tested Phase 1.
# For each test case show the command you ran, the output you got,
# and how you checked it was correct. Aim for breadth.

# For example:

# Several different domains resolving correctly (compare each against dig <domain>).
# A domain that returns multiple A records.
# A subdomain (e.g. www.example.com).
# An error case (e.g. a nonexistent domain) and how your resolver behaves.
