# Stage 3 - Drafting

> Last Updated: 2026-04-15

Drafting is where the platform starts producing target artifacts.

Its job is to:

- choose the target/layer strategy
- assemble agent prompt plus cartridge prompt plus optional custom instructions
- generate code or target artifacts
- validate the result
- review it through the critic/governance chain

This stage is where `direct` versus modernization-oriented outputs becomes especially important.

Current direct-mode runtime expectations:

- strict no-hardcode behavior for dynamic object resolution (table/schema/catalog/path)
- code must remain executable and metadata-driven
- critic scoring is mode-aware and can defer non-structural redesign objections to refinement

Drafting is also the first valid delivery-grade baseline. A project may stop after Drafting and move directly into later review and delivery flows if faithful migration is sufficient for the business case.

That means Drafting is not automatically a transitional state. It is the point where the user should be able to decide whether to:

- deliver the Drafting output as-is
- continue into a structured medallion-style refinement
- continue into a deeper project-level reengineering path
