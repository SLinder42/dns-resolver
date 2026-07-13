# Part 3 — Implement the resolver
# (start at a root server and follow referrals down to the authoritative server for the domain)

# Import previous functions
from DNSquery import header_to_bytes, question_to_bytes, encode_dns_name
from DNSparser import DNSHeader, DNSQuestion, DNSRecord, DNSPacket
from DNSparser import decode_name, parse_header, parse_question, parse_dns_packet, ip_to_string
from io import BytesIO

TYPE_A = 1
CLASS_IN = 1
TYPE_NS = 2

import random
import struct

# Build query without recursion
def build_query(domain_name, record_type):
	name = encode_dns_name(domain_name)
	id = random.randint(0, 65535)
	header = DNSHeader(id=id, num_questions=1, flags=0)
	question = DNSQuestion(name=name, type_=record_type, class_=CLASS_IN)
	return header_to_bytes(header) + question_to_bytes(question)

import socket

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
