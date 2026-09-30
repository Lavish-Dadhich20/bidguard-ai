"""Tests the Supabase provider with a fake client (no network needed) and
checks it gives identical results to the JSON data."""
import json, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.providers import SupabaseProvider
from engine.compliance_engine import evaluate_bidder

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
load = lambda f: json.load(open(os.path.join(DATA, f), encoding="utf-8"))


class FakeQuery:
    def __init__(self, gov, table): self.gov, self.table, self.f = gov, table, {}; self.in_vals = None
    def select(self, *_): return self
    def eq(self, k, v): self.f[k] = v; return self
    def in_(self, k, vals): self.in_vals = vals; return self
    def limit(self, _): return self
    def execute(self):
        class R: pass
        r = R()
        if self.table == "blacklist":
            bl = {x.strip().upper() for x in self.gov["BLACKLIST"]}
            r.data = [{"identifier": v} for v in self.in_vals if v in bl]
        else:
            rec = self.gov.get(self.f["source"], {}).get(self.f["identifier"])
            r.data = [{"data": rec}] if rec else []
        return r


class FakeClient:
    def __init__(self, gov): self.gov = gov
    def table(self, name): return FakeQuery(self.gov, name)


class TestSupabaseProvider(unittest.TestCase):
    def test_results_identical_to_json(self):
        tender, gov, bidders = load("tender_requirements.json"), load("government_records.json"), load("bidders.json")
        provider = SupabaseProvider(FakeClient(gov))
        for b in bidders:
            self.assertEqual(evaluate_bidder(b, tender, gov), evaluate_bidder(b, tender, provider))


if __name__ == "__main__":
    unittest.main()
