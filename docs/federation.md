# Independent federation model

The Atlas is a replaceable catalogue, never a mandatory control plane.

- Each node controls its own namespace, keys, records, and publication decisions.
- Consumers can pin trust roots and fetch manifests directly.
- Multiple indexes may mirror or curate public records.
- Records should identify issuer, version, timestamp, digest, and retrieval source.
- Key rotation and revocation must be explicit; stale records detectable.
- Export and re-import must not depend on the original operator.

This is a design constraint, not a claim that federation, signatures, or synchronization currently work.