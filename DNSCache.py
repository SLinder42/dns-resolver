# Phase 2 - Add record cache to resolver

# Import previous functions
from DNSquery import header_to_bytes, question_to_bytes, encode_dns_name
from DNSparser import DNSHeader, DNSQuestion, DNSRecord, DNSPacket
from DNSparser import decode_name, parse_header, parse_question, parse_dns_packet, ip_to_string
from DNSresolver import build_query, send_query, parse_record, parse_dns_packet, get_answer, get_nameserver_ip, get_nameserver, resolve
from io import BytesIO

TYPE_A = 1
CLASS_IN = 1
TYPE_NS = 2
TYPE_TXT = 16

import random
import struct
import socket
import time

dns_server="8.8.8.8"

cache = {} # domain -> (ip, expiry)

def DNSresolve_cache(domain):
	now = time.time()
	# Lookup the cache
	if domain in cache:
		ipresult, expiry = cache(domain)
		# Stop if cache is expired
		if now < expiry:
			print("Cache has been hit")
			return ipresult
	else:
		# Store result in cache
		cache[domain] = ipresult, now+ttl

	return ipresult