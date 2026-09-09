# SIH26092: MoSJE AI Scheme Matching for Marginalized Entrepreneurs

## Problem Statement

### Background

To promote the socio-economic empowerment of the Scheduled Caste (SC) population, the government provides concessional financial assistance and educational loans.

Beneficiaries with an annual family income of up to ₹5.00 Lakhs are eligible for various tailored financial products covering up to 90% of their project or education costs at highly concessional interest rates, typically ranging from 6.5% to 8% per annum.

However, direct loan applications are not entertained. Instead, funds are routed through a **Channel Finance System** comprising over 100 Channel Partners, including:

- State Channelizing Agencies (SCAs)
- Public Sector Banks (PSBs)
- Regional Rural Banks (RRBs)
- NBFC-MFIs

---

## Challenge

Citizens often lack awareness regarding which specific credit scheme fits their needs.

For example, they may have difficulty distinguishing between:

- A Micro Finance Scheme for small projects, up to ₹1.40 lakh
- A Term Loan for larger projects, up to ₹50.00 lakh
- An Educational Loan Scheme

Applicants also face difficulties identifying and locating the nearest authorized Channel Partner equipped to process their specific loan category.

This fragmentation leads to:

- Offline confusion
- Misrouted applications
- Delays in disbursement

The challenge is to develop an **intelligent, multi-lingual digital platform or mobile application** that bridges the gap between beneficiaries and the channelizing agencies.

---

# Expected Solution

Participants are expected to develop a comprehensive platform that includes the following components.

## 1. Smart Scheme Recommender

An AI/rule-based engine that takes basic user inputs such as:

- Project type
- Estimated cost
- Income level
- Education status

and automatically recommends the most suitable:

- Credit scheme
- Educational loan scheme

---

## 2. Financial Calculator

A dynamic tool to calculate projected EMIs while accounting for specific scheme guidelines such as:

- Maximum loan limits
- Interest rates
- Moratorium periods

Example ranges mentioned in the problem statement include:

- Interest rates: 6.5% to 15% depending on the scheme
- Moratorium periods: 3 to 12 months

The calculator should help beneficiaries understand the potential financial implications of the selected scheme.

---

## 3. Geo-Spatial Partner Locator & Router

Integration with a mapping service to identify the nearest eligible Channel Partner based on:

- User location
- Partner eligibility
- Relevant loan/scheme category

The routing mechanism should also consider the channel partner's current fund utilization eligibility, ensuring that applications are not sent to partners with high NPAs or overdues.

---

# Impact Goals

The proposed solution should aim to:

1. Enhance financial literacy among the target demographic regarding concessional lending.

2. Improve transparency and efficiency in the channel finance ecosystem.

3. Enable faster disbursements.

4. Improve fund utilization.

5. Reduce confusion and misrouting of applications.

---

# Core Functional Requirements

The system therefore needs to address three major problems:

### Problem 1: Scheme Discovery

Beneficiaries need help identifying which government scheme is appropriate for their particular requirement.

### Problem 2: Financial Understanding

Beneficiaries need a simple way to understand:

- Loan amount
- Interest
- Repayment
- EMI
- Moratorium
- Financing limits

### Problem 3: Channel Partner Discovery

Beneficiaries need to identify the appropriate nearby channel partner that can process their particular scheme/category.

---

# Key Inputs

The system is expected to work with beneficiary information including, but not necessarily limited to:

- Project type
- Estimated project cost
- Annual income
- Education status
- User location

Additional information may be required by individual schemes.

---

# Key Outputs

The platform should ultimately provide:

1. Recommended scheme(s)
2. Eligibility/suitability information
3. Financial/EMI calculation
4. Relevant scheme details
5. Appropriate channel partner
6. Location/distance information
7. Guidance toward the application process

---

# Target User Experience

The intended experience is:

User provides basic information
        ↓
System understands the user's requirement
        ↓
System identifies applicable schemes
        ↓
System recommends suitable scheme(s)
        ↓
System explains the recommendation
        ↓
User can estimate financial obligations
        ↓
System identifies an appropriate nearby channel partner
        ↓
User receives guidance for proceeding with the application

---

# Important Constraints

The solution must account for the fragmented nature of the existing channel finance ecosystem.

The system should:

- Reduce dependency on offline information discovery.
- Reduce misrouted applications.
- Help beneficiaries understand available concessional financial products.
- Support multilingual interaction.
- Use an AI/rule-based approach for scheme recommendation.
- Incorporate geographical partner discovery.
- Consider channel partner eligibility/performance information where such verified information is available.

---

# SIH Problem Statement Reference

Problem Statement ID:

**SIH26092**

Domain:

**MoSJE / Socio-Economic Empowerment**

Core Theme:

**AI-based scheme matching and channel partner discovery for marginalized entrepreneurs and beneficiaries.**