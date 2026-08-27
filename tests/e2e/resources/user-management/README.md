# User Management Test Project

E2E test fixture for graphify — a user management scenario with authentication, profile management, and domain events.

## Structure

```
src/
├── models/user.ts              — User aggregate root + Profile value object
├── repositories/user.repository.ts — User repository (data access)
├── services/user.service.ts    — User service (CRUD operations)
├── auth/
│   ├── password.ts             — Password hashing utility
│   ├── jwt.ts                  — JWT token management
│   ├── auth.service.ts         — Authentication service (register, login, refresh)
│   └── auth.controller.ts      — HTTP controller for auth endpoints
├── middleware/auth.middleware.ts — JWT authentication middleware
├── utils/logger.ts             — Structured logging utility
├── config.ts                   — Application configuration + DI wiring
└── index.ts                    — Entry point (exports)

docs/
├── context-map.md              — Business boundary map
├── technical-constraints.md    — Technical constraints
└── features/user-management/   — BC-level DDD documents
    ├── index.md
    ├── business-flow.md
    ├── domain-model.md
    ├── contracts.md
    ├── invariants.md
    └── domain-events.md
```

## Bounded Contexts

- **User Management (BC-01)** — core domain: user identity, profile, lifecycle
- **Authentication (BC-02)** — supporting domain: registration, login, token management

## Purpose

This project is a **deterministic test fixture** for the Understand-Anything CLI (`understand.mjs`). Run `/understand` on this project to generate the knowledge graph, then run `/understand-ddd` to merge DDD doc-anchor nodes. The resulting `.graph/knowledge-graph.json` is committed and used by E2E tests.
