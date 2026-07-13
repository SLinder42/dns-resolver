# Part 1 — Build a DNS query
# (construct the header + question, encode a domain name, send a UDP packet)

# Write the DNS Header
import dataclasses
from dataclasses import dataclass
import struct
import random
import socket
random.seed(1)

# Encodings for query types and classes defined in RFC 1035 sections 3.2.2 to 3.2.4
TYPE_A = 1
CLASS_IN = 1

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
