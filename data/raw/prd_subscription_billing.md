# PRD: Subscription Plan Changes & Proration

**Author:** Priya Nair, Product Manager, Billing Platform
**Status:** Approved for development
**Target release:** Q3, Sprint 14-16
**Stakeholders:** Billing Eng, Growth, Finance, Support

## 1. Background & problem statement

Today, customers on our SaaS platform can only change subscription plans by
contacting support, who manually issue credits and adjust billing in Stripe.
This creates a 2-3 day turnaround, generates ~140 support tickets/month, and
is a top-5 driver of customer churn during the trial-to-paid conversion window
(per Q1 churn survey, 22% of churned self-serve customers cited "wanted to
downgrade but it was too much hassle").

We are building self-serve plan changes: upgrades, downgrades, and billing
cycle changes (monthly <-> annual), with automatic proration.

## 2. Goals

- Allow customers to change plans without contacting support.
- Correctly prorate charges and credits for mid-cycle changes.
- Reduce billing-related support tickets by 60% within one quarter of launch.
- Maintain PCI compliance and existing fraud-prevention checks.

## 3. Non-goals

- This PRD does not cover cancellations (see PRD-2201, "Self-serve cancellation").
- This PRD does not cover team/seat-based pricing changes (see PRD-2214).
- Enterprise (custom contract) accounts are explicitly out of scope; they will
  continue to go through their account manager.

## 4. User personas

- **Self-serve Sam**: individual user on the Starter or Pro plan, pays by
  credit card, wants to upgrade because they hit a usage limit.
- **Budget-conscious Bea**: on Pro plan, wants to downgrade to Starter because
  she's using fewer features than expected, price-sensitive.
- **Annual Andre**: paying annually, wants to switch to monthly billing for
  cash-flow reasons.

## 5. Functional requirements

### FR1: Plan change entry point
Add a "Change plan" button to Account Settings > Billing. Visible to all
self-serve customers (Starter, Pro, Business tiers). Not visible to Enterprise
accounts (see Non-goals).

### FR2: Plan comparison view
Clicking "Change plan" opens a modal showing all available plans side by side,
with the customer's current plan highlighted. Each plan shows monthly and
annual pricing, and a feature comparison table.

### FR3: Upgrade flow (immediate effect)
When a customer upgrades (e.g. Starter -> Pro), the new plan takes effect
immediately. The customer is charged a prorated amount for the remainder of
the current billing cycle at the new plan's rate, calculated as:

`prorated_charge = (new_plan_price - old_plan_price) * (days_remaining_in_cycle / total_days_in_cycle)`

The customer's next full-price invoice occurs at the original billing date,
unchanged.

### FR4: Downgrade flow (deferred effect)
When a customer downgrades (e.g. Pro -> Starter), the change does NOT take
effect immediately. The customer keeps current-plan access until the end of
the current billing cycle, and the new (lower) plan begins at the next
billing date. No credit is issued for a downgrade — this avoids customers
gaming short-term downgrade/upgrade cycles for credits.

### FR5: Billing cycle change (monthly <-> annual)
Switching from monthly to annual: charge the annual rate immediately,
prorated by crediting the unused portion of the current monthly cycle against
the annual charge. Switching from annual to monthly: NOT allowed mid-cycle;
the customer must wait until their annual renewal date, at which point they
can select monthly billing before the renewal charge fires.

### FR6: Payment failure during upgrade
If the prorated upgrade charge fails (card declined, insufficient funds), the
plan change does not take effect. The customer remains on their original
plan. Show an inline error with the decline reason (if provided by the
payment processor) and a link to update payment method.

### FR7: Confirmation & receipts
After any successful plan change, send a transactional email confirming the
new plan, the effective date, and the prorated amount charged or credited (if
any). Also show a confirmation screen in-app with the same details.

### FR8: Plan change history
Add a "Billing history" section showing all past plan changes with date,
old plan, new plan, and amount charged/credited. Retained indefinitely.

### FR9: Mid-trial upgrades
Customers still in their 14-day free trial can upgrade their trial to a
higher tier at no charge (trial remains free); the trial simply reflects the
new tier's features and limits for the remainder of the trial period.

### FR10: Grandfathered pricing protection
Customers on legacy/grandfathered pricing plans (no longer sold publicly)
who choose to change plans permanently lose grandfathered pricing and move
to current published rates. Show a clear warning before confirming this
specific case, since it is irreversible.

## 6. Non-functional requirements

### NFR1: Idempotency
Plan change requests must be idempotent. If a customer double-clicks
"Confirm" or a network retry occurs, the customer must not be charged twice
or have the plan changed twice.

### NFR2: Consistency with payment processor
The plan change must be reflected in our database and the Stripe subscription
object atomically from the customer's point of view — if the Stripe API call
succeeds but our database write fails, we must reconcile (via webhook retry)
rather than leave the account in an inconsistent state.

### NFR3: Performance
The plan comparison modal must load in under 500ms at p95.

### NFR4: Auditability
Every plan change must be logged with: customer ID, old plan, new plan,
timestamp, prorated amount, actor (customer self-serve vs. support-initiated),
and payment processor transaction ID, for Finance reconciliation.

## 7. Edge cases to handle

- Customer attempts to "upgrade" to a plan that is actually cheaper (plan
  catalog misconfiguration) — system should treat by price comparison, not
  by plan name/tier label, to decide upgrade vs. downgrade logic.
- Customer's current billing cycle has fewer than 24 hours remaining when
  they attempt an upgrade — proration should still calculate correctly even
  for very small `days_remaining_in_cycle` values, including zero.
- Customer attempts to change plans while a previous plan-change request for
  the same account is still processing (race condition).
- Customer's card is valid but the prorated charge amount is $0.00 (e.g.
  upgrading on literally the last day of the cycle with old_plan_price ==
  new_plan_price minus rounding) — should this still count as a valid plan
  change, and should a confirmation email still send?
- Currency mismatch: customer's account currency differs from a promotional
  plan priced only in USD.
- Customer downgrades, then upgrades again before the downgrade has taken
  effect at cycle end — the pending downgrade should be cancelled, not
  stacked.
- Proration calculation when a coupon/discount code is active on the
  account.

## 8. Acceptance criteria

- [ ] Self-serve customers on Starter, Pro, and Business can upgrade or
      downgrade without contacting support.
- [ ] Upgrades apply immediately with correct proration; downgrades apply at
      next billing cycle with no credit issued.
- [ ] Failed payment on upgrade leaves the customer on their original plan
      with no partial state change.
- [ ] All plan changes are logged per NFR4 and visible in Billing history.
- [ ] Grandfathered-pricing customers see an explicit irreversibility warning.
- [ ] No double-charging occurs under retry/double-click conditions (NFR1).

## 9. Open questions

- Should annual-to-monthly be allowed mid-cycle for Business tier customers
  specifically, given their higher LTV? Growth wants this; Finance is
  concerned about revenue recognition complexity. Decision needed by Sprint
  14 planning.
- Do we need a cooldown period between plan changes (e.g. max one change per
  24 hours) to prevent abuse? Support has not seen this as a problem in the
  manual process, but self-serve removes the friction that implicitly limited
  it.

## 10. Rollout plan

Phase 1 (Sprint 14): Upgrades only, Starter/Pro tiers, feature-flagged to 5%
of accounts. Phase 2 (Sprint 15): Downgrades + Business tier. Phase 3
(Sprint 16): Billing cycle changes, full rollout.
