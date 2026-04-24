from datetime import datetime

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth

from rule_cache import RULE_CACHE, set_cache


class EcommerceBasketAnalyzer:
    def __init__(self, min_support=0.01, min_confidence=0.2):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.raw_transactions = pd.DataFrame()
        self.frequent_itemsets = pd.DataFrame()
        self.association_rules_df = pd.DataFrame()
        self.rule_cache = RULE_CACHE
        self.last_updated = None

    def ingest_batch_data(self, data: list):
        # data = [{"session_id": 1, "item_id": "SKU-001", "qty": 1}, ...]
        # Build basket matrix (session x item), boolean encode, store in self.raw_transactions
        if not data:
            self.raw_transactions = pd.DataFrame()
            return

        frame = pd.DataFrame(data)
        if frame.empty:
            self.raw_transactions = pd.DataFrame()
            return

        pivot = frame.pivot_table(
            index="session_id",
            columns="item_id",
            values="qty",
            aggfunc="sum",
            fill_value=0,
        )
        self.raw_transactions = pivot.gt(0)

    def execute_mining_pipeline(self):
        # Run fpgrowth() -> association_rules() from mlxtend
        # Sort by lift descending
        # Call build_in_memory_cache()
        if self.raw_transactions.empty:
            self.frequent_itemsets = pd.DataFrame()
            self.association_rules_df = pd.DataFrame()
            self.rule_cache.clear()
            return

        self.frequent_itemsets = fpgrowth(
            self.raw_transactions,
            min_support=self.min_support,
            use_colnames=True,
        )

        if self.frequent_itemsets.empty:
            self.association_rules_df = pd.DataFrame()
            self.rule_cache.clear()
            return

        rules = association_rules(self.frequent_itemsets, metric="confidence", min_threshold=self.min_confidence)
        if rules.empty:
            self.association_rules_df = pd.DataFrame()
            self.rule_cache.clear()
            return

        rules = rules[["antecedents", "consequents", "support", "confidence", "lift"]]
        rules = rules.sort_values(by="lift", ascending=False).reset_index(drop=True)
        self.association_rules_df = rules
        self.build_in_memory_cache()
        self.last_updated = datetime.utcnow()

    def build_in_memory_cache(self):
        # Convert rules DataFrame to dict keyed by frozenset(antecedents)
        new_cache = {}
        if self.association_rules_df.empty:
            set_cache(new_cache)
            return

        for _, row in self.association_rules_df.iterrows():
            antecedent_key = frozenset(row["antecedents"])
            consequents = row["consequents"]

            bucket = new_cache.setdefault(antecedent_key, [])
            for item in consequents:
                bucket.append(
                    {
                        "recommended_item": item,
                        "confidence": float(row["confidence"]),
                        "lift": float(row["lift"]),
                        "support": float(row["support"]),
                    }
                )

        for key in new_cache:
            dedup = {}
            for candidate in new_cache[key]:
                existing = dedup.get(candidate["recommended_item"])
                if not existing or candidate["lift"] > existing["lift"]:
                    dedup[candidate["recommended_item"]] = candidate
            new_cache[key] = sorted(dedup.values(), key=lambda x: x["lift"], reverse=True)

        set_cache(new_cache)
        self.rule_cache = RULE_CACHE

    def get_realtime_recommendations(self, active_cart: list, top_n=3):
        # Find all rules where antecedent subseteq cart
        # Filter out items already in cart
        # Return top_n sorted by lift
        cart_set = set(active_cart)
        candidates = {}

        for antecedent, recommendations in self.rule_cache.items():
            if antecedent.issubset(cart_set):
                for rec in recommendations:
                    if rec["recommended_item"] in cart_set:
                        continue
                    existing = candidates.get(rec["recommended_item"])
                    if not existing or rec["lift"] > existing["lift"]:
                        candidates[rec["recommended_item"]] = rec

        ranked = sorted(candidates.values(), key=lambda x: (x["lift"], x["confidence"]), reverse=True)
        return ranked[:top_n]

    def trigger_dynamic_discount(self, active_cart: list):
        # If cart matches antecedent with confidence > 0.80 but lacks consequent
        # Return promo code like "BUNDLE-SKU-001-10OFF"
        cart_set = set(active_cart)

        best_candidate = None
        for antecedent, recommendations in self.rule_cache.items():
            if not antecedent.issubset(cart_set):
                continue

            for rec in recommendations:
                if rec["confidence"] <= 0.80:
                    continue
                if rec["recommended_item"] in cart_set:
                    continue
                if not best_candidate or rec["confidence"] > best_candidate["confidence"]:
                    best_candidate = rec

        if not best_candidate:
            return None

        return f"BUNDLE-{best_candidate['recommended_item']}-10OFF"
