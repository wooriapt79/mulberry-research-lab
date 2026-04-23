# Mulberry Image Endpoint Spec v0.1

## Objective
Turn a brand image, logo, or banner into a trusted endpoint for agent execution.

## Input Modes
1. Logo / CI / BI
2. Banner text
3. Hybrid (logo + natural language)

## Pipeline
1. Extract visual / textual signal
2. Resolve brand identity
3. Infer natural-language intent
4. Check capability allowlist
5. Map to agent and functions
6. Execute via adapter / endpoint

## Safety
- brand allowlist
- intent allowlist
- text confidence threshold
- endpoint logging
- fallback defaults

## Example Mapping
- 공동구매 → `groupbuy.start`
- 보험 청구 도움 → `insurance.claim_help`
- 배포 준비 → `deploy.setup`