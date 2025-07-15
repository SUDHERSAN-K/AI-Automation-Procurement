
# 🧾 Project Procurement Rules – XYZ Renewables Solar Facility (Middle East)

## 🏗️ Project Context:
XYZ Renewables has partnered with Bechtel to construct a 200 MW solar energy facility in the Middle East. This project involves the procurement of critical electrical, mechanical, and structural components under strict timelines and quality requirements. The goal is to ensure timely delivery of compliant materials from qualified vendors.

---

## ✅ Vendor Selection Criteria:
- Vendor must have at least one of the following certifications: `ISO 9001`, `CE`, or `UL Listed`
- Vendor’s **lead time must be 30 days or less** for items required within the next 60 days
- Vendor’s **expertise must directly match the item category** (based on item-vendor mapping)
- Prefer vendors located in or near the **Middle East and South Asia** for logistical efficiency

---

## ⚠️ Red Flags:
- Avoid vendors that only have low-tier or local certifications (e.g., "Material Test Report" only)
- Avoid vendors with lead times exceeding 45 days for any item marked as urgent

---

## 🚨 Urgency Flags:
- Any item with a delivery date within the next **45 days** is considered **URGENT**
- Urgent items must be assigned to vendors with lead time **strictly under 30 days**
- Use `Delivery Date` in `df_items` to auto-calculate urgency status

---

## 💬 Justification Format:
For each recommended vendor, the GenAI assistant must generate a justification covering:
- Certification alignment
- Lead time suitability
- Past performance/reliability (from vendor history)
- Match between item type and vendor expertise

---

## 📄 Output Structure (Per Scope Row):
Each scope document entry must include:
- `Item Name`
- `Specification`
- `Quantity`
- `Unit of Measure`
- `Delivery Date`
- `Drawing Ref`
- `Urgency Flag` (Yes/No)
- `Recommended Vendor`
- `Justification`

Ensure the justification is **clear, professional, and concise**.
