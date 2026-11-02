# Phase 4A.2 — installed expression API contract

**The existing exported classifier cannot safely satisfy this assignment's full
contract. No LLM bridge was installed or added to the adapter.** The authorized
blocker path is retained: provider preferences stay unchanged, and the existing RP
adapter uses neutral fallback. This is not a claim that ST itself cannot classify
with an LLM; its export lacks the result/error/identity contract needed here.

Inspected local ST `8172dcd0ee672d3cd9a5e5f7af134f91a45cd2b8` (1.18.0),
Extension-Live2d `d1801d36a32ace9451cf6377c005a7a64292fc39` (0.1.0).
`public/scripts/extensions/expressions/index.js` SHA-256:
`42ef6cf85ee459d821eda3b10c9b589bccfbb2946bb743c3f5137a614836609c`.
No private chats, credentials, production HTTP sessions or actual LLM calls were
needed. Provider `expressions.api=2` was reconfirmed through the audit's restricted
settings projection; prompt/model/credential settings were not read.

## Observed contract, not an assumed stable API

At line 1041, `getExpressionLabel(text, expressionsApi=..., options={})` is an
export returning `Promise<string?>`. It delegates to ST's existing generation
functions. Reusing it would avoid a second independent classifier, but:

- LLM connection failures and caught generation/parsing failures return the user's
  configured fallback label. A valid classification of that same emotion returns
  exactly the same value. There is no typed error/result or success flag. We cannot
  keep valid joy classifications and guarantee neutral on errors by wrapping this
  export alone. Temporarily changing the global fallback would violate preferences
  and introduce races with ST's own expression worker.
- `promptType=raw` passes sampled message text to `generateRaw`. `promptType=full`
  calls `generateQuietPrompt({quietPrompt: prompt})`, with no supplied text argument;
  it uses the application's generation context. Switching modes would alter user
  preferences. The export is not a pure message-in/label-out service.
- `filterAvailable` defaults to the user's setting and can restrict labels to sprite
  files, not Live2D expressions. `getExpressionsList` at line 1397 consults the sprite
  cache. An override needs explicit semantics rather than assuming the seven Live2D
  assets are available as sprites.
- The module worker at lines 549–609 manages its own `inApiCall`, streaming timing
  and `lastMessage`. Direct export callers do not participate in a shared in-flight
  request cache. Two identical calls generate two requests. The module's shared
  boolean is not a general concurrency lock.
- **There is an exported `lastExpression` object** (line 104), updated by
  `sendExpressionCall` at line 653. It is keyed by sprite folder/character name,
  contains only a label, and also accepts manual/slash-command changes. It has no
  message ID, generation token, provider, success status or completion timestamp.
  Reusing it after a new reply could apply the previous reply's or a manual emotion.
  Polling this object or watching sprite DOM changes cannot establish freshness.
- No classification-result event with message identity was found in this revision.
  No cancellation signal is accepted by the export. Live2D's existing generation/
  request guards can discard late application, but cannot eliminate duplicate
  requests already made by the independent sprite worker.
- Local HTTP failure returns `undefined`; thrown errors and unknown LLM output can
  return the configured fallback. A wrapper would need to distinguish these cases
  without global fetch interception or changes to preferences.

A direct import would therefore solve only the basic happy path. We did not patch
`expressions/index.js`, override global fetch in shipped code, intercept toasts,
replace event listeners, read private module variables, or force provider settings.
The existing optional adapter and its pinned hashes are unchanged.

## Validation and limits

`node scripts/audit_st_expression_contract.mjs <installed-expressions-index.js>`
verifies the exact source hash, extracts the actual exported function and executes
it in a Node VM with synthetic dependencies. It confirms seven deterministic
simulated LLM labels, local-label success, local HTTP failure, unknown-label
fallback, indistinguishable LLM success/error values, two requests for identical
calls, and omission of supplied text in full-prompt mode. Generation and parsing
dependencies are mocks; this is an API-contract experiment, **not full ST generation
or real LLM inference**. Evidence: `runs/phase4a2-audit/classifier-contract.json`.

Actual Btrfs-hosted ST browser scenarios use real `MESSAGE_RECEIVED` handlers and
render the accepted Girl2. With provider 0 and mocked classification responses,
all seven mapped expressions pass; failure, delayed older reply, switching, reload,
talking, idle and blink tests pass with the optional adapter. With provider 2
preserved, an attempted synthetic anger label results in **zero classifier requests**:
upstream displays happy (joy fallback), adapter displays neutral. This verifies the
known limitation rather than claiming an LLM-to-render integration.

| Gate | Result |
| --- | --- |
| Simulated labels through exact built-in exported function | Seven labels returned; dependencies mocked |
| Mocked supported local provider → actual events → rendered expressions | Pass |
| Real LLM inference or private-chat classification | Not attempted, not authorized |
| LLM provider → Live2D emotion integration | Blocked, no bridge shipped |
| Reliable shared result reuse/deduplication | Unavailable in inspected export contract |
| Provider-2 preserved fallback with no new requests | Pass: upstream happy, adapter neutral |
| Audio lip synchronization | Not implemented |

## Next viable design

A maintainable solution needs a reviewed ST-side result service/event carrying
message/chat identity, provider, a success/error discriminator and a shared
in-flight/result cache. The existing sprite worker and Live2D should consume that
single result, with request-generation guards on both. This could be an upstream
API addition or an explicitly scoped, version-pinned built-in extension change;
it is materially broader than the current two-file RP adapter. It must preserve
full/raw prompt semantics, filtering and preferences, isolate context changes, and
be tested with synthetic data before any separately authorized API calls.

Do not silently change the global provider to local as a workaround. A later
production decision may accept neutral/manual expressions while provider 2 remains,
or authorize this broader integration work. Actual API/model calls remain a
separate authorization regardless of the choice.
