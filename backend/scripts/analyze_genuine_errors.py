import csv
import json
import os
import re
import sys
from collections import defaultdict, Counter

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
project_root = os.path.dirname(backend_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

dataset_dir = os.path.join(project_root, "data", "datasets", "CUB_200_2011")
analysis_dir = os.path.join(dataset_dir, "analysis")
os.makedirs(analysis_dir, exist_ok=True)

canonical_csv_path = os.path.join(analysis_dir, "canonical_species_results.csv")
classes_path = os.path.join(dataset_dir, "classes.txt")

# Load BioCLIP label table for taxonomy lookup
from bioclip.predict import TreeOfLifeClassifier
print("Loading BioCLIP taxonomy table...")
clf = TreeOfLifeClassifier()
label_df = clf.get_label_data()

def canonical_normalize(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r'^\d+\.', '', s)
    s = s.replace("'s", "").replace("’s", "").replace("'", "").replace("’", "")
    s = s.replace('_', ' ').replace('-', ' ')
    s = s.lower()
    s = re.sub(r'\bgrey\b', 'gray', s)
    s = re.sub(r'\bleconte\b', 'le conte', s)
    s = re.sub(r'[^a-z0-9\s]', '', s)
    return re.sub(r'\s+', ' ', s).strip()

# Build fast taxonomy lookup dictionaries
sci_tax_map = {}
common_tax_map = {}

for idx, row in label_df.iterrows():
    sci = canonical_normalize(str(row.get("species", "")))
    common = canonical_normalize(str(row.get("common_name", "")))
    t = {
        "order": str(row.get("order", "")).strip().lower(),
        "family": str(row.get("family", "")).strip().lower(),
        "genus": str(row.get("genus", "")).strip().lower(),
        "species": str(row.get("species", "")).strip().lower(),
        "common_name": str(row.get("common_name", "")).strip().lower()
    }
    if sci and sci not in sci_tax_map:
        sci_tax_map[sci] = t
    if common and common not in common_tax_map:
        common_tax_map[common] = t

# Manual taxonomy lookup dict for CUB 200 classes
CUB_SPECIES_SCI_MAP = {
    "001.black footed albatross": "phoebastria nigripes",
    "002.laysan albatross": "phoebastria immutabilis",
    "003.sooty albatross": "phoebetria fusca",
    "004.groove billed ani": "crotophaga sulcirostris",
    "005.crested auklet": "aethia cristatella",
    "006.least auklet": "aethia pusilla",
    "007.parakeet auklet": "aethia psittacula",
    "008.rhinoceros auklet": "cerorhinca monocerata",
    "009.brewer blackbird": "euphagus cyanocephalus",
    "010.red winged blackbird": "agelaius phoeniceus",
    "011.rusty blackbird": "euphagus carolinus",
    "012.yellow headed blackbird": "xanthocephalus xanthocephalus",
    "013.bobolink": "dolichonyx oryzivorus",
    "014.indigo bunting": "passerina cyanea",
    "015.lazuli bunting": "passerina amoena",
    "016.painted bunting": "passerina ciris",
    "017.cardinal": "cardinalis cardinalis",
    "018.spotted catbird": "ailuroedus melanotis",
    "019.gray catbird": "dumetella carolinensis",
    "020.yellow breasted chat": "icteria virens",
    "021.eastern towhee": "pipilo erythrophthalmus",
    "022.chuck will widow": "antrostomus carolinensis",
    "023.brandt cormorant": "uri态 cormorant", # fallback genus Uri
    "024.red faced cormorant": "uri态 cormorant",
    "025.pelagic cormorant": "uri态 cormorant",
    "026.bronzed cowbird": "molothrus aeneus",
    "027.shiny cowbird": "molothrus bonariensis",
    "028.brown creeper": "certhia americana",
    "029.american crow": "corvus brachyrhynchos",
    "030.fish crow": "corvus ossifragus",
    "031.black billed cuckoo": "coccyzus erythropthalmus",
    "032.mangrove cuckoo": "coccyzus minor",
    "033.yellow billed cuckoo": "coccyzus americanus",
    "034.gray crowned rosy finch": "leucosticte tephrocotis",
    "035.purple finch": "haemorhous purpureus",
    "036.northern flicker": "colaptes auratus",
    "037.acadian flycatcher": "empidonax virescens",
    "038.great crested flycatcher": "myiarchus crinitus",
    "039.least flycatcher": "empidonax minimus",
    "040.olive sided flycatcher": "contopus cooperi",
    "041.scissor tailed flycatcher": "tyrannus forficatus",
    "042.vermilion flycatcher": "pyrocephalus rubinus",
    "043.yellow bellied flycatcher": "empidonax flaviventris",
    "044.frigatebird": "fregata aquila",
    "045.northern fulmar": "fulmarus glacialis",
    "046.gadwall": "mareca strepera",
    "047.american goldfinch": "spinus tristis",
    "048.european goldfinch": "carduelis carduelis",
    "049.boat tailed grackle": "quiscalus major",
    "050.eared grebe": "podiceps nigricollis",
    "051.horned grebe": "podiceps auritus",
    "052.pied billed grebe": "podilymbus podiceps",
    "053.western grebe": "aechmophorus occidentalis",
    "054.blue grosbeak": "passerina caerulea",
    "055.evening grosbeak": "coccothraustes vespertinus",
    "056.pine grosbeak": "pinicola enucleator",
    "057.rose breasted grosbeak": "pheucticus ludovicianus",
    "058.pigeon guillemot": "cepphus columba",
    "059.california gull": "larus californicus",
    "060.glaucous winged gull": "larus glaucescens",
    "061.heermann gull": "larus heermanni",
    "062.herring gull": "larus argentatus",
    "063.ivory gull": "pagophila eburnea",
    "064.ring billed gull": "larus delawarensis",
    "065.slaty backed gull": "larus schistisagus",
    "066.western gull": "larus occidentalis",
    "067.anna hummingbird": "calypte anna",
    "068.ruby throated hummingbird": "archilochus colubris",
    "069.rufous hummingbird": "selasphorus rufus",
    "070.green violetear": "colibri thalassinus",
    "071.long tailed jaeger": "stercorarius longicaudus",
    "072.pomarine jaeger": "stercorarius pomarinus",
    "073.blue jay": "cyanocitta cristata",
    "074.florida jay": "aphelocoma coerulescens",
    "075.green jay": "cyanocorax yncas",
    "076.dark ruffed junco": "junco hyemalis",
    "077.tropical kingbird": "tyrannus melancholicus",
    "078.gray kingbird": "tyrannus dominicensis",
    "079.belted kingfisher": "megaceryle alcyon",
    "080.green kingfisher": "chloroceryle americana",
    "081.pied kingfisher": "ceryle rudis",
    "082.ringed kingfisher": "megaceryle torquata",
    "083.white breasted kingfisher": "halcyon smyrnensis",
    "084.red leg kittiwake": "rissa brevirostris",
    "085.horned lark": "eremophila alpestris",
    "086.pacific loon": "gavia pacifica",
    "087.mallard": "anas platyrhynchos",
    "088.western meadowlark": "sturnella neglecta",
    "089.hooded merganser": "lophodytes cucullatus",
    "090.red breasted merganser": "mergus serrator",
    "091.mockingbird": "mimus polyglottos",
    "092.nighthawk": "chordeiles minor",
    "093.clark nutcracker": "nucifraga columbiana",
    "094.white breasted nuthatch": "sitta carolinensis",
    "095.baltimore oriole": "icterus galbula",
    "096.hooded oriole": "icterus cucullatus",
    "097.orchard oriole": "icterus spurius",
    "098.scott oriole": "icterus parisorum",
    "099.ovenbird": "seiurus aurocapilla",
    "100.brown pelican": "pelecanus occidentalis",
    "101.white pelican": "pelecanus erythrorhynchos",
    "102.western wood pewee": "contopus sordidulus",
    "103.say phoebe": "sayornis saya",
    "104.american pipit": "anthus rubescens",
    "105.whip poor will": "antrostomus vociferus",
    "106.horned puffin": "fratercula corniculata",
    "107.common raven": "corvus corax",
    "108.white necked raven": "corvus albicollis",
    "109.american redstart": "setophaga ruticilla",
    "110.george wood warbler": "setophaga townsendi",
    "111.loggerhead shrike": "lanius ludovicianus",
    "112.great grey shrike": "lanius excubitor",
    "113.baird sparrow": "centronyx bairdii",
    "114.black troated sparrow": "amphispiza bilineata",
    "115.brewer sparrow": "spizella breweri",
    "116.chipping sparrow": "spizella passerina",
    "117.clay colored sparrow": "spizella pallida",
    "118.field sparrow": "spizella pusilla",
    "119.fox sparrow": "passerella iliaca",
    "120.grasshopper sparrow": "ammodramus savannarum",
    "121.harris sparrow": "zonotrichia querula",
    "122.henslow sparrow": "centronyx henslowii",
    "123.le conte sparrow": "ammospiza leconteii",
    "124.lincoln sparrow": "melospiza lincolnii",
    "125.nelson sharp tailed sparrow": "ammospiza nelsoni",
    "126.savannah sparrow": "passerculus sandwichensis",
    "127.seaside sparrow": "ammospiza maritima",
    "128.song sparrow": "melospiza melodia",
    "129.tree sparrow": "spizelloides arborea",
    "130.vesper sparrow": "pooecetes gramineus",
    "131.white crowned sparrow": "zonotrichia leucophrys",
    "132.white throated sparrow": "zonotrichia albicollis",
    "133.cape glossy starling": "lamprotornis nitens",
    "134.bank swallow": "riparia riparia",
    "135.barn swallow": "hirundo rustica",
    "136.cliff swallow": "petrochelidon pyrrhonota",
    "137.tree swallow": "tachycineta bicolor",
    "138.scarlet tanager": "piranga oliva",
    "139.summer tanager": "piranga rubra",
    "140.artic tern": "sterna paradisaea",
    "141.black tern": "chlidonias niger",
    "142.caspian tern": "hydroprogne caspia",
    "143.common tern": "sterna hirundo",
    "144.elegant tern": "thalassaeus elegans",
    "145.forster tern": "sterna forsteri",
    "146.least tern": "sternula antillarum",
    "147.green tailed towhee": "pipilo chlorurus",
    "148.brown thrasher": "toxostoma rufum",
    "149.sage thrasher": "oreoscoptes montanus",
    "150.black capped vireo": "vireo atricapilla",
    "151.blue headed vireo": "vireo solitarius",
    "152.philadelphia vireo": "vireo philadelphicus",
    "153.red eyed vireo": "vireo olivaceus",
    "154.warbling vireo": "vireo gilvus",
    "155.white eyed vireo": "vireo gryseus",
    "156.yellow throat vireo": "vireo flavifrons",
    "157.bay breasted warbler": "setophaga castanea",
    "158.black and white warbler": "mniotilta varia",
    "159.black throated blue warbler": "setophaga caerulescens",
    "160.black throated green warbler": "setophaga virens",
    "161.canada warbler": "cardellina canadensis",
    "162.cape may warbler": "setophaga tigrina",
    "163.cerulean warbler": "setophaga cerulea",
    "164.chestnut sided warbler": "setophaga pensylvanica",
    "165.golden winged warbler": "vermiphora chrysoptera",
    "166.hooded warbler": "setophaga citrina",
    "167.kentucky warbler": "geothlypis formosa",
    "168.magnolia warbler": "setophaga magnolia",
    "169.mourning warbler": "geothlypis philadelphia",
    "170.myrtle warbler": "setophaga coronata",
    "171.nashville warbler": "leiothlypis ruficapilla",
    "172.orange crowned warbler": "leiothlypis celata",
    "173.palm warbler": "setophaga palmarum",
    "174.pine warbler": "setophaga pinus",
    "175.prairie warbler": "setophaga discolor",
    "176.prothonotary warbler": "protonotaria citrea",
    "177.swainson warbler": "limnothlypis swainsonii",
    "178.tennessee warbler": "leiothlypis peregrina",
    "179.wilson warbler": "cardellina pusilla",
    "180.worm eating warbler": "helmitheros vermivorum",
    "181.yellow warbler": "setophaga petechia",
    "182.northern waterthrush": "parkesia noveboracensis",
    "183.louisiana waterthrush": "parkesia motacilla",
    "184.bohemian waxwing": "bombycilla garrulus",
    "185.cedar waxwing": "bombycilla cedrorum",
    "186.american three toed woodpecker": "picoides dorsalis",
    "187.black backed woodpecker": "picoides arcticus",
    "188.red bellied woodpecker": "melanerpes carolinus",
    "189.red headed woodpecker": "melanerpes erythrocephalus",
    "190.downy woodpecker": "dryobates pubescens",
    "191.hairy woodpecker": "dryobates villosus",
    "192.pileated woodpecker": "dryocopus pileatus",
    "193.bewick wren": "thryomanes bewickii",
    "194.cactus wren": "campylorhynchus brunneicapillus",
    "195.carolina wren": "thryothorus ludovicianus",
    "196.house wren": "troglodytes aedon",
    "197.marsh wren": "cistothorus palustris",
    "198.rock wren": "salpinctes obsoletus",
    "199.winter wren": "troglodytes hiemalis",
    "200.common yellowthroat": "geothlypis trichas"
}

def get_taxonomy(species_or_common_name: str) -> dict:
    cn = canonical_normalize(species_or_common_name)
    
    # Check overrides
    if cn in CUB_SPECIES_SCI_MAP:
        sci_override = CUB_SPECIES_SCI_MAP[cn]
        tax = sci_tax_map.get(sci_override) or common_tax_map.get(sci_override)
        if tax:
            return tax

    tax = common_tax_map.get(cn) or sci_tax_map.get(cn)
    if tax:
        return tax
        
    # Attempt splitting by space (genus)
    parts = cn.split()
    if len(parts) >= 2:
        genus_cand = parts[0]
        # Search df for genus
        matching_genus = label_df[label_df["genus"].str.lower() == genus_cand]
        if not matching_genus.empty:
            r = matching_genus.iloc[0]
            return {
                "kingdom": str(r.get("kingdom", "")),
                "class": str(r.get("class", "")),
                "order": str(r.get("order", "")),
                "family": str(r.get("family", "")),
                "genus": str(r.get("genus", "")),
                "species": str(r.get("species", "")),
                "common_name": str(r.get("common_name", ""))
            }

    return {"kingdom": "Animalia", "class": "Aves", "order": "unknown", "family": "unknown", "genus": "unknown", "species": cn, "common_name": cn}

print("Loading canonical_species_results.csv...")
rows = []
with open(canonical_csv_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

total_images = len(rows)
genuine_mismatches = [r for r in rows if r["match_type"] == "GENUINE_MISMATCH"]
num_genuine = len(genuine_mismatches)
print(f"Loaded {total_images} rows. Found {num_genuine} GENUINE_MISMATCH rows.")

# -------------------------------------------------------------------
# 1. MOST COMMON GENUINE CONFUSIONS (Top 30)
# -------------------------------------------------------------------
confusion_counts = defaultdict(lambda: {"count": 0, "confidences": [], "actual_name": ""})
actual_species_genuine_errors = defaultdict(int)

for r in genuine_mismatches:
    act = r["ground_truth"]
    pred = r["raw_prediction"]
    actual_species_genuine_errors[act] += 1
    
    key = (act, pred)
    confusion_counts[key]["count"] += 1
    confusion_counts[key]["confidences"].append(float(r["top1_confidence"]))

genuine_confusion_rows = []
for (act, pred), stats in confusion_counts.items():
    cnt = stats["count"]
    avg_c = sum(stats["confidences"]) / len(stats["confidences"])
    act_total_errs = actual_species_genuine_errors[act]
    pct_of_actual_errs = (cnt / act_total_errs * 100.0) if act_total_errs > 0 else 0.0

    genuine_confusion_rows.append({
        "actual_cub_class_name": act,
        "predicted_species": pred,
        "count": cnt,
        "average_confidence": round(avg_c, 4),
        "percentage_of_actual_species_errors": round(pct_of_actual_errs, 2)
    })

genuine_confusion_rows.sort(key=lambda x: (x["count"], x["average_confidence"]), reverse=True)

genuine_pairs_csv_path = os.path.join(analysis_dir, "genuine_error_pairs.csv")
with open(genuine_pairs_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "actual_cub_class_name", "predicted_species", "count",
        "average_confidence", "percentage_of_actual_species_errors"
    ])
    writer.writeheader()
    writer.writerows(genuine_confusion_rows)
print(f"Saved {genuine_pairs_csv_path}")

# -------------------------------------------------------------------
# 2. PER-SPECIES GENUINE ERROR RATE
# -------------------------------------------------------------------
species_all_stats = defaultdict(lambda: {"class_id": 0, "total": 0, "canonical_correct": 0, "genuine_incorrect": 0})

for r in rows:
    act = r["ground_truth"]
    species_all_stats[act]["total"] += 1
    if r["match_type"] in ("EXACT", "NAMING_VARIANT"):
        species_all_stats[act]["canonical_correct"] += 1
    else:
        species_all_stats[act]["genuine_incorrect"] += 1

species_error_rows = []
for idx, (act, stats) in enumerate(species_all_stats.items(), start=1):
    tot = stats["total"]
    corr = stats["canonical_correct"]
    g_err = stats["genuine_incorrect"]
    acc_pct = (corr / tot * 100.0) if tot > 0 else 0.0
    err_pct = (g_err / tot * 100.0) if tot > 0 else 0.0

    species_error_rows.append({
        "actual_cub_class_name": act,
        "total_test_images": tot,
        "canonical_correct": corr,
        "genuine_incorrect": g_err,
        "canonical_accuracy_percent": round(acc_pct, 2),
        "genuine_error_rate_percent": round(err_pct, 2)
    })

species_error_rows.sort(key=lambda x: x["genuine_error_rate_percent"], reverse=True)

species_rates_csv_path = os.path.join(analysis_dir, "genuine_species_error_rates.csv")
with open(species_rates_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "actual_cub_class_name", "total_test_images", "canonical_correct",
        "genuine_incorrect", "canonical_accuracy_percent", "genuine_error_rate_percent"
    ])
    writer.writeheader()
    writer.writerows(species_error_rows)
print(f"Saved {species_rates_csv_path}")

# -------------------------------------------------------------------
# 3. TAXONOMIC ERROR ANALYSIS
# -------------------------------------------------------------------
tax_rel_counts = {
    "Same Genus": {"count": 0, "confidences": []},
    "Same Family (Different Genus)": {"count": 0, "confidences": []},
    "Same Order (Different Family)": {"count": 0, "confidences": []},
    "Different Order": {"count": 0, "confidences": []},
    "Unknown Taxonomy": {"count": 0, "confidences": []}
}

for r in genuine_mismatches:
    act_tax = get_taxonomy(r["ground_truth"])
    pred_tax = get_taxonomy(r["raw_prediction"])
    conf = float(r["top1_confidence"])

    act_order = act_tax.get("order", "unknown").lower()
    pred_order = pred_tax.get("order", "unknown").lower()

    act_fam = act_tax.get("family", "unknown").lower()
    pred_fam = pred_tax.get("family", "unknown").lower()

    act_gen = act_tax.get("genus", "unknown").lower()
    pred_gen = pred_tax.get("genus", "unknown").lower()

    if act_gen != "unknown" and act_gen == pred_gen:
        cat = "Same Genus"
    elif act_fam != "unknown" and act_fam == pred_fam:
        cat = "Same Family (Different Genus)"
    elif act_order != "unknown" and act_order == pred_order:
        cat = "Same Order (Different Family)"
    elif act_order != "unknown" and pred_order != "unknown":
        cat = "Different Order"
    else:
        cat = "Unknown Taxonomy"

    tax_rel_counts[cat]["count"] += 1
    tax_rel_counts[cat]["confidences"].append(conf)

tax_analysis_rows = []
for cat, stats in tax_rel_counts.items():
    cnt = stats["count"]
    pct = (cnt / num_genuine * 100.0) if num_genuine > 0 else 0.0
    avg_c = (sum(stats["confidences"]) / len(stats["confidences"])) if stats["confidences"] else 0.0

    tax_analysis_rows.append({
        "taxonomic_level_relationship": cat,
        "genuine_error_count": cnt,
        "percentage_of_genuine_errors": round(pct, 2),
        "average_confidence": round(avg_c, 4)
    })

tax_csv_path = os.path.join(analysis_dir, "genuine_taxonomic_analysis.csv")
with open(tax_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "taxonomic_level_relationship", "genuine_error_count",
        "percentage_of_genuine_errors", "average_confidence"
    ])
    writer.writeheader()
    writer.writerows(tax_analysis_rows)
print(f"Saved {tax_csv_path}")

# -------------------------------------------------------------------
# 4. CONFIDENCE ANALYSIS OF GENUINE ERRORS
# -------------------------------------------------------------------
bins = [
    ("0-10", 0.0, 0.10),
    ("10-20", 0.10, 0.20),
    ("20-30", 0.20, 0.30),
    ("30-40", 0.30, 0.40),
    ("40-50", 0.40, 0.50),
    ("50-60", 0.50, 0.60),
    ("60-70", 0.60, 0.70),
    ("70-80", 0.70, 0.80),
    ("80-90", 0.80, 0.90),
    ("90-100", 0.90, 1.00001),
]

genuine_conf_rows = []
for label, low, high in bins:
    items = [r for r in genuine_mismatches if low <= float(r["top1_confidence"]) < high or (high > 1.0 and float(r["top1_confidence"]) == 1.0)]
    cnt = len(items)
    pct = (cnt / num_genuine * 100.0) if num_genuine > 0 else 0.0
    avg_c = (sum(float(r["top1_confidence"]) for r in items) / cnt) if cnt > 0 else 0.0

    genuine_conf_rows.append({
        "bin_range": label,
        "genuine_error_count": cnt,
        "percentage_of_genuine_errors": round(pct, 2),
        "average_confidence": round(avg_c, 4)
    })

genuine_conf_csv_path = os.path.join(analysis_dir, "genuine_confidence_analysis.csv")
with open(genuine_conf_csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "bin_range", "genuine_error_count", "percentage_of_genuine_errors", "average_confidence"
    ])
    writer.writeheader()
    writer.writerows(genuine_conf_rows)
print(f"Saved {genuine_conf_csv_path}")

# High confidence genuine error counts
ge_gt_80 = [r for r in genuine_mismatches if float(r["top1_confidence"]) >= 0.80]
ge_gt_90 = [r for r in genuine_mismatches if float(r["top1_confidence"]) >= 0.90]

# -------------------------------------------------------------------
# 5. TOP-K RECOVERY OF GENUINE ERRORS
# -------------------------------------------------------------------
top3_recovered = [r for r in genuine_mismatches if str(r["canonical_top3_correct"]).lower() == "true"]
top5_recovered = [r for r in genuine_mismatches if str(r["canonical_top5_correct"]).lower() == "true"]
missed_completely = [r for r in genuine_mismatches if str(r["canonical_top5_correct"]).lower() == "false"]

print("\n==========================================")
print("PHASE 22 GENUINE ERROR ANALYSIS SUMMARY")
print("==========================================")
print(f"Total Test Images:                   {total_images}")
print(f"Canonical Top-1 Correct:             {total_images - num_genuine} ({(total_images - num_genuine)/total_images*100:.2f}%)")
print(f"Total Genuine Mismatches:            {num_genuine} ({num_genuine/total_images*100:.2f}%)")
print()
print(f"Genuine Errors Recov. in Top-3:      {len(top3_recovered)} ({len(top3_recovered)/num_genuine*100:.2f}% of genuine errors)")
print(f"Genuine Errors Recov. in Top-5:      {len(top5_recovered)} ({len(top5_recovered)/num_genuine*100:.2f}% of genuine errors)")
print(f"Genuine Errors Missed (Not in Top5): {len(missed_completely)} ({len(missed_completely)/num_genuine*100:.2f}% of genuine errors)")
print()
print(f"Genuine Errors >= 80% Confidence:    {len(ge_gt_80)} ({len(ge_gt_80)/num_genuine*100:.2f}% of genuine errors, {len(ge_gt_80)/total_images*100:.2f}% of total images)")
print(f"Genuine Errors >= 90% Confidence:    {len(ge_gt_90)} ({len(ge_gt_90)/num_genuine*100:.2f}% of genuine errors, {len(ge_gt_90)/total_images*100:.2f}% of total images)")
print("\nTaxonomic Breakdown of Genuine Errors:")
for row in tax_analysis_rows:
    print(f"  {row['taxonomic_level_relationship']:<32}: {row['genuine_error_count']:3d} ({row['percentage_of_genuine_errors']:5.2f}%) | AvgConf: {row['average_confidence']*100:.1f}%")
