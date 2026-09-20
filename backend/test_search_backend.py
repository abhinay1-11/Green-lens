import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retries = Retry(total=2, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))
session.headers.update({'User-Agent': 'GreenLens/1.0 (biodiversity-monitor; mailto:contact@greenlens.app)'})

def search_gbif_and_wiki(q):
    results_map = {}
    term = q.strip()
    if not term:
        return []
    
    # 1. GBIF Search (searches canonical, scientific, and vernacular common names)
    try:
        r = session.get('https://api.gbif.org/v1/species/search', params={'q': term, 'limit': 15}, timeout=4)
        if r.status_code == 200:
            for item in r.json().get('results', []):
                sci = item.get('canonicalName') or item.get('species') or item.get('scientificName')
                rank = (item.get('rank') or '').upper()
                if not sci or rank not in ['SPECIES', 'SUBSPECIES', 'GENUS']:
                    continue
                key = sci.strip().lower()
                if key not in results_map:
                    vernacular = item.get('vernacularName')
                    if not vernacular and item.get('vernacularNames'):
                        for v in item['vernacularNames']:
                            if v.get('language') in ['eng', 'en', None]:
                                vernacular = v.get('vernacularName')
                                break
                    kingdom = (item.get('kingdom') or '').lower()
                    cat = 'other'
                    if kingdom in ['animalia', 'metazoa']:
                        cls = (item.get('class') or '').lower()
                        if cls == 'aves': cat = 'bird'
                        elif cls in ['insecta', 'insect', 'arachnida']: cat = 'insect'
                        else: cat = 'other'
                    elif kingdom in ['plantae', 'viridiplantae']:
                        cat = 'plant'
                        
                    results_map[key] = {
                        'scientific_name': sci.strip(),
                        'common_name': (vernacular or term).title(),
                        'category': cat,
                        'rank': rank.capitalize()
                    }
    except Exception as e:
        print(f'GBIF error for "{term}": {e}')

    # 2. GBIF Match (direct scientific/common name match) if zero results
    if not results_map:
        try:
            mr = session.get('https://api.gbif.org/v1/species/match', params={'name': term}, timeout=3)
            if mr.status_code == 200:
                mdata = mr.json()
                sci = mdata.get('canonicalName') or mdata.get('scientificName')
                if sci and mdata.get('rank') in ['SPECIES', 'SUBSPECIES', 'GENUS']:
                    key = sci.strip().lower()
                    kingdom = (mdata.get('kingdom') or '').lower()
                    cat = 'other'
                    if kingdom in ['animalia', 'metazoa']:
                        cls = (mdata.get('class') or '').lower()
                        if cls == 'aves': cat = 'bird'
                        elif cls in ['insecta', 'insect']: cat = 'insect'
                    elif kingdom in ['plantae', 'viridiplantae']:
                        cat = 'plant'
                    results_map[key] = {
                        'scientific_name': sci.strip(),
                        'common_name': term.title(),
                        'category': cat,
                        'rank': (mdata.get('rank') or 'Species').capitalize()
                    }
        except Exception as e:
            print(f'GBIF match error for "{term}": {e}')

    # 3. Wikipedia search fallback if still empty (handles common names like "Neem", "Monarch Butterfly")
    if not results_map:
        try:
            w_resp = session.get('https://en.wikipedia.org/w/api.php', params={'action': 'query', 'list': 'search', 'srsearch': f'{term} species', 'format': 'json'}, timeout=3)
            if w_resp.status_code == 200:
                for w in w_resp.json().get('query', {}).get('search', [])[:2]:
                    title = w['title']
                    mr = session.get('https://api.gbif.org/v1/species/match', params={'name': title}, timeout=3)
                    if mr.status_code == 200:
                        mdata = mr.json()
                        sci = mdata.get('canonicalName') or mdata.get('scientificName')
                        if sci and mdata.get('rank') in ['SPECIES', 'SUBSPECIES', 'GENUS']:
                            key = sci.strip().lower()
                            if key not in results_map:
                                kingdom = (mdata.get('kingdom') or '').lower()
                                cat = 'other'
                                if kingdom in ['animalia', 'metazoa']:
                                    cls = (mdata.get('class') or '').lower()
                                    if cls == 'aves': cat = 'bird'
                                    elif cls in ['insecta', 'insect']: cat = 'insect'
                                elif kingdom in ['plantae', 'viridiplantae']:
                                    cat = 'plant'
                                results_map[key] = {
                                    'scientific_name': sci.strip(),
                                    'common_name': title,
                                    'category': cat,
                                    'rank': (mdata.get('rank') or 'Species').capitalize()
                                }
        except Exception as e:
            print(f'Wiki error for "{term}": {e}')

    return list(results_map.values())

if __name__ == '__main__':
    test_terms = ['Greater Sage-Grouse', 'Neem', 'Apis mellifera', 'Black-footed Albatross', 'Monarch Butterfly', 'Centrocercus urophasianus', 'Azadirachta indica']
    for t in test_terms:
        res = search_gbif_and_wiki(t)
        print(f'Query "{t}" -> {len(res)} results:')
        for item in res[:3]:
            print('  ', item['scientific_name'], '|', item['common_name'], '|', item['category'])
