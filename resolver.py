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

# Part 2 — Parse the response
# (decode the header, questions, and resource records, including DNS name compression)

# Part 3 — Implement the resolver
# (start at a root server and follow referrals down to the authoritative server for the domain)

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
