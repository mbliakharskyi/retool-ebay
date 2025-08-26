CATEGORY_SITES = {
    "watches": ["chrono24.com", "watchcharts.com"],
    "wine": ["winesearcher.com", "winemarketplace.fr"],
    "coins": ["ma-shops.com", "numisbids.com"],
    "stamps": ["delcampe.net"],
}

def sites_for_category(cat: str) -> list[str]:
    if not cat:
        return []
    return CATEGORY_SITES.get(cat.strip().lower(), [])
