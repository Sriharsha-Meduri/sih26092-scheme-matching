"""Clearly labelled prototype seed data.

Everything here is a development placeholder. The five schemes are the ones the
PRD names, but their numeric terms are NOT official NSFDC figures and must not
be presented as such. Every row points at a source of type prototype_mock with
a note saying exactly that. Developer 1 replaces this with verified data
loaded into the same tables; no application code changes.

Partners use generic names on purpose so no real institution is implied to be
authorised for anything."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Activity,
    ApplicationRequirement,
    EligibilityRule,
    ElsCourse,
    Partner,
    PartnerPerformance,
    Scheme,
    SchemePartnerMapping,
    Source,
)

PROTOTYPE_SOURCE_TITLE = "Prototype placeholder data"
PROTOTYPE_NOTE = (
    "Placeholder values for development and testing. Not official NSFDC figures. "
    "Replace with verified data from the scheme master."
)


def seed_prototype_data(db: Session) -> dict:
    """Idempotent: does nothing if any scheme already exists."""
    if db.scalar(select(Scheme.id).limit(1)) is not None:
        return {"skipped": True, "reason": "schemes already present"}

    src = Source(
        title=PROTOTYPE_SOURCE_TITLE,
        source_type="prototype_mock",
        version="prototype",
        notes=PROTOTYPE_NOTE,
    )
    db.add(src)
    db.flush()

    common = dict(
        financing_percentage=90,
        target_group="Scheduled Caste beneficiaries",
        application_mode="Through an authorised channel partner",
        installment_frequency="monthly",
        status="active",
        source_id=src.id,
    )
    schemes = [
        Scheme(scheme_id="NSFDC-MFS", name="Micro Finance Scheme", scheme_type="micro_finance", purpose="business",
               project_cost_max=150000, max_loan_amount=140000, nsfdc_interest_rate=2, beneficiary_interest_rate=5,
               repayment_period_months=36, moratorium_period_months=3, **common),
        Scheme(scheme_id="NSFDC-TL", name="Term Loan", scheme_type="term_loan", purpose="business",
               project_cost_max=5000000, max_loan_amount=4500000, nsfdc_interest_rate=3, beneficiary_interest_rate=8,
               repayment_period_months=120, moratorium_period_months=6, **common),
        Scheme(scheme_id="NSFDC-AMY", name="Aajeevika Micro-Finance Yojana", scheme_type="micro_finance", purpose="business",
               project_cost_max=500000, max_loan_amount=450000, nsfdc_interest_rate=2, beneficiary_interest_rate=5,
               repayment_period_months=48, moratorium_period_months=3, **common),
        Scheme(scheme_id="NSFDC-UNY", name="Udyam Nidhi Yojana", scheme_type="term_loan", purpose="business",
               project_cost_max=1000000, max_loan_amount=900000, nsfdc_interest_rate=3, beneficiary_interest_rate=8,
               repayment_period_months=84, moratorium_period_months=6, **common),
        Scheme(scheme_id="NSFDC-ELS", name="Educational Loan Scheme", scheme_type="education_loan", purpose="education",
               project_cost_max=None, max_loan_amount=3000000, nsfdc_interest_rate=1.5, beneficiary_interest_rate=4,
               repayment_period_months=240, moratorium_period_months=12, **common),
    ]
    db.add_all(schemes)
    db.flush()
    by_id = {s.scheme_id: s for s in schemes}

    for s in schemes:
        db.add_all([
            EligibilityRule(scheme_id=s.id, field="is_sc", operator="==", value="true", priority=1,
                            explanation="Applicant must belong to a Scheduled Caste (prototype placeholder rule)",
                            source_id=src.id),
            EligibilityRule(scheme_id=s.id, field="annual_income", operator="<=", value="300000", unit="INR", priority=2,
                            explanation="Annual family income within the applicable limit (prototype placeholder value)",
                            source_id=src.id),
            EligibilityRule(scheme_id=s.id, field="purpose", operator="==", value=s.purpose, priority=3,
                            explanation=f"Scheme supports the {s.purpose} purpose", source_id=src.id),
        ])

    common_docs = [
        ("Caste certificate", True, "Issued by the competent authority"),
        ("Income certificate", True, "Annual family income proof"),
        ("Identity proof", True, "Aadhaar or an equivalent identity document"),
        ("Address proof", True, None),
    ]
    for s in schemes:
        for name, mandatory, desc in common_docs:
            db.add(ApplicationRequirement(scheme_id=s.id, document_name=name, mandatory=mandatory,
                                          description=desc, source_id=src.id))
        if s.purpose == "business":
            db.add(ApplicationRequirement(scheme_id=s.id, document_name="Project report", mandatory=True,
                                          description="Project cost and activity details", source_id=src.id))
        else:
            db.add(ApplicationRequirement(scheme_id=s.id, document_name="Admission letter", mandatory=True,
                                          description="From the admitting institution", source_id=src.id))

    db.add_all([
        Activity(name="tailoring", sector="Services", sub_sector="Garments",
                 keywords=["tailor", "stitching", "garment"], aliases=["stitching unit"]),
        Activity(name="dairy", sector="Agriculture allied", sub_sector="Animal husbandry",
                 keywords=["milk", "cattle"], aliases=["milk dairy"]),
        Activity(name="grocery shop", sector="Trade", sub_sector="Retail",
                 keywords=["kirana", "provision"], aliases=["kirana store"]),
        Activity(name="beauty parlour", sector="Services", sub_sector="Personal care",
                 keywords=["salon"], aliases=["salon"]),
        Activity(name="auto rickshaw", sector="Transport", sub_sector="Passenger",
                 keywords=["auto", "three wheeler"], aliases=["three wheeler"]),
    ])

    db.add_all([
        ElsCourse(course_name="B.Tech", category="Engineering", level="Undergraduate", source_id=src.id),
        ElsCourse(course_name="MBA", category="Management", level="Postgraduate", source_id=src.id),
        ElsCourse(course_name="MBBS", category="Medicine", level="Undergraduate", source_id=src.id),
        ElsCourse(course_name="B.Sc Nursing", category="Nursing", level="Undergraduate", source_id=src.id),
        ElsCourse(course_name="Diploma", category="Technical", level="Diploma", source_id=src.id),
    ])

    ts = dict(state="Telangana", district="Hyderabad", source_id=src.id)
    partners = [
        Partner(partner_id="SCA-TS-001", name="Prototype State Channelizing Agency, Hyderabad", partner_type="SCA",
                address="Masab Tank, Hyderabad", latitude=17.4126, longitude=78.4691, status="active", **ts),
        Partner(partner_id="PSB-HYD-001", name="Prototype public sector bank branch, Abids", partner_type="PSB",
                address="Abids, Hyderabad", latitude=17.3907, longitude=78.4761, status="active", **ts),
        Partner(partner_id="PSB-HYD-002", name="Prototype public sector bank branch, Secunderabad", partner_type="PSB",
                address="Secunderabad, Hyderabad", latitude=17.4399, longitude=78.4983, status="active", **ts),
        Partner(partner_id="RRB-TS-001", name="Prototype regional rural bank, Kukatpally", partner_type="RRB",
                address="Kukatpally, Hyderabad", latitude=17.4948, longitude=78.3996, status="active", **ts),
        Partner(partner_id="NBFC-HYD-001", name="Prototype NBFC-MFI, Dilsukhnagar", partner_type="NBFC_MFI",
                address="Dilsukhnagar, Hyderabad", latitude=17.3688, longitude=78.5247, status="active", **ts),
        Partner(partner_id="PSB-HYD-003", name="Prototype public sector bank branch, Mehdipatnam", partner_type="PSB",
                address="Mehdipatnam, Hyderabad", latitude=17.3948, longitude=78.4386, status="unknown", **ts),
        Partner(partner_id="PSB-WGL-001", name="Prototype public sector bank branch, Warangal", partner_type="PSB",
                address="Hanamkonda, Warangal", latitude=17.9689, longitude=79.5941, status="active",
                state="Telangana", district="Warangal", source_id=src.id),
        Partner(partner_id="PSB-HYD-004", name="Prototype inactive branch, Begumpet", partner_type="PSB",
                address="Begumpet, Hyderabad", latitude=17.4435, longitude=78.4636, status="inactive", **ts),
    ]
    db.add_all(partners)
    db.flush()
    p = {x.partner_id: x for x in partners}

    def link(pid: str, sid: str, status: str, scope: str = "Telangana") -> None:
        db.add(SchemePartnerMapping(scheme_id=by_id[sid].id, partner_id=p[pid].id,
                                    authorization_status=status, geographic_scope=scope, source_id=src.id))

    for sid in by_id:
        link("SCA-TS-001", sid, "authorized")
    for sid in ("NSFDC-TL", "NSFDC-UNY", "NSFDC-ELS"):
        link("PSB-HYD-001", sid, "authorized")
    link("PSB-HYD-002", "NSFDC-TL", "authorized")
    link("PSB-HYD-002", "NSFDC-ELS", "authorized")
    link("PSB-HYD-002", "NSFDC-UNY", "unknown")
    for sid in ("NSFDC-MFS", "NSFDC-AMY", "NSFDC-TL"):
        link("RRB-TS-001", sid, "authorized")
    for sid in ("NSFDC-MFS", "NSFDC-AMY"):
        link("NBFC-HYD-001", sid, "authorized")
    link("PSB-HYD-003", "NSFDC-TL", "not_authorized")
    link("PSB-WGL-001", "NSFDC-TL", "authorized")
    link("PSB-HYD-004", "NSFDC-TL", "authorized")

    # One prototype performance row, for the SCA only, so "unavailable" is the common case.
    db.add(PartnerPerformance(partner_id=p["SCA-TS-001"].id, period="FY2025-26 Q1", sanctioned_amount=50000000,
                              disbursed_amount=31250000, utilization_percentage=62.5, beneficiary_count=410,
                              status="active", as_of_date=date(2025, 6, 30), source_id=src.id))

    db.commit()
    return {"sources": 1, "schemes": len(schemes), "partners": len(partners)}
