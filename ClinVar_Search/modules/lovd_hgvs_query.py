import requests

def check_hgvs_syntax(hgvs_notation: str):
    """
    Query the LOVD HGVS syntax checker API and return the corrected_value
    with the highest confidence score.
    """
    base_url = "https://api.lovd.nl"
    endpoint = f"/checkHGVS/{requests.utils.quote(hgvs_notation, safe='')}"
    url = base_url + endpoint

    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    # The relevant data is inside data["data"][0]["corrected_values"]
    items = data.get("data", [])
    if not items:
        return None, None, data

    corrected = items[0].get("corrected_values", {})
    if not corrected:
        return None, None, data

    # Pick key with highest probability
    best_variant = max(corrected, key=lambda k: corrected[k])
    best_conf = corrected[best_variant]

    return best_variant, best_conf, data


def main():
    variant = input("Enter HGVS or VCF-like variant: ").strip()
    best, confidence, raw = check_hgvs_syntax(variant)

    if best:
        print("\nBest HGVS suggestion:")
        print(best)
        print(f"Confidence: {confidence}")
    else:
        print("No corrected_values returned. Check input or raw output below.")

    #print("\nRaw response:")
    #print(raw)


if __name__ == "__main__":
    main()




