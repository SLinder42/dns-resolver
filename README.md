# DNS Resolver

## Group Information

**Group Number:** 1

**Members:**

- Amirreza Arefi
- Simon Linder

## Project Overview

This project implements an iterative DNS resolver from scratch in Python 3.

The final runnable implementation is:

```text
resolver.py
```

The program does not use the operating system's resolver, `getaddrinfo`,
`dnspython`, or another external DNS-resolution library.

The resolver:

- Constructs DNS query packets.
- Sends non-recursive DNS queries over UDP.
- Parses DNS response packets.
- Handles DNS name compression.
- Follows referrals from root servers to TLD and authoritative servers.
- Resolves IPv4 A records.
- Caches DNS records while honoring their TTLs.
- Reuses cached NS and glue A records.
- Supports CNAME alias resolution.

## Requirements

- Python 3
- An Internet connection that allows UDP DNS traffic on port 53
- `dig` for independent verification

## How to Run

Open a terminal in the repository directory:

```bash
cd dns-resolver
```

Resolve a domain:

```bash
python3 resolver.py example.com
```

Example output:

```text
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
172.66.147.243
```

DNS server addresses, TTLs, and returned IP addresses may vary because DNS
responses can change by time, location, authoritative server, and load
balancing.

### Cache Test Commands

Repeated lookup:

```bash
python3 resolver.py --cache-test example.com
```

TTL expiration:

```bash
python3 resolver.py --ttl-test example.com
```

Intermediate NS/glue reuse:

```bash
python3 resolver.py --delegation-test example.com www.example.com
```

---

## Phase 1

### Implementation

Phase 1 implements the baseline resolver using the
**Implement DNS in a Weekend** guide.

The resolver performs the following steps:

1. Encodes the requested domain using DNS label encoding.
2. Constructs a DNS header and question.
3. Sends a non-recursive DNS query over UDP.
4. Parses the header, question, answer, authority, and additional sections.
5. Decodes compressed DNS names.
6. Begins at a root DNS server.
7. Follows a referral to the appropriate TLD server.
8. Follows another referral to an authoritative server.
9. Returns an IPv4 A record.

Important functions include:

- `encode_dns_name()`
- `build_query()`
- `send_query()`
- `parse_dns_packet()`
- `resolve()`

### Test Cases

#### Test 1 — Basic A-record lookup

Command:

```bash
python3 resolver.py example.com
```

Output:

```text
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
172.66.147.243
```

Verification:

```bash
dig example.com A
```

The resolver returned a valid A record. `example.com` can return multiple
valid addresses, so the exact result may vary.

#### Test 2 — Google

Command:

```bash
python3 resolver.py google.com
```

Example output:

```text
CACHE MISS: google.com type=1
Querying 198.41.0.4 for google.com
Querying 192.41.162.30 for google.com
Querying 216.239.34.10 for google.com
142.251.218.110
```

Verification:

```bash
dig google.com A
```

The resolver completed the iterative DNS walk and returned a valid Google
A record. The exact address may differ from the local recursive resolver's
answer.

#### Test 3 — GitHub

Command:

```bash
python3 resolver.py github.com
```

Verification:

```bash
dig github.com A
```

The resolver contacted the DNS hierarchy and returned an A record for
`github.com`.

#### Test 4 — Subdomain

Command:

```bash
python3 resolver.py www.example.com
```

Verification:

```bash
dig www.example.com A
```

The resolver successfully resolved the subdomain.

#### Test 5 — Multiple A records

Command:

```bash
dig example.com A
```

`dig` returned multiple valid A records for `example.com`.

The current command-line resolver returns the first usable A record from
the response.

#### Test 6 — Nonexistent domain

Command:

```bash
python3 resolver.py this-domain-should-not-exist-12345.com
```

The test was used to observe the resolver's failure behavior for a
nonexistent domain. Graceful NXDOMAIN handling was not selected as a
Phase 3 extension.

---

## Phase 2

### Implementation

Phase 2 adds an in-memory DNS record cache directly to `resolver.py`.

Cache entries are keyed by:

```text
(normalized domain name, record type)
```

Each entry stores:

- Record data
- TTL
- Expiration time

Before sending a DNS request, the resolver checks the cache. An unexpired
entry is returned immediately. An expired entry is rejected and the record
is fetched again.

The resolver caches records from all three resource-record sections:

- Answer records
- Authority records
- Additional records

This allows the resolver to cache:

- Final A records
- CNAME records
- NS delegation records
- Glue A records

The implementation follows the TTL behavior described in
**RFC 1035 Sections 3.2.1 and 4.1.3**.

### Test Cases

#### Test 1 — Repeated lookup is served from cache

Command:

```bash
python3 resolver.py --cache-test example.com
```

Output:

```text
=== FIRST LOOKUP ===
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
Result: 172.66.147.243
Network queries: 3

=== SECOND LOOKUP ===
CACHE HIT: example.com type=1
Result: 172.66.147.243
New network queries: 0
```

The first lookup sent three DNS queries. The second lookup was served
entirely from the cache and sent zero new network queries.

#### Test 2 — Record is fetched again after TTL expiration

Command:

```bash
python3 resolver.py --ttl-test example.com
```

Relevant output:

```text
=== INITIAL LOOKUP ===
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
Result: 104.20.23.154
Network queries: 3

Waiting 3 seconds for the test TTL to expire...

=== LOOKUP AFTER EXPIRATION ===
CACHE EXPIRED: example.com type=1
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
Result: 172.66.147.243
New network queries: 3
```

For this test only, cached TTLs are capped at two seconds so expiration can
be demonstrated quickly. Normal resolver execution honors the actual TTL
received in the DNS response.

After the test TTL expired, the cached answer was not served. The resolver
performed three new network queries.

#### Test 3 — Cached NS and glue records are reused

Command:

```bash
python3 resolver.py --delegation-test example.com www.example.com
```

Output:

```text
=== FIRST LOOKUP: example.com ===
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
Result: 172.66.147.243
Network queries: 3

=== SECOND LOOKUP: www.example.com ===
CACHE HIT: example.com type=2
CACHE HIT: hera.ns.cloudflare.com type=1
Using cached delegation for example.com:
hera.ns.cloudflare.com -> 108.162.192.162
Querying 108.162.192.162 for www.example.com
Result: 172.66.147.243
New network queries: 1
```

The second lookup reused a cached NS delegation and its cached glue A
record. It contacted the authoritative server directly, skipping the root
and TLD queries.

---

## Phase 3

### Extension: CNAME Resolution

#### RFC Gap

The baseline resolver handled A and NS records but did not correctly follow
CNAME aliases.

A CNAME record maps an alias to another canonical domain name rather than
directly containing an IP address.

Without CNAME support, real domains such as `www.reddit.com` and
`www.python.org` can fail to resolve because the DNS answer contains another
hostname instead of an IPv4 address.

**RFC 1034 Section 3.6.2** defines Canonical Name records and their alias
behavior.

#### Implementation

The extension:

1. Defines `TYPE_CNAME = 5`.
2. Parses CNAME record data as a compressed DNS name.
3. Adds `get_cname()` to search the answer section.
4. Updates `resolve()` to resolve the canonical name recursively.
5. Logs the alias transition for testing and demonstration.

Relevant logic:

```python
elif cname := get_cname(response):
    cname = normalize_name(cname)
    print(f"Following CNAME: {domain_name} -> {cname}")
    return resolve(cname, TYPE_A)
```

### Test Cases

#### Test 1 — Before CNAME support

The baseline was tested from the Phase 1 commit.

Command:

```bash
python3 resolver.py www.reddit.com
```

Output:

```text
Querying 198.41.0.4 for www.reddit.com
Querying 192.41.162.30 for www.reddit.com
Querying 205.251.193.122 for www.reddit.com
Querying 198.41.0.4 for b'ns-1029.awsdns-00.org'
Traceback (most recent call last):
  ...
AttributeError: 'bytes' object has no attribute 'encode'
```

The baseline failed before reaching a final A record.

#### Test 2 — Reddit CNAME after extension

Command:

```bash
python3 resolver.py www.reddit.com
```

Output:

```text
CACHE MISS: www.reddit.com type=1
Querying 198.41.0.4 for www.reddit.com
Querying 192.41.162.30 for www.reddit.com
Querying 205.251.193.122 for www.reddit.com
Following CNAME: www.reddit.com -> reddit.map.fastly.net
CACHE MISS: reddit.map.fastly.net type=1
Querying 198.41.0.4 for reddit.map.fastly.net
Querying 192.55.83.30 for reddit.map.fastly.net
Querying 23.235.32.32 for reddit.map.fastly.net
151.101.41.140
```

Verification:

```bash
dig www.reddit.com CNAME
```

Relevant output:

```text
www.reddit.com. IN CNAME reddit.map.fastly.net.
```

The alias returned by `dig` matched the alias detected and followed by the
resolver.

#### Test 3 — Python CNAME

Command:

```bash
python3 resolver.py www.python.org
```

Output:

```text
CACHE MISS: www.python.org type=1
Querying 198.41.0.4 for www.python.org
Querying 199.249.112.1 for www.python.org
Querying 205.251.196.110 for www.python.org
Following CNAME: www.python.org -> dualstack.python.map.fastly.net
CACHE MISS: dualstack.python.map.fastly.net type=1
Querying 198.41.0.4 for dualstack.python.map.fastly.net
Querying 192.55.83.30 for dualstack.python.map.fastly.net
Querying 23.235.32.32 for dualstack.python.map.fastly.net
151.101.0.223
```

Verification:

```bash
dig www.python.org CNAME
```

Relevant output:

```text
www.python.org. IN CNAME dualstack.python.map.fastly.net.
```

The resolver followed the same canonical name reported by `dig` and
returned the final A record.

#### Test 4 — Normal A-record regression test

Command:

```bash
python3 resolver.py example.com
```

Output:

```text
CACHE MISS: example.com type=1
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
172.66.147.243
```

This confirms that adding CNAME support did not break normal A-record
resolution.

---

## Contributions

### Amirreza Arefi

- Fixed and tested the Phase 1 iterative resolver.
- Added command-line execution.
- Implemented CNAME parsing and alias resolution.
- Integrated and completed the TTL-based cache.
- Added cache test modes.
- Tested the resolver and documented results.

### Simon Linder

- Created the initial Phase 2 cache work.
- Refactored resolver-related files.
- Contributed project setup and baseline implementation work.

## References

- Julia Evans, **Implement DNS in a Weekend**
- RFC 1034, Section 3.6.2 — Canonical Name records
- RFC 1035, Section 3.2.1 — Resource-record format and TTL
- RFC 1035, Section 4.1.3 — Resource-record message format