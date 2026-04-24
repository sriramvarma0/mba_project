import json
from typing import Dict, List

import pandas as pd


RULE_CACHE: Dict[frozenset, List[dict]] = {}
LAST_UPDATED = None


def clear_cache():
    RULE_CACHE.clear()


def set_cache(new_cache: Dict[frozenset, List[dict]]):
    RULE_CACHE.clear()
    RULE_CACHE.update(new_cache)


def cache_to_jsonable():
    output = []
    for key, values in RULE_CACHE.items():
        output.append({"antecedent": sorted(list(key)), "recommendations": values})
    return output


def serialize_itemset(itemset):
    return json.dumps(sorted(list(itemset)))


def deserialize_itemset(itemset_str):
    try:
        values = json.loads(itemset_str)
        return frozenset(values)
    except json.JSONDecodeError:
        return frozenset()


def hydrate_analyzer_from_db(db_session, analyzer, active_only=True):
    from models import AssociationRule

    query = db_session.query(AssociationRule)
    if active_only:
        query = query.filter(AssociationRule.is_active.is_(True))

    rows = query.order_by(AssociationRule.lift.desc()).all()
    if not rows:
        analyzer.association_rules_df = pd.DataFrame()
        clear_cache()
        analyzer.rule_cache = RULE_CACHE
        return

    frame = pd.DataFrame(
        [
            {
                "antecedents": set(json.loads(rule.antecedents)),
                "consequents": set(json.loads(rule.consequents)),
                "support": float(rule.support),
                "confidence": float(rule.confidence),
                "lift": float(rule.lift),
            }
            for rule in rows
        ]
    )
    analyzer.association_rules_df = frame
    analyzer.build_in_memory_cache()
