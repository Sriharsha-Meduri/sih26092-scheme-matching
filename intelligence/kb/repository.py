"""Typed, read-only repository over the M1 normalized KB.

Consumers (eligibility, matching, financial, ranking) never touch raw file
shapes directly; they go through here. Everything the repository returns is the
M1 normalized record (dict), indexed where a speed/typing win exists.

The repository is immutable after construction (lazily built on first use) and
deterministic: the same KB directory always yields the same repository.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from intelligence.kb.adapters import (
    active_scheme_scope,
    evaluate_formula,
    normalize_key,
    resolve_conditional,
)
from intelligence.kb.loader import KBIntegrityError, find_kb_dir, load_normalized


class KnowledgeBase:
    def __init__(self, kb_dir: Optional[Path] = None) -> None:
        self._kb_dir = Path(kb_dir) if kb_dir else find_kb_dir()
        if self._kb_dir is None:
            raise KBIntegrityError(
                "KB/normalized not found. Set SIH26092_KB_DIR or run from the repo root."
            )
        self._data = load_normalized(self._kb_dir)
        self._scheme_order: list[str] = []
        self._schemes: dict[str, dict] = {}
        self._scheme_names: dict[str, str] = {}
        self._rules: dict[str, dict] = {}
        self._fps_by_id: dict[str, dict] = {}
        self._fps_by_scheme: dict[str, list[dict]] = {}
        self._activities: dict[str, dict] = {}
        self._activities_by_key: dict[str, dict] = {}
        self._sectors: dict[str, dict] = {}
        self._sources: dict[str, dict] = {}
        self._families: dict[str, dict] = {}
        self._families_by_key: dict[str, dict] = {}
        self._activity_mappings: list[dict] = []
        self._sector_mappings: list[dict] = []
        self._build()

    # ------------------------------------------------------------------ init
    def _build(self) -> None:
        for rec in self._schemes_records():
            sid = rec["id"]
            self._schemes[sid] = rec
            self._scheme_order.append(sid)
            name = rec.get("scheme_name") or sid
            short = rec.get("short_name") or sid
            self._scheme_names[sid] = f"{name}"
            self._scheme_names[f"{sid}:short"] = short

        for rec in self._data["eligibility_rules"]["records"]:
            self._rules[rec["id"]] = rec

        for rec in self._data["financial_parameters"]["records"]:
            fp = dict(rec)
            self._fps_by_id[fp["id"]] = fp
            self._fps_by_scheme.setdefault(fp["scheme_id"], []).append(fp)

        for rec in self._data["activities"]["records"]:
            act = dict(rec)
            self._activities[act["id"]] = act
            self._activities_by_key[normalize_key(act["name"])] = act
            self._activities_by_key[normalize_key(act.get("source_name") or "")] = act
            for alias in act.get("aliases") or []:
                self._activities_by_key[normalize_key(alias)] = act

        for rec in self._data["sectors"]["records"]:
            self._sectors[rec["id"]] = rec

        for rec in self._data["sources"]["records"]:
            self._sources[rec["id"]] = rec

        mappings = self._data["activity_scheme_mappings"]
        self._activity_mappings = mappings.get("activity_mappings") or []
        self._sector_mappings = mappings.get("sector_mappings") or []

        edu = self._data["education"]
        self.education = edu
        for fam in edu.get("course_families") or []:
            self._families[fam["id"]] = fam
            self._families_by_key[normalize_key(fam["family"])] = fam
            self._families_by_key[normalize_key(fam.get("raw_text") or "")] = fam
            for level in fam.get("levels") or []:
                self._families_by_key.setdefault(normalize_key(level), fam)

        self._group_scheme_ids = {"income_generating": [
            sid for sid in self._scheme_order
            if self._schemes[sid].get("education", {}).get("is_education_scheme") is not True
        ]}

    def _schemes_records(self) -> list[dict]:
        return self._data["schemes"]["records"]

    # --------------------------------------------------------------- schemes
    @property
    def kb_dir(self) -> Path:
        return self._kb_dir

    @property
    def index(self) -> dict[str, Any]:
        return self._data["index"]

    @property
    def kb_version(self) -> Optional[str]:
        return self.index.get("kb_version")

    @property
    def schema_version(self) -> Optional[str]:
        return self.index.get("schema_version")

    @property
    def generated_on(self) -> Optional[str]:
        return self.index.get("generated_on")

    @property
    def scheme_ids(self) -> list[str]:
        return list(self._scheme_order)

    def scheme(self, scheme_id: str) -> Optional[dict]:
        return self._schemes.get(scheme_id)

    def scheme_name(self, scheme_id: str) -> str:
        rec = self._schemes.get(scheme_id)
        return rec["scheme_name"] if rec else scheme_id

    def all_schemes(self) -> list[dict]:
        return [self._schemes[sid] for sid in self._scheme_order]

    # ---------------------------------------------------------------- rules
    def rule(self, rule_id: str) -> Optional[dict]:
        return self._rules.get(rule_id)

    def rules_for_scheme(self, scheme_id: str) -> list[dict]:
        """Rules applicable to a scheme, in KB order (M2 §8 scope handling).

        EXTERNAL_DOMAIN rules (E007) are never applied to loan eligibility.
        """
        applicable: list[dict] = []
        for rule in self._rules.values():
            scope = rule.get("scope") or {}
            if scheme_id in active_scheme_scope(
                scope, self._scheme_order, self._group_scheme_ids
            ):
                applicable.append(rule)
        return applicable

    # ---------------------------------------------------------- financials
    def fp(self, scheme_id: str, parameter: str) -> Optional[dict]:
        for fp in self._fps_by_scheme.get(scheme_id, []):
            if fp["parameter"] == parameter:
                return fp
        return None

    def financial_parameters(self, scheme_id: str) -> list[dict]:
        return list(self._fps_by_scheme.get(scheme_id, []))

    # ------------------------------------------------------------ activities
    def activity(self, activity_id: str) -> Optional[dict]:
        return self._activities.get(activity_id)

    def resolve_activity_name(self, name: str) -> Optional[dict]:
        """Resolve raw text to a canonical activity record (case-insensitive, alias-aware)."""
        key = normalize_key(name)
        return self._activities_by_key.get(key)

    def all_activities(self) -> list[dict]:
        return list(self._activities.values())

    def sector(self, sector_id: str) -> Optional[dict]:
        return self._sectors.get(sector_id)

    def activity_scheme_ids(self, activity_id: str) -> list[str]:
        for m in self._activity_mappings:
            if m["activity_id"] == activity_id:
                return list(m.get("scheme_ids") or [])
        return []

    def activity_mapping(self, activity_id: str) -> Optional[dict]:
        for m in self._activity_mappings:
            if m["activity_id"] == activity_id:
                return m
        return None

    def sector_mapping(self, sector_id: str) -> Optional[dict]:
        for m in self._sector_mappings:
            if m["sector_id"] == sector_id:
                return m
        return None

    # -------------------------------------------------------------- education
    @property
    def course_families(self) -> list[dict]:
        return self.education.get("course_families") or []

    def family(self, family_id: str) -> Optional[dict]:
        return self._families.get(family_id)

    def resolve_course(self, text: str) -> Optional[dict]:
        """Resolve course/family text to a listed course family (levels/raw text)."""
        return self._families_by_key.get(normalize_key(text))

    # --------------------------------------------------------------- sources
    def source(self, source_id: str) -> Optional[dict]:
        return self._sources.get(source_id)

    def source_title(self, source_id: str) -> str:
        rec = self._sources.get(source_id)
        return rec["title"] if rec else source_id

    def source_url(self, source_id: str) -> Optional[str]:
        rec = self._sources.get(source_id)
        return rec.get("url") if rec else None

    # ------------------------------------------------------------- conditionals
    def resolve_conditional(self, value: Any, context: dict[str, Any]) -> tuple[Any, bool]:
        return resolve_conditional(value, context)

    def evaluate_formula(self, value: Any, context: dict[str, Any]) -> tuple[Any, Optional[str]]:
        return evaluate_formula(value, context)