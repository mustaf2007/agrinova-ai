from __future__ import annotations
import re

SOMALIA_LOCATIONS = {
    "Mogadishu": (2.0469, 45.3182), "Baidoa": (3.1138, 43.6498),
    "Kismayo": (-0.3582, 42.5454), "Beledweyne": (4.7358, 45.2036),
    "Jowhar": (2.7809, 45.5005), "Galkayo": (6.7697, 47.4308),
    "Garowe": (8.4021, 48.4828), "Hargeisa": (9.5624, 44.0770),
    "Bosaso": (11.2842, 49.1816), "Dhusamareb": (5.5350, 46.3861),
    "Marka": (1.7159, 44.7717), "Afgooye": (2.1381, 45.1212),
}
CROPS = {
    "Maize": {"water":"Moderate–high","duration":"90–150 days"},
    "Sorghum": {"water":"Low–moderate","duration":"90–150 days"},
    "Sesame": {"water":"Low–moderate","duration":"90–120 days"},
    "Cowpea": {"water":"Low–moderate","duration":"60–100 days"},
    "Banana": {"water":"High","duration":"Perennial"},
    "Tomato": {"water":"Moderate","duration":"70–110 days"},
    "Onion": {"water":"Moderate","duration":"90–150 days"},
    "Watermelon": {"water":"Moderate","duration":"75–100 days"},
    "Groundnut": {"water":"Moderate","duration":"90–130 days"},
    "Rice": {"water":"High","duration":"100–150 days"},
}
CROP_GUIDANCE = {
    "Maize": ["Use certified or locally recommended seed varieties suited to the rainfall zone.","Plant when effective soil moisture is adequate rather than relying on a fixed calendar date.","Scout regularly for fall armyworm and other pests; use integrated pest management.","Keep fields weed-managed during early crop establishment."],
    "Sorghum": ["Select locally adapted varieties with suitable maturity length.","Establish the crop after effective rainfall and avoid sowing into dry soil.","Monitor birds, shoot fly and grain mold risks where relevant.","Use crop residues and soil cover where practical to conserve moisture."],
    "Sesame": ["Use clean seed and a well-prepared, well-drained seedbed.","Avoid prolonged waterlogging and excessive nitrogen.","Monitor for leaf-feeding insects and diseases during humid periods.","Harvest according to capsule maturity to reduce shattering losses."],
    "Cowpea": ["Choose varieties adapted to local rainfall and intended use.","Use good-quality seed and avoid waterlogged fields.","Scout for aphids, pod borers and storage pests.","Rotate with cereals where practical."],
    "Banana": ["Ensure reliable irrigation or dependable rainfall and good drainage.","Use healthy planting material from trusted sources.","Maintain mulch and monitor nutrient status.","Scout for leaf diseases and weevils; manage infected material safely."],
    "Tomato": ["Use healthy seedlings and rotate away from solanaceous crops where possible.","Use drip or carefully managed irrigation to limit prolonged leaf wetness.","Scout for whiteflies, fruit borers and early/late blight symptoms.","Stake and prune according to variety and production system."],
    "Onion": ["Use clean seed or healthy transplants and well-drained soil.","Avoid irregular irrigation during bulb development.","Monitor thrips and foliar diseases.","Cure bulbs properly before storage."],
    "Watermelon": ["Select locally adapted varieties and suitable planting dates.","Avoid waterlogging and manage irrigation consistently.","Monitor for aphids, whiteflies and fruit flies.","Use clean fields and crop rotation to reduce disease carryover."],
    "Groundnut": ["Use tested seed and a loose, well-drained soil.","Avoid excessive nitrogen where nodulation is effective.","Monitor leaf spots and soil pests.","Dry and store pods properly to reduce aflatoxin risk."],
    "Rice": ["Use locally recommended varieties and ensure water availability before planting.","Manage water depth and weeds according to the production system.","Monitor for stem borers, blast and nutrient disorders.","Dry grain to safe moisture before storage."],
}

KNOWLEDGE = [
    {"title":"Managing maize water stress","category":"Water management","answer":"Maize is sensitive to water shortage around tasseling, silking and early grain filling. Where irrigation is available, prioritize these stages, avoid over-irrigation and check soil moisture below the surface. Mulching and timely weed control can reduce avoidable water loss. Adapt advice to soil texture and crop stage.","source":"FAO crop water management resources; local extension validation required."},
    {"title":"Integrated fall armyworm management","category":"Pest management","answer":"Scout fields frequently, especially young maize. Look for window-pane feeding, fresh frass in the whorl and larvae. Use locally approved integrated pest management: conserve natural enemies, use tolerant varieties where available, and seek extension advice before pesticide use. Follow label directions and local regulations.","source":"FAO fall armyworm guidance; local pesticide registration must be checked."},
    {"title":"Improving soil organic matter","category":"Soil management","answer":"Retain safe crop residues, add mature compost or well-decomposed manure, rotate crops with legumes where appropriate, reduce unnecessary soil disturbance and maintain ground cover. Test soil before selecting amendments.","source":"FAO soil management and conservation agriculture resources."},
    {"title":"Reducing soil erosion","category":"Soil management","answer":"Keep soil covered, use contour-aligned barriers on sloping land, maintain vegetative strips, reduce bare fallow periods and manage grazing pressure. Select measures according to slope, soil type and runoff pathways.","source":"FAO soil conservation resources."},
    {"title":"Planting after rainfall","category":"Crop planning","answer":"Do not use the first isolated shower as the only planting signal. Consider effective rainfall, soil moisture at seed depth, short-term forecast, crop duration and seed availability. Confirm seasonal onset and false-start risks with local extension services.","source":"General agronomic guidance; confirm with local seasonal advisories."},
    {"title":"Safe crop disease response","category":"Crop health","answer":"Record crop, variety, location, crop stage, symptom distribution and recent weather. Photograph whole plant, affected and healthy parts. Avoid applying chemicals based on one symptom alone; consult an extension officer or plant pathologist for confirmation.","source":"General plant-health diagnostic practice."},
    {"title":"Post-harvest grain storage","category":"Post-harvest","answer":"Harvest at suitable maturity, dry grain adequately, clean storage containers, keep grain off the floor, control moisture ingress and inspect regularly for insects or mold. Groundnut and maize require attention to safe drying and aflatoxin prevention.","source":"FAO post-harvest handling resources."},
    {"title":"Efficient irrigation practices","category":"Water management","answer":"Schedule irrigation based on crop stage, soil moisture, weather and water availability. Check for leaks, avoid waterlogging and consider salinity where irrigation water is used repeatedly.","source":"FAO irrigation and water management resources."},
    {"title":"Crop rotation with legumes","category":"Crop planning","answer":"Rotating cereals with legumes such as cowpea or groundnut can diversify production and may improve soil nitrogen dynamics. Benefits depend on biomass returned, nodulation, harvest removal, pest cycles and local conditions.","source":"FAO and CGIAR crop rotation research; local trials recommended."},
]

def get_crop_guidance(crop, region, season, farm_size):
    crop_profile = CROPS.get(crop)
    if crop_profile:
        water = crop_profile["water"]
        duration = crop_profile["duration"]
        guidance = CROP_GUIDANCE.get(crop, [])
    else:
        water = "Species- and growth-stage-dependent"
        duration = "Varies by species and variety"
        guidance = [
            f"Identify the exact species and variety of {crop} before selecting seed, planting material or production practices.",
            "Use locally validated extension guidance for planting time, spacing, water and nutrient management.",
            "Monitor the crop regularly and use integrated pest and disease management based on confirmed field observations.",
            "Consult a local agronomist or extension service for crop-specific recommendations."
        ]
    return {
        "water": water,
        "duration": duration,
        "guidance": guidance,
        "cautions": [
            f"Planning location: {region}. These are general crop characteristics, not a district-level suitability map.",
            f"Season selected: {season}. Confirm seasonal onset and rainfall outlook before planting.",
            "Seed rate, fertilizer rate and expected yield are not calculated because variety- and soil-specific local evidence is required.",
            "For user-entered crops or plants outside the built-in reference list, water needs and growing duration are intentionally left species-dependent rather than guessed.",
            "Use local extension guidance and a soil test to finalize input decisions."
        ],
    }

def assess_soil(ph, organic, ec, nitrogen, phosphorus, potassium, crop):
    out = []
    if ph < 5.5:
        out.append(("Soil reaction","Acidic range. Some crops may experience nutrient availability constraints; verify with a laboratory and seek locally recommended amendments."))
    elif ph <= 7.5:
        out.append(("Soil reaction","Within a commonly suitable pH range for many crops, though crop-specific tolerances vary."))
    elif ph <= 8.5:
        out.append(("Soil reaction","Alkaline range. Check micronutrient availability and irrigation-water quality."))
    else:
        out.append(("Soil reaction","Strongly alkaline. Specialist soil assessment is recommended before selecting amendments."))
    if organic < 1:
        out.append(("Organic matter","Low measured organic matter. Consider tested compost, residue retention, cover and rotations where feasible."))
    elif organic < 3:
        out.append(("Organic matter","Moderate-to-low range for many mineral soils. Build organic inputs where practical and monitor changes."))
    else:
        out.append(("Organic matter","Relatively higher organic matter for many mineral soils; maintain soil cover."))
    if ec >= 4:
        out.append(("Salinity indicator","May indicate salinity concern, but interpretation depends on test method (e.g. saturated paste ECe). Confirm the method."))
    else:
        out.append(("Salinity indicator","Entered EC is below the common 4 dS/m ECe threshold often used to flag saline soil; method differences matter."))
    out.append(("Nutrients","N, P and K cannot be classified reliably without extraction method, units, soil texture and regional calibration. Use the laboratory's interpretation."))
    out.append(("Crop context",f"Selected crop: {crop}. Do not infer fertilizer rates from these inputs alone."))
    return out

def screen_crop_symptoms(crop, symptoms, plant_part, conditions):
    s = set(symptoms)
    likely = "Cause undetermined — more field information is needed"
    explanation = "The selected symptoms do not point clearly to one cause. Several pests, diseases and nutrient or water stresses can look similar."
    actions = [
        "Inspect at least 10 plants across the field and note whether symptoms are patchy or widespread.",
        "Photograph the whole plant, upper and lower leaf surfaces, stem and roots where possible.",
        "Record crop variety, crop stage, date symptoms began and recent rainfall or irrigation.",
        "Ask a local agricultural extension officer or plant pathologist to confirm the cause before treatment."
    ]
    if "Holes or chewing damage" in s:
        likely = "Possible insect feeding damage"; explanation = "Chewed leaves or holes can be caused by caterpillars, beetles or other insects. The pest cannot be confirmed from this symptom alone."
        actions = ["Inspect leaf undersides, whorls and growing points for insects, eggs and fresh feeding.","Record pest size and presence of frass; use integrated pest management.","Avoid broad-spectrum pesticide use without confirming the pest and checking local registration."]
    elif "White powdery growth" in s:
        likely = "Possible powdery mildew or other surface fungal growth"; explanation = "White powdery growth can be consistent with powdery mildew, but dust, residues and other fungi can resemble it."
        actions = ["Check whether the growth is on both leaf surfaces and whether it spreads between plants.","Improve airflow where crop spacing and system allow.","Seek confirmation before using fungicides; follow local labels and safety requirements."]
    elif "Rust-colored pustules" in s:
        likely = "Possible rust disease"; explanation = "Orange, brown or raised pustules can be consistent with rust fungi on susceptible crops."
        actions = ["Inspect both leaf surfaces for raised pustules and record affected leaf age.","Avoid moving infected plant material between fields.","Obtain local diagnosis and variety-specific management advice."]
    elif "Mosaic / mottled pattern" in s:
        likely = "Possible viral disease or nutrient / herbicide injury"; explanation = "Mosaic patterns can be associated with plant viruses, but nutrient disorders and chemical injury can look similar."
        actions = ["Check for aphids, whiteflies or other vectors and note nearby affected crops.","Seek local advice before removing plants where a virus is suspected.","Use clean planting material and manage volunteer host plants."]
    elif "Yellowing leaves" in s or "Leaf edges drying" in s:
        likely = "Possible nutrient deficiency, water stress or root-zone problem"; explanation = "Yellowing and leaf-edge drying are non-specific and may reflect nutrient imbalance, salinity, drought, waterlogging or root damage."
        actions = ["Note which leaves are affected first and whether the pattern is uniform or between veins.","Check soil moisture, drainage and irrigation-water quality.","Use a soil or plant tissue test before applying fertilizer."]
    elif "Wilting" in s or "Rotting / soft tissue" in s:
        likely = "Possible water stress, root disease or stem / vascular disorder"; explanation = "Wilting and soft tissue may result from drought, waterlogging, root rot or vascular disease."
        actions = ["Check soil moisture at root depth and inspect roots on a representative plant.","Look for darkened roots, stem discoloration or foul odor.","Improve drainage only if waterlogging is confirmed; seek a diagnostic sample."]
    if "Heavy rainfall" in conditions or "High humidity" in conditions:
        actions.append("Given reported wet or humid conditions, inspect for leaf-spot and other moisture-favored diseases.")
    if "Hot and dry weather" in conditions:
        actions.append("Given reported hot and dry conditions, check for heat and moisture stress before assuming an infectious disease.")
    return {"likely_issue":likely,"explanation":explanation,"actions":actions}

def search_knowledge(query, category="All"):
    candidates = [item for item in KNOWLEDGE if category == "All" or item["category"] == category]
    if not query.strip() or not candidates:
        return []
    documents = [" ".join([x["title"], x["category"], x["answer"]]) for x in candidates]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(documents + [query])
        scores = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
        ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
        return [item for score, item in ranked if score > 0][:5]
    except (ImportError, ValueError):
        tokens = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
        ranked = []
        for item, document in zip(candidates, documents):
            words = set(re.findall(r"[a-zA-Z]{3,}", document.lower()))
            score = len(tokens & words) / max(len(tokens), 1)
            if score > 0:
                ranked.append((score, item))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in ranked[:5]]
