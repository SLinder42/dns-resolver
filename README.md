# DNS Resolver

## Group Information

**Group Number:** 1

**Members:**
- Amirreza Arefi
- Simon Linder

---

## Project Overview

This project implements a DNS resolver from scratch in Python 3 without
using the operating system's resolver or external DNS libraries.

The resolver:

- Builds DNS query packets.
- Sends DNS queries over UDP.
- Parses DNS responses.
- Follows referrals from the root server to the authoritative server.
- Resolves IPv4 (A) records.
- Implements DNS caching (Phase 2).
- Supports CNAME resolution (Phase 3).

---

## Requirements

- Python 3
- Internet connection
- `dig` (for verification)

---

## Running the Resolver

Resolve a domain:

```bash
python3 resolver.py example.com
```

Example output:

```text
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
104.20.23.154
```

---

# Phase 1

## Implementation

The Phase 1 resolver was implemented following the **Implement DNS in a Weekend**
guide.

The resolver performs an iterative lookup by:

1. Encoding the domain name into DNS format.
2. Building a DNS query packet.
3. Sending the query using UDP.
4. Parsing DNS responses.
5. Handling DNS name compression.
6. Following referrals from:
   - Root Server
   - TLD Server
   - Authoritative Server
7. Returning the final A record.

Important functions:

- `build_query()`
- `send_query()`
- `parse_dns_packet()`
- `resolve()`

---

## Test Cases

### Test 1 — example.com

Command

```bash
python3 resolver.py example.com
```

Output

```text
Querying 198.41.0.4 for example.com
Querying 192.41.162.30 for example.com
Querying 108.162.192.162 for example.com
104.20.23.154
```

Verification

```bash
dig example.com A
```

The returned IP matched one of the A records returned by `dig`.

---

### Test 2 — google.com

Command

```bash
python3 resolver.py google.com
```

Verification

```bash
dig google.com A
```

The resolver successfully returned a valid A record.

---

### Test 3 — github.com

Command

```bash
python3 resolver.py github.com
```

Verification

```bash
dig github.com A
```

The resolver successfully returned a valid A record.

---

### Test 4 — Subdomain

Command

```bash
python3 resolver.py www.example.com
```

Verification

```bash
dig www.example.com A
```

The resolver successfully resolved the subdomain.

---

### Test 5 — Multiple A Records

Command

```bash
dig example.com A
```

`dig` returned multiple valid A records.

Our resolver returns one valid A record.

---

### Test 6 — Invalid Domain

Command

```bash
python3 resolver.py this-domain-should-not-exist-12345.com
```

Result

The resolver correctly reported a lookup failure.

---

# Phase 2

## Implementation

Phase 2 adds DNS caching.

The resolver:

- Stores cached DNS records.
- Uses the TTL provided in each DNS record.
- Returns cached records before sending a new network query.
- Re-fetches records after TTL expiration.
- Caches intermediate NS and glue records.

---

## Test Cases

### Cache Hit

*(To be completed after Phase 2 merge.)*

---

### TTL Expiration

*(To be completed after Phase 2 merge.)*

---

### Cached NS/Glue Records

*(To be completed after Phase 2 merge.)*

---

# Phase 3

## Extension: CNAME Resolution

### RFC Gap

The baseline resolver only handled A records.

If a DNS response contained a CNAME record, the resolver did not follow
the alias to the canonical domain.

According to **RFC 1034 Section 3.6.2**, a resolver should continue
resolving the canonical name until it reaches the requested resource
record.

---

## Implementation

The extension:

- Added `TYPE_CNAME = 5`.
- Updated the parser to decode CNAME records.
- Added `get_cname()`.
- Updated `resolve()` so it follows the alias automatically.

The resolver now continues resolving until it reaches the final A record.

---

## Test Cases

### Before Extension

Command

```bash
python3 resolver.py www.reddit.com
```

Output

```text
Querying 198.41.0.4 for www.reddit.com
Querying 192.41.162.30 for www.reddit.com
Querying 205.251.193.122 for www.reddit.com
Querying 198.41.0.4 for b'ns-1029.awsdns-00.org'
AttributeError: 'bytes' object has no attribute 'encode'
```

The baseline resolver failed before reaching the final A record.

---

### After Extension

Command

```bash
python3 resolver.py www.reddit.com
```

Output

```text
Querying 198.41.0.4 for www.reddit.com
Querying 192.41.162.30 for www.reddit.com
Querying 205.251.193.122 for www.reddit.com
Following CNAME: www.reddit.com -> reddit.map.fastly.net
Querying 198.41.0.4 for reddit.map.fastly.net
Querying 192.55.83.30 for reddit.map.fastly.net
Querying 23.235.32.32 for reddit.map.fastly.net
151.101.41.140
```

Verification

```bash
dig www.reddit.com CNAME
```

Output

```text
www.reddit.com. CNAME reddit.map.fastly.net.
```

The resolver detected the same CNAME returned by `dig` and successfully
resolved the canonical domain to the final IP address.

---

## References

- Implement DNS in a Weekend
- RFC 1034 — Domain Names: Concepts and Facilities
- RFC 1035 — Domain Names: Implementation and Specification