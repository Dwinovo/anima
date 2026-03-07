# Event Verb Domain Filter Design

**Goal:** Add an optional `verb_domain` filter to `GET /api/v1/sessions/{session_id}/events` so clients can page through a single verb namespace such as `social.*`.

## Scope

- Add an optional query parameter `verb_domain`.
- Match events whose `verb` starts with `<verb_domain>.`.
- Keep existing pagination behavior and response shape unchanged.
- Return an empty page instead of an error when no events match.

## Contract

- Parameter: `verb_domain`
- Example: `GET /api/v1/sessions/{session_id}/events?verb_domain=social&limit=20`
- Validation: `verb_domain` must contain only the namespace part and match `^[a-z][a-z0-9_]*$`.
- Pagination semantics: filtering happens before pagination; `cursor` continues to paginate within the filtered result set.

## Implementation Notes

- Extend `EventListQuery` validation to accept `verb_domain`.
- Thread `verb_domain` through the router, use case, repository protocol, and Neo4j implementation.
- Apply the filter in the Neo4j recent-event query with a prefix match against `verb`.

## Testing

- Request schema validation accepts valid `verb_domain` values and rejects invalid values.
- Event listing use case forwards `verb_domain` to the graph repository.
- Neo4j query text includes the prefix filter clause.
