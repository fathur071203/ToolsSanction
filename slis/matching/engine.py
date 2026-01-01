from typing import List, Dict, Any, Tuple

from .names import calculate_advanced_name_score_normed, normalize_name, HybridNameIndex
from .dob import calculate_dob_score_flexible
from .geo import generate_geographic_insights
from .utils import normalize_and_compare



BASE_WEIGHTS = {
    "name": 0.50,         
    "dob": 0.35,          
    "citizenship": 0.15,  
}


def _extract_customer_fields(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ambil field nama, DOB, kewarganegaraan, residence, birthplace
    dengan fallback ke beberapa nama kolom yang mungkin.
    """
    name = (
        customer.get("Nama")
        or customer.get("Full_Name")
        or customer.get("full_name")
        or customer.get("name")
    )

    dob = (
        customer.get("Tanggal Lahir")
        or customer.get("Tanggal_Lahir")
        or customer.get("Date_of_Birth")
        or customer.get("dob")
    )

    citizenship = (
        customer.get("Kewarganegaraan")
        or customer.get("Citizenship")
        or customer.get("citizenship")
    )

    country_of_residence = (
        customer.get("Country_of_Residence")
        or customer.get("country_of_residence")
        or customer.get("Residence")
    )

    place_of_birth = (
        customer.get("Place_of_Birth")
        or customer.get("Tempat_Lahir")
        or customer.get("place_of_birth")
    )

    return {
        "name": name or "",
        "dob": dob or "",
        "citizenship": citizenship or "",
        "country_of_residence": country_of_residence or "",
        "place_of_birth": place_of_birth or "",
    }


def _extract_sanction_fields(sanction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ambil field kunci dari entry sanction list.
    Wajib punya Full_Name minimal.
    """
    full_name = (
        sanction.get("Full_Name")
        or sanction.get("full_name")
        or sanction.get("Name")
        or sanction.get("name")
    )

    date_of_birth = (
        sanction.get("Date_of_Birth")
        or sanction.get("dob")
        or sanction.get("Tanggal_Lahir")
    )

    citizenship = (
        sanction.get("Citizenship")
        or sanction.get("citizenship")
        or sanction.get("Kewarganegaraan")
    )

    source = sanction.get("Source_List") or sanction.get("source") or "N/A"

    return {
        "full_name": full_name or "",
        "date_of_birth": date_of_birth or "",
        "citizenship": citizenship or "",
        "source_list": source,
    }


def _compute_dynamic_weights(
    has_dob: bool,
    has_citizenship: bool,
) -> Tuple[str, Dict[str, float]]:
    """
    Menentukan skema bobot & bobot ter-normalisasi berdasarkan
    field yang tersedia untuk pasangan customer–sanction ini.

    Return:
        scheme_name: string deskriptif (mis. "name_dob", "name_only")
        weights: dict { "name": w_name, "dob": w_dob, "citizenship": w_cit }
                 (hanya key yg dipakai yang muncul; total = 1.0)
    """
    
    components: Dict[str, float] = {
        "name": BASE_WEIGHTS["name"],
    }

    if has_dob:
        components["dob"] = BASE_WEIGHTS["dob"]

    if has_citizenship:
        components["citizenship"] = BASE_WEIGHTS["citizenship"]

    total = sum(components.values())
    if total <= 0:
        # fallback defensif
        return "invalid", {"name": 1.0}

    normalized = {k: v / total for k, v in components.items()}

    if has_dob and has_citizenship:
        scheme_name = "name_dob_citizenship"
    elif has_dob and not has_citizenship:
        scheme_name = "name_dob"
    elif not has_dob and has_citizenship:
        scheme_name = "name_citizenship"
    else:
        scheme_name = "name_only"

    return scheme_name, normalized


def run_screening_engine(
    customers: List[Dict[str, Any]],
    sanctions: List[Dict[str, Any]],
    name_threshold: float = 70.0,
) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []

    # Precompute sanction payloads + GPU/CPU index once per call
    sanction_payloads: List[Dict[str, Any]] = []
    sanction_name_norms: List[str] = []
    for sanc in sanctions:
        sanc_fields = _extract_sanction_fields(sanc)
        full_name = sanc_fields["full_name"]
        if not full_name:
            continue
        name_norm = normalize_name(full_name)
        if not name_norm:
            continue
        payload = dict(sanc)
        payload["__slis_full_name"] = full_name
        payload["__slis_name_norm"] = name_norm
        payload["__slis_source_list"] = sanc_fields["source_list"]
        payload["__slis_date_of_birth"] = sanc_fields["date_of_birth"]
        payload["__slis_citizenship"] = sanc_fields["citizenship"]
        sanction_payloads.append(payload)
        sanction_name_norms.append(name_norm)

    sanction_index = HybridNameIndex(sanction_name_norms)

    for customer in customers:
        customer.setdefault("Country_of_Residence", customer.get("country_of_residence", ""))
        customer.setdefault("Place_of_Birth", customer.get("place_of_birth", ""))

    for cust in customers:
        cust_fields = _extract_customer_fields(cust)
        customer_name = cust_fields["name"]

        if not customer_name:
            
            continue

        customer_norm = normalize_name(customer_name)
        if not customer_norm:
            continue

        candidate_idxs = sanction_index.filter_indices(customer_norm)
        for idx in candidate_idxs:
            sanc_payload = sanction_payloads[idx]
            source_list = sanc_payload["__slis_source_list"]

            name_score = calculate_advanced_name_score_normed(
                customer_norm,
                sanc_payload["__slis_name_norm"],
            )

            
            if name_score < name_threshold:
                continue

            

            has_dob = bool(cust_fields["dob"] and sanc_payload["__slis_date_of_birth"])
            has_cit = bool(cust_fields["citizenship"] and sanc_payload["__slis_citizenship"])

            
            if has_dob:
                dob_score, dob_match_type = calculate_dob_score_flexible(
                    cust_fields["dob"],
                    sanc_payload["__slis_date_of_birth"],
                    source_list,
                )
            else:
                dob_score, dob_match_type = 0, "Not Available"

            
            if has_cit:
                citizenship_score = normalize_and_compare(
                    cust_fields["citizenship"],
                    sanc_payload["__slis_citizenship"],
                )
            else:
                citizenship_score = 0

            
            scheme_name, weights = _compute_dynamic_weights(
                has_dob=has_dob,
                has_citizenship=has_cit,
            )

            final_score = (
                weights.get("name", 0.0) * name_score
                + weights.get("dob", 0.0) * dob_score
                + weights.get("citizenship", 0.0) * citizenship_score
            )

            
            customer_geo_payload = {
                "Citizenship": cust_fields["citizenship"],
                "Country_of_Residence": cust_fields["country_of_residence"],
                "Place_of_Birth": cust_fields["place_of_birth"],
            }

            sanction_geo_payload = {
                "Citizenship": sanc_payload["__slis_citizenship"],
            }

            geo_insights = generate_geographic_insights(
                customer_geo_payload, sanction_geo_payload
            )

            exact_matches_found = []
            if has_dob and dob_score > 0:
                exact_matches_found.append(f"Date_of_Birth ({dob_match_type})")
            if has_cit and citizenship_score == 100:
                exact_matches_found.append("Citizenship")

            results.append(
                {
                    
                    "Customer_Id": cust.get("id") or cust.get("customer_id"),
                    "Sanction_Id": sanc.get("id") or sanc.get("sanction_id"),

                    "Customer_Name": customer_name,
                    "Matched_Sanction_Name": sanc_payload["__slis_full_name"],
                    "Source_List": source_list,

                    "Final_Score": final_score,
                    "Name_Score": name_score,
                    "DOB_Score": dob_score,
                    "DOB_Match_Type": dob_match_type,
                    "Citizenship_Score": citizenship_score,

                    "Customer_DOB": cust_fields["dob"],
                    "Sanction_DOB": sanc_payload["__slis_date_of_birth"],
                    "Customer_Citizenship": cust_fields["citizenship"],
                    "Sanction_Citizenship": sanc_payload["__slis_citizenship"],

                    "Exact_Matches": ", ".join(exact_matches_found) if exact_matches_found else "None",

                    "Geographic_Insights": geo_insights,

                    
                    "Weighting_Scheme": scheme_name,
                    "Weights_Used": {
                        "name": weights.get("name", 0.0),
                        "dob": weights.get("dob", 0.0),
                        "citizenship": weights.get("citizenship", 0.0),
                    },
                    "Has_DOB": has_dob,
                    "Has_Citizenship": has_cit,
                }
            )

    return results
