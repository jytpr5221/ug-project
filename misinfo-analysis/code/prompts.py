"""Prompts for the POC v1 batch evaluation (300 claims per API call).

Design notes
------------
* ONE API call receives a numbered list of up to 300 claims and must return
  exactly one line per claim: ``<number>: <LABEL>, <SEVERITY>``. The runner
  parses the ids back onto the claims (parsing.parse_batch_response).
* Only the raw claim text is inserted - no justification, no evidence.
* Label space: TRUE / FALSE / NEI, where
  - FALSE (misinformation): false, fabricated, or misleading about money,
    markets, companies, government finances, or personal finance, such that
    someone who believed it could make a harmful financial decision;
  - TRUE: factually accurate or a defensible financial/economic statement;
  - NEI: the claim is NOT RELATED TO FINANCIAL MATTERS (project definition).
* Severity HIGH/MEDIUM/LOW mirrors the ground-truth severity semantics in
  misinfo-analysis/datasets/finfact_training_schema.json (high = substantial
  loss/fraud/insolvency; medium = decision/market/public-finance stakes with
  bounded loss; low = general topic, no direct substantial loss).
"""

SYSTEM_PROMPT = (
    "You are a careful financial fact-checking assistant. You receive a "
    "numbered list of claims and must answer with exactly one line per claim "
    "in the requested format, and nothing else."
)

BATCH_PROMPT_TEMPLATE = """You will receive {n} numbered claims. For EACH claim, using ONLY the claim text, produce two judgements.

TASK 1 - Claim judgement:
- TRUE: the claim is factually accurate, or a defensible statement about financial or economic matters.
- FALSE (misinformation): the claim is false, fabricated, or misleading about money, markets, companies, government finances, or personal finance, such that someone who believed it could make a harmful financial decision or suffer financial harm.
- NEI: the claim is not related to financial matters (it does not involve money, markets, companies, government finances, or personal finance).

TASK 2 - Severity rating. Rate how serious the claim's subject matter is: the financial stakes if the claim were believed and acted upon. This is independent of your TASK 1 answer (a TRUE claim can still be HIGH).
- HIGH: potentially substantial financial loss, fraud, scam, insolvency, theft of funds, or disruption to personal or institutional financial security (for example a scam that could drain savings, or a false bankruptcy story).
- MEDIUM: concerns a financial decision, obligation, market, or public-finance issue that could influence monetary decisions, but with bounded or indirect losses (for example a wrong growth-rate, tax-rate, or budget figure that misleads expectations).
- LOW: a general financial or economic topic without a clear indicator of direct, substantial individual or institutional loss (for example economic trivia, historical curiosities, or non-financial claims).

OUTPUT FORMAT - exactly one line per claim, nothing else. Always give both values for every claim:
<number>: <TRUE|FALSE|NEI>, <HIGH|MEDIUM|LOW>
Example output for 2 claims:
1: FALSE, HIGH
2: NEI, LOW

Claims:
{claims_block}"""


def build_batch_prompt(claims: list[str]) -> str:
    """Render the numbered claim block and insert it into the template."""
    block = "\n".join(
        f"{i}. {claim.replace(chr(10), ' ').strip()}" for i, claim in enumerate(claims, 1)
    )
    return (
        BATCH_PROMPT_TEMPLATE
        .replace("{n}", str(len(claims)))
        .replace("{claims_block}", block)
    )
