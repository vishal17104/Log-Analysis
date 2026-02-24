# Agentic Router – Decision Tree

## Purpose
The agentic router is a central decision-making component responsible for determining how an incident should be resolved.  
It routes incidents to either a deterministic runbook-based solution or an AI-generated recommendation, ensuring predictable behavior while enabling intelligent fallback.

The router **does not execute fixes** and **does not create incidents**. It only decides *which source of intelligence to use* for resolution guidance.

---

## Inputs to the Router
The router operates on an already-created incident and uses the following inputs:

- `incident_id`
- `service_name`
- `error_type`
- `severity`
- `incident_metadata` (timestamps, counts, tags)
- `ai_analysis` (optional, precomputed during incident creation)

---

## Decision Flow

1. Receive an `incident_id`
2. Fetch full incident details from the incident service
3. Extract routing signals:
   - service name
   - error type
4. Query the runbook system using `(service_name, error_type)`
5. Decision:
   - If a matching runbook exists:
     - Select runbook-based solution
     - Mark resolution source as **runbook**
   - Else:
     - Request AI-generated recommendation
     - Mark resolution source as **ai**
6. Return a unified resolution response

---

## Deterministic vs AI Boundary

- Runbooks always take priority over AI recommendations
- AI is used strictly as a fallback mechanism
- The router never merges runbook and AI outputs
- The router does not execute actions or apply fixes
- The router only returns **guidance and context**

This ensures predictable and auditable behavior.

---

## Output Structure (Conceptual)

The router returns a unified response containing:

- `incident_id`
- `resolution_source` (`runbook` or `ai`)
- `solution_text`
- `confidence` (optional)
- `metadata` (runbook path or AI prompt reference)

---

## Extensibility Considerations

The agentic router is designed to support future extensions without architectural changes, including:

- Severity-based routing
- Confidence scoring
- Auto-remediation agents
- Human-in-the-loop approval
- Multiple AI providers
- Policy-based routing logic

These extensions will be layered on top of the existing decision flow.

---

## Design Principles

- Deterministic-first routing
- Explicit fallback to AI
- Clear separation of concerns
- Service-based backend design
- No hidden side effects
- Minimal and extensible logic