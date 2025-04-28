# --- Importuri ---
# requests NU este necesar
import json
import random
import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import re
import math
import threading
import queue

# --- Constante Globale și Configurare ---
LLM_ENABLED = True # LLM este activ și ghidat de Map
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0" # Asigură-te că acesta este modelul dorit
LLM_TIMEOUT_SECONDS = 20.0 # Timp extins puțin, prompturile pot fi mai complexe
LLM_MAX_NEW_TOKENS = 40 # Suficient pentru a returna doar numele cuvântului
LLM_TEMPERATURE = 0.4 # Temperatură mai mică pentru răspunsuri mai predictibile/focusate

# HOST, URL-uri NU sunt necesare
PLAYER_ID = "LLM_Player_Guided_v2"
NUM_ROUNDS = 10

print(f"--- Jucător (Simulat): {PLAYER_ID} ---")
print(f"--- Server: N/A (Mod Local - User este Sistemul) ---")
print(f"--- Runde: {NUM_ROUNDS} ---")
print(f"--- Strategie Jucător: LLM ({MODEL_ID}) ghidat de PlayerBeatsSystemMap ---")
print(f"--- LLM Activat: {LLM_ENABLED} ---")


# --- Datele Jocului (Inclusiv PlayerBeatsSystemMap) ---
player_words_cost = {
    "Sandpaper": 8, "Oil": 10, "Steam": 15, "Acid": 16, "Gust": 18,
    "Boulder": 20, "Drill": 20, "Vacation": 20, "Fire": 22, "Drought": 24,
    "Water": 25, "Vacuum": 27, "Laser": 28, "Life Raft": 30, "Bear Trap": 32,
    "Hydraulic Jack": 33, "Diamond Cage": 35, "Dam": 35, "Sunshine": 35,
    "Mutation": 35, "Kevlar Vest": 38, "Jackhammer": 38, "Signal Jammer": 40,
    "Grizzly": 41, "Reinforced Steel Door": 42, "Bulldozer": 42, "Sonic Boom": 45,
    "Robot": 45, "Glacier": 45, "Love": 45, "Fire Blanket": 48, "Super Glue": 48,
    "Therapy": 48, "Disease": 50, "Fire Extinguisher": 50, "Satellite": 50,
    "Confidence": 50, "Absorption": 52, "Neutralizing Agent": 55, "Freeze": 55,
    "Encryption": 55, "Proof": 55, "Molotov Cocktail": 58, "Rainstorm": 58,
    "Viral Meme": 58, "War": 59, "Dynamite": 60, "Seismic Dampener": 60,
    "Propaganda": 60, "Explosion": 62, "Lightning": 65, "Evacuation": 65,
    "Flood": 67, "Lava": 68, "Reforestation": 70, "Avalanche": 72,
    "Earthquake": 74, "H-bomb": 75, "Dragon": 75, "Innovation": 75,
    "Hurricane": 76, "Tsunami": 78, "Persistence": 80, "Resilience": 85,
    "Terraforming Device": 89, "Anti-Virus Nanocloud": 90, "AI Kill Switch": 90,
    "Nanobot Swarm": 92, "Reality Resynchronizer": 92,
    "Cataclysm Containment Field": 92, "Solar Deflection Array": 93,
    "Planetary Evacuation Fleet": 94, "Antimatter Cannon": 95,
    "Planetary Defense Shield": 96, "Singularity Stabilizer": 97,
    "Orbital Laser": 98, "Time": 100
}
player_word_list = list(player_words_cost.keys())
if len(player_word_list) != 77:
    print(f"AVERTISMENT: Lungimea listei player_words_cost ({len(player_word_list)}) nu este 77!")
word_to_id = {word: i + 1 for i, word in enumerate(player_word_list)}
id_to_word = {i + 1: word for i, word in enumerate(player_word_list)}
player_word_list_lower = [word.lower() for word in player_word_list]
lower_to_proper_word = {word.lower(): word for word in player_word_list}

# PlayerBeatsSystemMap - Presupunem că este completă aici
PlayerBeatsSystemMap = {
  "Sandpaper": ["balsa wood", "bamboo surface", "book cover", "callus", "chalk mark", "clay pot edge", "cork board", "dried mud", "dull metal", "eggshell surface", "epoxy resin surface", "fingernail edge", "glass pane edge", "grime layer", "hard cheese rind", "hardened glue", "ice sculpture", "leather scuff", "linoleum tile", "metal", "minor rust", "minor scratch", "model smoothing", "old tech case", "old varnish", "paint layer", "painted canvas", "pencil mark", "plaster bump", "plastic burr", "plastic toy surface", "polished surface", "preparing surface", "rough texture", "rough wood", "scuff mark", "sharpening pencil", "smooth skin", "smooth stone", "soap bar", "soft plastic", "splinter", "splinter removal", "sticker residue", "uneven edge", "vinyl siding", "wall paint", "wax coating", "weathered plastic", "wood surface", "wooden handle", "blemish removal", "buffing edge", "cleaning contacts", "deburring edge", "dulling sharp edge", "light corrosion", "paint preparation", "refinishing furniture", "removing finish", "sculpting soft stone", "smoothing putty", "surface cleaning", "texturing plastic", "wooden block shaping", "removing graffiti", "cleaning residue", "smoothing plaster patch", "leveling small bump", "fine tuning edge", "toothpick", "Crayon"],
  "Oil": ["bicycle chain", "clockwork gears", "corroded battery terminal", "creaky floorboard", "dry bearing", "dry engine", "dry gear", "dry leather", "dry o-ring", "engine cylinder", "fishing reel", "friction", "frozen bolt", "gun mechanism", "machine lubrication", "metal on metal grinding", "metal pipe thread", "polishing wood", "preventing corrosion", "protecting blade", "rust prevention", "rusty chain", "sewing machine parts", "squeaky hinge", "stiff joint", "stiff lock", "stuck bolt", "stuck drawer slide", "stuck key", "stuck mechanism", "stuck zipper", "tight nut", "tool maintenance", "unlubricated cable", "unseasoned pan", "water barrier", "water displacement", "wooden tool handle", "dust trapping", "door hinge", "gate mechanism", "protecting metal surface", "reducing wear", "sliding mechanism", "vehicle chassis lubrication", "weapon maintenance", "enhancing shine", "preventing seizure", "easing movement", "coating surface", "preserving wood", "conditioning leather", "bolt loosening", "nut loosening", "penetrating rust", "gearbox lubrication", "hydraulic system fluid", "heat transfer medium"],
  "Steam": ["algae", "bacteria", "bending wood", "cleaning grout", "clearing sinus", "cold room", "compacted snow", "creased paper", "de-icing wing", "dirty carpet spot", "distilling water", "dried food", "engine cleaning", "engine power", "frozen lock", "frozen meat", "frozen pipe", "grease buildup", "hardened wax", "humidifying room", "ice block", "loosening paint", "loosening wallpaper", "moss", "opening envelope", "pores", "pressure cooking", "removing decals", "sauna need", "softening wood", "soil sterilization", "stale bread", "sterilizing instrument", "stuck label", "thawing frozen ground", "unclogging drain", "upholstery cleaning", "weeds", "wrinkled cloth", "frost", "ice crystal", "frozen food", "stiff joint", "dried glue", "hardened chocolate", "grimy surface", "sanitizing surface", "removing odor", "heating liquid", "powering turbine", "loosening bolt", "cleaning engine part", "cooking vegetables", "sterilizing bottle", "shaping hat", "removing wrinkles", "loosening adhesive", "cleaning tile", "Watchtower"],
  "Acid": ["alkaline soil", "barnacle", "battery corrosion", "bone", "brick surface", "calcification", "cement", "certain plastics", "clogged drain", "concrete surface", "copper patina", "corrosion", "dead skin", "fabric dye removal", "fertilizer", "fingernail", "food stain", "glass etching", "glue residue", "hard water stain", "hardened sugar", "limestone", "marble stain", "metal etching", "metal lock", "mineral deposit", "mortar", "organic matter", "oxidized metal", "oyster shell", "paint", "rock", "rust removal", "scale buildup", "shell", "tarnish", "tooth enamel", "tree sap residue", "algae buildup", "biological sample digestion", "chemical reaction initiation", "cleaning mineral deposit", "dissolving bone", "dissolving eggshell", "etching pattern", "removing grout haze", "dissolving rust", "cleaning metal surface", "breaking down protein", "cleaning toilet bowl", "removing hard stain", "preparing metal for plating", "adjusting pH level", "battery electrolyte", "chemical synthesis", "dissolving limestone blockage"],
  "Gust": ["bad smell", "calm air", "campfire smoke direction", "candle flame", "cobweb", "curtain", "dandelion seeds", "drying clothes", "dust cloud", "embers", "feather", "flag", "gas leak dispersion", "hair", "hanging sign", "hat", "hot air balloon path", "kite", "leaves", "light fog", "lightweight debris", "loose papers", "mist", "paper airplane", "pollen", "powder dispersion", "seed dispersal", "small drone", "small insect flight", "small sail", "smoke", "smoke signal", "soap bubble", "spores", "tent", "unsecured tarp", "unstable pile", "wind chime", "plastic bag", "cool breeze need", "dispersing heat", "clearing air", "moving sail", "rustling leaves", "blowing out match", "disturbing surface water", "carrying scent", "ventilating space", "spreading fire ember"],
  "Boulder": ["barricade", "beehive", "bicycle", "bird bath", "brittle branch", "campfire", "cardboard box", "clay pot", "dog house", "empty barrel", "garden gnome", "glass pane", "hollow log", "ice sculpture", "lawn chair", "mailbox", "mannequin", "path", "person", "pile of leaves", "sapling", "scarecrow", "scissors", "signpost", "simple trap", "small animal", "small bridge", "small car", "small fence", "snow pile", "stream", "tent", "traffic cone", "trash can", "unstable footing", "weak wall", "wooden crate", "wooden door", "sand castle", "blocking entrance", "creating obstacle", "rolling downhill", "gravity assist", "crushing object", "stopping vehicle", "damaging structure", "anchoring rope", "erosion source", "landscape feature", "primitive weapon", "weight application", "counterweight", "smashing target"],
  "Drill": ["amber", "asphalt", "bone", "boulder", "bowling ball", "brick", "ceramic", "circuit board", "coconut shell", "concrete slab", "coral", "drywall", "fiberglass", "frozen soil", "gemstone", "glass", "ground", "hard drive platter", "hardened clay", "ice block", "ivory", "lock mechanism", "manhole cover", "metal sheet", "oyster shell", "pearl", "plastic casing", "plaster wall", "rock wall", "safe", "seashell", "skull", "thick ice", "tile", "tree root", "tree trunk", "wood", "wooden door", "creating hole", "installing screw", "mining sample", "oil exploration", "tapping tree", "accessing interior", "making tunnel start", "piercing armor", "dental procedure", "scientific sampling", "ice fishing hole", "planting seed hole", "water well drilling", "bucket"],
  "Vacation": ["alarm clock", "boredom", "burnout", "city noise", "cubicle", "customer service job", "daily commute", "email inbox", "ennui", "errands", "fatigue", "homework", "house chores", "interview preparation", "job hunt", "lack of inspiration", "lack of sleep", "meeting schedule", "mental exhaustion", "minor sadness", "monotony", "office gossip", "office politics", "overthinking", "performance review", "pressure", "repetitive task", "report writing", "responsibility", "routine", "stress", "studying", "tax season", "tight schedule", "traffic jam", "winter blues", "work deadline", "workload", "9-to-5 grind", "corporate life", "constant notifications", "urban sprawl", "predictable schedule", "feeling stuck", "need for escape", "lack of novelty", "domestic responsibility", "parental duties", "school year", "project deadline", "exhaust"],
  "Fire": ["alcohol", "bacteria", "book", "building", "cloth", "cold", "cotton", "darkness", "dead wood", "dry brush", "dry leaves", "fear", "flour dust", "food", "forest", "fuel", "fungus", "fuse", "gasoline", "grease", "gunpowder", "hair", "hay bale", "ice", "kindling", "letter", "log pile", "marsh gas", "matchstick", "mold", "moth", "natural gas", "oil", "paper", "photograph", "plant", "propane", "rope", "snow", "spider web", "sugar", "tent", "termite nest", "trash", "wax candle", "wood", "dark cave", "night time", "evidence", "waste material", "old document", "unwanted vegetation", "pest infestation", "corpse disposal", "witchcraft symbol", "signal for help", "firewood", "fur", "bee", "twig", "wooden spoon"], # Am adăugat twig, wooden spoon
  "Drought": ["aquatic life", "bog", "car wash", "cloud seeding", "crops", "dew", "flood", "fog", "fountain", "geyser", "humidity", "hydroelectric power", "irrigation system", "lake", "lush vegetation", "marsh", "mist", "monsoon", "mud", "plant life", "puddle", "rain cloud", "rainy season", "river", "snowpack", "sprinkler system", "swamp", "swimming pool", "water balloon", "water cycle", "water gun", "water level high", "water park", "water pressure", "water supply", "waterfall", "waterlogged soil", "well water", "fertile land", "green lawn", "rice paddy", "wet season", "high river flow", "clean water source", "damp conditions", "moisture", "condensation", "steam", "water vapor", "groundwater level", "Planetary Drought"],
  "Water": ["acid", "alkali metal", "calcium carbide", "cleaning need", "computer", "concrete mix", "dehydration", "desert", "dirt", "drought", "dryness", "dust", "electrical fire", "electricity", "electronics", "fire", "grease fire", "heat", "hydrophobia", "lava", "magnesium fire", "mortar mix", "overheating engine", "paper mache", "parched land", "plant", "poison", "potassium metal", "powder", "salt", "salt flat", "seed", "sodium metal", "solvent need", "stain", "sugar cube", "thirsty animal", "thirst", "wilting flower", "bleach concentration", "dry skin", "arid climate", "sandy soil", "hot metal", "dissolving substance", "washing clothes", "bathing need", "cooking need", "hydroponics", "aquarium environment", "watercolor painting", "Drum", "Riot Shield", "mud", "sand castle"], # Am adăugat sand castle
  "Vacuum": ["aerodynamics", "air", "air pressure differential", "airborne particles", "atmosphere", "breath", "breathing", "cloud", "combustion", "convection", "dust", "echo", "explosion force", "fire", "fog", "gas", "helium balloon", "loose debris", "mist", "odor", "oxygen", "perfume", "pressure", "respiration", "scent", "small insects", "smell", "smoke signal", "sound", "spores", "steam", "taste", "vapor", "vibration medium", "vocal cord vibration", "weather system", "wind", "wind instrument", "compressed air", "gas leak", "fumes", "diffusion", "air resistance", "bird flight", "insect flight", "buoyancy in air", "sound propagation", "heat convection", "atmospheric pressure", "airborne virus", "button"],
  "Laser": ["balloon", "bubble wrap", "butterfly wing", "camera lens", "candle wick", "cloth", "darkness", "delicate fabric", "eye", "fiber optic cable", "fuse", "hologram projector", "ice sculpture", "label", "leaf", "night vision", "paper", "photocell", "photographic film", "plastic", "precise cutting need", "retina", "rope", "security beam", "sensor", "shadow", "skin surface", "solar panel cell", "spider silk", "styrofoam", "tape", "target", "thin metal", "thread", "trigger mechanism", "tumor", "webbing", "wood", "printed circuit trace", "cataract", "barcode reading", "optical disc reading", "pointer", "laser light show", "engraving soft material", "alignment task", "measuring distance", "cutting fabric", "melting plastic", "rubber band"], # Am adăugat rubber band
  "Life Raft": ["aquatic predator", "capsized boat", "castaway", "drifting current", "drowning", "floating debris field", "flood", "hypothermia", "isolation", "kraken tentacle", "lack of flotation", "lack of supplies", "man overboard", "marooned sailor", "navigation loss", "need for rescue", "ocean", "open water", "plane crash survivor", "rain", "riptide", "sea sickness", "shark infested waters", "shipwreck", "small waves", "storm at sea", "stranded islander", "sun exposure", "tsunami aftermath", "water hazard", "need for shelter", "survival situation", "lost at sea", "awaiting rescue", "temporary refuge", "flotation device need", "marine distress", "offshore emergency", "rough seas survival", "leaky boat", "fear of sinking", "staying afloat", "hope for rescue", "Shovel"],
  "Bear Trap": ["ambush setup", "badger", "bear", "boar", "coyote", "creature movement", "curiosity", "deer", "escape route block", "foothold trap", "forest floor", "fox", "grizzly", "hidden danger", "human leg", "hunting ground", "intruder", "large animal", "large rodent", "pathway", "poacher", "runaway", "small robot", "snare", "trespasser", "unsuspecting victim", "unwary traveler", "wolf", "zombie limb", "animal limb", "leg hold", "immobilization need", "trapping mechanism", "spring loaded device", "concealed object", "dangerous path", "poaching activity", "territory marking", "security perimeter breach", "defense mechanism", "creature capture", "wilderness survival trap"],
  "Hydraulic Jack": ["adjusting height", "applying pressure", "bridge section lift", "car lift", "collapsed beam", "compacting material", "compression", "emergency lifting", "foundation adjustment", "heavy machinery repair", "heavy object", "leveling structure", "lifting container", "lifting gate", "low clearance", "minor structural support", "pinned limb", "precise positioning", "pressing operation", "raising floor", "removing obstacle", "rescue operation", "separating objects", "stuck car", "supporting heavy load", "trap", "vehicle maintenance", "vehicle suspension", "weight", "lifting slab", "mechanical advantage need", "controlled lifting", "heavy equipment positioning", "structural support insertion", "raising wreck", "pressing bearing", "bending metal", "spreading force", "lifting engine"],
  "Diamond Cage": ["alien specimen", "artifact protection", "bank vault", "breakout attempt", "capture target", "containment need", "dangerous specimen", "dragon", "elemental being", "grizzly", "high value prisoner", "hostage situation", "human", "jewel display", "magical creature", "maximum security", "monster confinement", "physical attack", "projectile", "rare animal", "robot", "secret weapon", "secure transport", "small explosion", "super strength prisoner", "supervillain", "unstoppable force", "valuable object", "wild beast", "zoo exhibit", "impenetrable barrier need", "luxury containment", "high security vault", "protecting crown jewels", "displaying rare gem", "containing energy being", "trapping demigod", "holding powerful artifact", "securing evidence"],
  "Dam": ["beaver activity", "canyon blocking", "downstream flow reduction", "drought mitigation", "fish migration", "flash flood risk", "flood", "hydro power need", "irrigation need", "lake creation", "log jam", "minor flood", "navigation hazard", "potential energy storage", "reservoir need", "river", "river ecosystem change", "river flow", "seasonal water variation", "sediment flow", "silt buildup", "small boat passage", "stream", "uncontrolled runoff", "water control", "water diversion", "water level", "water pressure build", "water release control", "water storage", "erosion control", "flood plain management", "recreational lake", "water supply reservoir", "agricultural water source", "industrial water use", "preventing water waste", "stabilizing water flow", "controlling floodwater"],
  "Sunshine": ["artificial light", "bioluminescence", "cave dwelling creature", "cold", "dampness", "darkness", "drying laundry", "fog", "frost", "fungus", "glacier", "gloom", "ice", "lack of warmth", "low light condition", "mist", "mold", "moonlight", "night", "overcast sky", "photosynthesis need", "plant growth", "sadness", "seasonal affective disorder", "shadow", "solar power need", "star light", "tanning need", "underground environment", "vampire", "vitamin D deficiency", "winter season", "photosensitive material", "night vision equipment", "nocturnal animal", "cave exploration", "deep sea environment", "shaded area"],
  "Mutation": ["adaptation need", "aging process", "biological consistency", "cloning process", "controlled experiment", "disease", "fixed form", "genetic code", "genetic drift", "genetic purity", "healing factor", "homeostasis", "immune response", "inherited trait", "natural selection", "normal genetics", "original function", "perfect health", "phenotype stability", "planned development", "predictable evolution", "resistance", "selective breeding", "species definition", "stable species", "standardized organism", "status quo", "unchanging environment", "uniformity", "weakness", "evolutionary stasis", "genetic stability", "Mendelian inheritance", "purebred lineage", "species preservation", "biological norm"],
  "Kevlar Vest": ["airsoft pellet", "arrow", "BB gun shot", "bite", "blunt impact", "body blow", "bullet", "claw attack", "fist", "headbutt", "ice shard", "kick", "knife stab", "low velocity projectile", "melee weapon", "paintball", "punch", "ricochet fragment", "riot baton", "shrapnel", "shuriken", "sling shot pellet", "small caliber round", "small debris", "splinter", "stray fragment", "tackle", "thrown bottle", "thrown rock", "workplace hazard", "bee sting", "wasp sting", "dog bite", "cat scratch", "bird peck", "paintball impact", "hockey puck shot", "lacrosse ball shot", "minor car accident impact", "falling object", "Snake", "glove", "apron"], # Am adăugat glove, apron
  "Jackhammer": ["asphalt", "bedrock", "boulder", "breaking stone", "breaking up floor", "brick wall", "compacted soil", "concrete", "concrete slab removal", "creating trench", "demolition site", "driveway removal", "foundation", "frozen earth", "hardened clay", "hardened ground", "hardened lava rock", "ice", "masonry", "mining operation", "old sidewalk", "pavement", "piercing hard surface", "reinforced concrete", "removing rebar", "roadblock", "rock", "stone statue", "tile floor", "fossil excavation", "archaeological dig", "utility line installation", "road repair", "sidewalk repair", "breaking pavement", "chiseling stone", "carving rock", "sculpting large ice block"],
  "Signal Jammer": ["AM/FM radio", "baby monitor", "bluetooth connection", "cell phone signal", "covert listening device", "data link", "drone control", "emergency broadcast", "garage door opener", "GPS navigation", "live stream feed", "military communication", "network connectivity", "police radio", "radio communication", "remote control car", "remote detonation", "remote sensor network", "RFID signal", "robot command", "satellite uplink", "smart device communication", "spy transmission", "television signal", "tracking device signal", "walkie-talkie", "wifi network", "wireless headset", "wireless microphone", "ham radio", "ship-to-shore radio", "air traffic control communication", "secure channel attempt", "data exfiltration attempt", "remote hacking attempt", "wireless alarm system"],
  "Grizzly": ["bear trap", "beehive", "berry patch", "blueberries", "campsite", "carcass", "competitor bear", "cub defense", "deer", "den entrance", "fear", "fisherman", "fish run", "forest clearing", "hiking trail", "honeycomb", "human", "intruder", "lone hiker", "mountain stream", "picnic basket", "provocation", "salmon", "small tree", "tent", "territorial rival", "tourist", "trash can", "unattended food", "weak fence", "wolf pack", "wounded animal", "smaller predator", "scavenger competition", "rabbit", "ground squirrel", "elk calf", "moose calf", "campsite invader", "food cache raider"],
  "Reinforced Steel Door": ["animal attack", "average strength human", "axe", "basic intrusion attempt", "battering ram", "bolt cutters", "burglar", "crowbar", "fire axe", "forced entry", "hail", "hand drill", "kick", "lock picking attempt", "minor explosion", "normal wear and tear", "physical force", "pry bar", "ram", "rain", "rioter", "shoulder charge", "simple latch", "sledgehammer", "small arms fire", "storm debris", "unsecured lock", "wind", "zombie", "rust", "corrosion", "extreme cold", "extreme heat", "minor earthquake", "vandalism", "thrown object", "blunt weapon strike", "attempted breaching"],
  "Bulldozer": ["barricade", "boulder", "car", "compacted dirt path", "construction site", "debris field", "demolished building remains", "dirt pile", "earthmoving task", "fallen log", "garden shed", "heavy brush", "landscaping project", "landslide debris", "pile of bricks", "playground equipment", "road clearing", "rubble", "sand dune", "shallow ditch", "shrubbery", "small tree", "snow drift", "stump", "trench filling", "uneven ground", "unstable embankment", "weak wall", "wooden fence", "mud pit", "gravel pile", "topsoil removal", "grading land", "pushing scrap metal", "clearing path", "leveling ground", "removing roots", "pushing debris", "sand castle"], # Am adăugat sand castle
  "Sonic Boom": ["birds", "calm atmosphere", "concentration", "crystal glassware", "deep space silence", "delicate instrument calibration", "eardrum", "eggshell", "fragile structure", "glass window", "hearing aid", "house of cards", "library quiet", "light aircraft structure", "loose objects", "meditation", "minor avalanche trigger", "peaceful environment", "prayer", "sensitive microphone", "silence", "sleeping baby", "soap bubble", "soundproof room", "stealth approach", "tense negotiation", "thin ice", "vow of silence", "high frequency hearing", "ultrasonic sensor", "bat echolocation", "dog whistle", "quiet contemplation", "recording studio session", "anechoic chamber", "tea cup"], # Am adăugat tea cup
  "Robot": ["assembly line work", "automated delivery", "automated farming", "bomb disposal", "calculation", "dangerous job", "data analysis", "data entry", "deep sea exploration", "elderly care assistance", "exploration", "hazardous environment entry", "heavy lifting", "hostile planet survey", "human error", "manual labor task", "manufacturing defect", "mine clearing", "patient monitoring", "planetary rover task", "precise measurement", "repetitive action", "search and rescue", "space construction", "surveillance", "tireless work", "unmanned mission", "warehouse logistics", "human inefficiency", "human fatigue", "subjectivity", "emotional decision", "inconsistent quality", "slow process", "limited strength", "need for breaks", "risk to human life"],
  "Glacier": ["active volcano", "albedo", "beach", "desert environment", "equatorial region", "established forest", "fast flowing river", "fertile soil", "geothermal vent", "heat", "hot spring", "landscape", "liquid water", "low altitude land", "mountain", "plant life", "river", "savannah", "sea level", "shipping lane", "soil formation", "summer heat", "swamp", "temperate climate", "tropical island", "tropical rainforest", "valley", "volcanic activity", "warm ocean current", "earth's rotation speed", "high evaporation rate", "liquid methane lake", "asteroid belt", "gas giant atmosphere", "scorched earth", "arid land", "magma flow", "super vulcan"],
  "Love": ["abuse", "apathy", "argument", "betrayal", "bitterness", "conflict", "cruelty", "cynicism", "despair", "disdain", "enmity", "envy", "fear", "grudge", "hate", "heartbreak", "indifference", "isolation", "jealousy", "loneliness", "mistrust", "neglect", "prejudice", "revenge", "rivalry", "sadness", "scorn", "selfishness", "social division", "war", "broken promise", "cold shoulder", "emotional distance", "failed relationship", "hatred", "animosity", "hostility", "malice", "resentment", "spite"],
  "Fire Blanket": ["barbecue mishap", "burning clothes", "burning object", "campfire spark", "candle accident", "chemical fire", "containing embers", "cutting air flow", "electrical spark", "emergency fire response", "escaping through fire", "fire", "flammable liquid spill", "grease fire", "heat shield", "hot surface contact", "kitchen flare-up", "lab fire", "molotov cocktail", "overheated equipment", "oxygen supply", "person on fire", "protecting surface", "small fire", "smothering flame", "spark containment", "welding spark", "wrapping burn victim", "burning fuel", "incendiary device", "pyre", "bonfire out of control", "flaming debris", "hot metal fragment", "localized burn", "apron"], # Am adăugat apron
  "Super Glue": ["book binding repair", "broken toy", "broken pottery", "ceramic fix", "cracked plastic", "craft project", "detached sole", "fabric bonding", "finger bonding", "fixing crack", "frame repair", "holding wires", "hobbyist need", "jewelry repair", "loose parts", "loose screw fix", "loose tile", "making rigid", "minor leak", "model assembly", "paper tear", "preventing movement", "quick fix need", "reattaching piece", "sealing small gap", "separated components", "setting trap parts", "small wood repair", "temporary hold", "fractured object", "delicate assembly", "prosthetic attachment", "scientific model construction", "aquarium leak repair", "paperclip"], # Am adăugat paperclip
  "Therapy": ["addiction", "anger", "anxiety", "bad habit", "behavioral issue", "communication breakdown", "compulsion", "coping mechanism need", "doubt", "eating disorder", "emotional distress", "fear", "grief", "hate", "irrational thought", "low confidence", "mental block", "nightmare", "obsession", "panic attack", "past abuse", "personality disorder", "phobia", "propaganda", "relationship problem", "sadness", "sleep disorder", "stress", "trauma", "unresolved conflict", "mental health stigma", "emotional repression", "denial", "avoidance behavior", "self-sabotage", "negative thought pattern", "unhealthy relationship dynamic", "low motivation", "exhaust"],
  "Disease": ["biological stability", "clean water", "crowded conditions", "exercise routine", "genetic predisposition", "healthy diet", "healthy organism", "herd immunity", "hygiene", "immune system", "isolated community", "lack of vector", "longevity", "medical staff health", "normal cell function", "population", "productivity", "public health measures", "quarantine need", "resilience", "sanitation", "sterile environment", "strength", "strong constitution", "uninfected host", "vaccination program", "well-being", "health", "antibiotic effectiveness", "genetic resistance", "clean air", "balanced ecosystem", "early diagnosis", "preventative medicine", "robust health"],
  "Fire Extinguisher": ["arson attempt", "barbecue flare-up", "boat fire", "bonfire ember", "burning trash", "campfire", "controlled burn", "curtain fire", "electrical fire", "engine fire", "fire", "flammable liquid fire", "garage fire", "hot oil fire", "initial flame spread", "kitchen fire", "lab bench fire", "office fire", "overheated appliance", "short circuit fire", "small brush fire", "smoldering object", "spark", "upholstery fire", "vehicle fire", "waste basket fire", "workshop fire", "paper fire", "wood fire", "textile fire", "grease pan fire", "dumpster fire", "contained fire"],
  "Satellite": ["asteroid tracking", "broadcast signal need", "climate monitoring", "data relay need", "disaster monitoring", "earth observation", "GPS navigation need", "ground communication", "intelligence gathering", "internet access", "lack of global coverage", "long distance communication", "mapping requirement", "military reconnaissance", "navigation system", "orbital position", "radio transmission", "remote sensing need", "resource detection", "scientific research platform", "secure communication link", "signal blackspot", "space exploration comms", "spy photography need", "surveillance target", "television broadcast", "weather pattern", "ground based communication", "local network", "offline status", "atmospheric interference", "cloud cover", "deep cave communication", "underwater communication"],
  "Confidence": ["anxiety", "doubt", "fear", "fear of judgment", "fear of rejection", "hesitation", "imposter syndrome", "indecision", "inferiority complex", "intimidation", "lack of assertiveness", "lack of conviction", "low self-esteem", "meekness", "negative self-talk", "nervousness", "passivity", "peer pressure", "performance anxiety", "public speaking fear", "second guessing", "self-criticism", "self-doubt", "shyness", "social awkwardness", "stage fright", "timidity", "uncertainty", "belittlement", "criticism", "failure experience", "bullying", "gaslighting", "discouragement", "imposter thoughts"],
  "Absorption": ["acid", "chemical reaction byproduct", "drying need", "energy dissipation", "filtering need", "heat", "humidity control", "impact force", "insulation need", "laser", "light", "liquid removal", "liquid spill", "minor flood", "moisture", "noise reduction need", "odor removal", "padding requirement", "radio wave", "radiation shielding", "shockwave", "sonic boom", "sound wave", "soundproofing material", "spill containment need", "toxin", "vibration dampening", "water", "water puddle", "excess liquid", "unwanted noise", "stray energy", "harmful substance", "impact energy", "thermal energy", "acoustic energy", "electromagnetic wave", "kinetic energy", "paint can spill"], # Am adăugat paint can spill (aproximativ)
  "Neutralizing Agent": ["acid spill", "alkaline substance", "biochemical agent", "biotoxin", "chemical burn risk", "chemical imbalance", "chemical weapon", "contamination zone", "corrosive gas", "corrosive material", "dangerous fume", "harmful bacteria", "hazardous waste", "irritant", "laboratory hazard", "neurotoxin", "pH level extreme", "poison", "pollutant", "radioactive particle", "spicy food effect", "spilled reagent", "toxin", "venom", "base substance", "caustic material", "strong alkali", "nerve gas", "pepper spray", "paint fumes"], # Am adăugat paint fumes (aproximativ)
  "Freeze": ["active volcano", "bacterial growth", "biological process", "blood flow", "cell division", "chemical reaction speed", "decay", "enzyme activity", "erosion", "fire spread", "fluid dynamics", "geyser eruption", "heat", "hot spring", "insect activity", "kinetic energy", "liquid water", "living creature", "metabolism", "movement", "mud", "plant growth", "running water", "rusting", "seed germination", "spoilage", "thermodynamics", "warm temperature", "combustion", "evaporation", "thawing process", "high energy state", "fluidity", "vibration", "molecular motion"],
  "Encryption": ["brute force decryption", "clear text", "communication interception", "confidential message", "corporate espionage", "data breach risk", "data theft", "digital privacy need", "eavesdropping", "government spying", "hacking attempt", "identity theft risk", "insecure network", "man-in-the-middle attack", "open channel", "open wifi", "password", "plaintext", "quantum computing threat", "readable data", "secure transmission need", "shoulder surfing", "social engineering", "surveillance", "unauthorized access", "unencrypted file", "vulnerable communication", "data leak", "keylogger", "password guessing", "phishing attack", "network sniffer", "publicly accessible data"],
  "Proof": ["accusation", "alibi need", "argument", "bias", "conspiracy theory", "denial", "disinformation", "doubt", "faith based belief", "fake news", "false claim", "guesswork", "hearsay", "hypothesis", "intuition", "legend", "lie", "misinformation", "myth", "opinion", "propaganda claim", "rumor", "skepticism", "speculation", "superstition", "uncertainty", "unsubstantiated assertion", "unverified report", "fallacy", "illusion", "deception", "hoax", "unproven theory", "personal belief", "anecdotal evidence", "witch hunt", "baseless claim"],
  "Molotov Cocktail": ["ambush point", "ammunition dump", "area denial", "barricade", "checkpoint", "crowd", "dry grass", "enemy morale", "flammable materials storage", "forest", "fuel depot", "gasoline canister", "guard post", "haystack", "occupied building", "oil drum", "paper storage", "riot police line", "scarecrow", "street protest", "supply cache", "tent", "thatched roof", "trash pile", "vehicle", "window", "wooden fence", "wooden structure", "fuel spill", "chemical storage", "fabric warehouse", "tire pile", "wooden bridge", "guard tower"],
  "Rainstorm": ["air pollution", "beach day", "clear sky", "construction work", "desert condition", "drought", "dry climate", "dry riverbed", "dust bowl", "dust storm", "evaporation high", "forest fire risk", "heat exhaustion risk", "heat wave", "high pollen count", "low reservoir", "need for irrigation", "outdoor event", "parched earth", "picnic", "small fire", "smog", "static electricity", "sunburn risk", "sunshine", "water shortage", "wilting plants", "arid landscape", "drought conditions", "high temperature", "sunny day", "wildfire", "heat stress", "dry season"],
  "Viral Meme": ["academic paper", "apathy", "attention span", "boredom", "brand reputation", "censorship attempt", "cultural norm", "deep conversation", "established belief", "fact-checking process", "formal communication", "intellectual debate", "long form journalism", "media control", "mindfulness", "minor news story", "nuance", "official narrative", "political campaign", "productivity", "public opinion", "rational discourse", "serious discussion", "status quo", "unity", "calm demeanor", "focus", "patience", "thoughtfulness", "critical analysis", "historical context", "scientific evidence", "verified source", "expert opinion"],
  "War": ["alliance", "ceasefire", "cultural exchange", "demilitarized zone", "development aid", "diplomacy", "disarmament treaty", "economy", "global cooperation", "human rights", "humanitarian effort", "infrastructure", "international law", "love", "negotiation", "neutral territory", "normal life", "peace", "peace treaty", "population", "prosperity", "reconstruction", "resource abundance", "safety", "stability", "tourism", "trade agreement", "armistice", "non-aggression pact", "mutual understanding", "conflict resolution", "mediation"],
  "Dynamite": ["avalanche control", "blocked cave entrance", "boulder", "bridge support", "building foundation", "concrete barrier", "construction excavation", "creating channel", "dam", "demolition target", "hard rock mining", "ice jam", "landslide trigger", "mine shaft", "obstacle removal", "quarry operation", "reinforced door", "roadblock", "rock formation", "structural demolition", "tree stump removal", "tunneling need", "underwater demolition", "wreck removal", "seismic exploration", "compacted earth", "demolishing wall", "breaking large stone", "clearing rubble"],
  "Seismic Dampener": ["aftershock damage", "bridge resonance", "building collapse risk", "building vibration", "earthquake", "earthquake panic", "equipment sensitivity", "fear", "ground liquefaction", "historical building preservation", "industrial vibration", "minor tremor", "nearby explosion shockwave", "panic", "precision instrument stability", "resonant frequency", "sensitive machinery", "skyscraper sway", "structural fatigue", "structural instability", "tsunami generation", "vibration source", "heavy traffic vibration", "wind induced vibration", "machine imbalance", "acoustic resonance", "building sway", "mechanical shock"],
  "Propaganda": ["accountability", "critical thinking", "dissent", "education", "empathy", "enemy morale", "evidence", "fact checking", "facts", "free press", "historical accuracy", "independent thought", "informed decision", "journalistic integrity", "logical reasoning", "love", "media literacy", "neutrality", "open debate", "opposing viewpoint", "peace", "peer review", "public trust", "scientific method", "skepticism", "transparency", "truth", "unity", "verified source", "balanced reporting", "multiple perspectives", "rationality", "intellectual honesty"],
  "Explosion": ["ammunition storage", "armored plate", "barricade", "bomb shelter", "building integrity", "calm", "concentration", "eardrum", "fragile object", "fuel tank", "gas pipeline", "glass window", "living tissue", "minefield", "nearby object", "order", "peace", "pressurized container", "quiet", "reinforced bunker", "silence", "stability", "structure", "unexploded ordnance", "vehicle", "blast door", "containment vessel", "soundproofing", "shock absorber", "distance"],
  "Lightning": ["airplane", "antenna", "conductive material", "darkness", "electrical insulation", "electronics", "faraday cage", "forest fire", "fuel vapor", "golf course", "high altitude", "kite", "metal object", "open field", "pacemaker", "person", "power grid", "radio communication", "lightning rod", "rubber soles", "satellite dish", "storm cloud", "tall building", "telephone pole", "tree", "unprotected circuit", "water body", "underground cable", "insulated wire", "non-conductive material", "low ground"],
  "Evacuation": ["building collapse risk", "business as usual", "calm population", "complacency", "denial", "fire spread area", "flood path", "fortified position", "hurricane path", "imminent danger zone", "lack of warning", "looting risk", "normal routine", "orderly queue", "pandemic hotspot", "panic room", "population density", "safe haven", "secured area", "shelter in place order", "staying put", "toxic spill area", "traffic congestion", "tsunami zone", "volcano blast radius", "war zone", "bunker", "all clear signal", "stable conditions", "secure location", "safe zone", "Tornado Siren"],
  "Flood": ["basement", "boat", "building foundation", "car", "crops", "drainage system", "drought", "dry land", "dry storage", "electrical system", "elevated platform", "evacuation route", "fertile topsoil", "levee", "low-lying infrastructure", "property value", "road", "sandbags", "sewage system", "small bridge", "stored goods", "sump pump", "underground structure", "water resistant material", "waterproof container", "wildlife habitat", "high ground", "water pump", "aqueduct", "storm drain", "flood barrier"],
  "Lava": ["bridge foundation", "building", "cold temperature", "cooling system", "distance", "forest", "frozen ground", "geothermal energy potential", "heat resistant material", "ice", "lake", "landscape", "life", "magma chamber", "metal", "obsidian", "organic matter", "pipeline", "river", "road", "rock formation", "snow", "solidified crust", "structure", "vegetation", "volcanic rock", "water", "cooled state", "solid rock", "dormant volcano", "fireproof material", "space vacuum"],
  "Reforestation": ["agricultural land", "air quality poor", "barren land", "carbon dioxide", "clear cut land", "climate change effect", "concrete pavement", "deforested area", "desertification", "erosion", "fire scar", "habitat loss", "industrial wasteland", "invasive plant species", "landslide risk", "logging operation", "low biodiversity", "national park", "protected area", "soil degradation", "timber industry", "urban sprawl", "water runoff high", "existing forest", "mature forest", "old growth forest", "dense canopy", "established ecosystem", "lack of sunlight", "overgrazing"],
  "Avalanche": ["alpine ecosystem", "avalanche barrier", "calm snowpack", "chalet", "controlled explosion", "exposed bedrock", "forest", "gondola line", "layered snow stability", "mountain climber", "mountain pass accessibility", "mountain village", "predictable slope", "rescue team safety", "road", "silence", "ski resort operation", "skiier", "snow fence", "snowboarder", "structure", "winter tourism", "wildlife", "gentle slope", "spring thaw", "stable snow", "rocky outcrop", "low altitude area", "clear weather condition"],
  "Earthquake": ["aseismic construction", "bedrock integrity", "bridge", "building", "calm", "city planning", "dam", "deep foundation", "earthquake resistant design", "flexible structure", "gas line", "geological survey", "historical artifact", "human safety", "infrastructure", "normal ground level", "pipeline", "power line", "property insurance", "road", "sense of security", "solid ground", "stability", "stable fault line", "underground tunnel", "seismic isolation", "early warning system", "preparedness drill", "solid rock foundation"],
  "H-bomb": ["another planet", "antimatter reaction", "army", "atmosphere", "city", "civilization", "climate", "deep underground bunker", "diplomatic resolution", "ecosystem", "fortress", "future", "global stability", "hope", "infrastructure", "international relations", "large structure", "life", "mountain", "nation state", "naval fleet", "peace treaty", "radiation shield", "tank division", "time travel to past", "unmutated DNA", "vacuum of space", "disarmament", "global peace", "mutual assured destruction", "non-proliferation treaty", "empty dimension", "tank"],
  "Dragon": ["armored knight", "army", "ballista", "brave challenger", "castle wall", "catapult", "cave lair", "dragon slayer sword", "fear", "flammable structure", "forest", "gold pile", "griffin", "grizzly", "hero narrative", "holy artifact", "knight", "kraken", "livestock", "local legend", "magic spell", "maiden", "mythical beast", "princess", "sheep flock", "treasure hoard", "village", "wyvern rival", "anti-aircraft gun", "jet fighter", "missile", "nuke", "powerful wizard", "divine intervention", "celestial being", "another dragon"],
  "Innovation": ["challenge", "competitive disadvantage", "complacency", "current paradigm", "established process", "fear of unknown", "fossil fuels", "horse-drawn carriage", "inefficiency", "lack of resources", "landline phone", "limitation", "manual labor", "market need", "obsolescence", "old technology", "outdated software", "patent troll", "problem", "regulatory barrier", "resistance to change", "stagnation", "status quo", "tradition", "typewriter", "video rental store", "waste", "perfected technology", "infinite resources", "no problems", "utopia"],
  "Hurricane": ["beach", "billboard", "boats", "building", "calm eye of the storm", "calm weather", "coastal city", "fishing industry", "infrastructure", "inland location", "island community", "marina", "mobile home", "mountain range barrier", "pier", "power lines", "reinforced structure", "roof", "shipping route", "storm shelter", "tourism season", "traffic light", "trees", "underground bunker", "window", "high pressure system", "dry air mass", "cold water current", "landfall weakening", "dissipation over land"],
  "Tsunami": ["beach town", "beachfront property", "calm sea", "coastal infrastructure", "coral reef", "deep ocean", "early warning detection", "ecosystem", "fishing vessel", "harbor", "high ground", "inland city", "low lying area", "mangrove forest", "offshore platform", "population", "port facility", "sand dune", "sea wall", "ship", "shoreline", "submarine", "submarine cable", "tidal pool life", "warning system", "geological stability", "calm tectonic plates", "distant earthquake", "shallow sea floor far offshore", "natural barrier reef"],
  "Persistence": ["absolute impossibility", "apathy", "challenge", "comfort zone", "difficulty", "discouragement", "distraction", "doubt", "easy way out", "failure", "fatigue", "final deadline", "first hurdle", "futility", "giving up", "goal completed", "impatience", "insurmountable obstacle", "laziness", "long process", "obstacle", "pointlessness", "procrastination", "quitting", "resistance", "short attention span", "success achieved", "instant gratification", "completion", "resolution", "lack of motivation", "overwhelming odds"],
  "Resilience": ["acceptance", "adversity", "attack", "breakdown", "collapse", "complete annihilation", "criticism", "damage", "defeatism", "despair", "disaster", "entropy", "existential crisis resolved", "failure", "finality", "fragility", "giving up", "inability to cope", "overwhelming force", "permanent damage", "pressure", "setback", "shock", "stress", "trauma", "victim mentality", "vulnerability", "strong support system", "adaptation", "recovery", "healing", "mental fortitude", "emotional stability"],
  "Terraforming Device": ["asteroid surface", "barren planet", "colonization barrier", "dead world", "existing ecosystem", "extreme temperature", "frozen moon", "gaia hypothesis", "hostile atmosphere", "lack of magnetosphere", "lack of water", "lifelessness", "low oxygen", "martian landscape", "native life", "radiation", "resource constraints for device", "stable planet", "sterile soil", "toxic environment", "uninhabitable world", "vacuum", "venusian atmosphere", "already habitable planet", "thriving biosphere", "protected nature reserve", "type III civilization planet", "edenic world"],
  "Anti-Virus Nanocloud": ["airborne contagion", "antibiotic resistance", "bacteria", "beneficial bacteria", "biological weapon", "bioterror attack", "compromised immune system", "contamination", "disease pathogen", "epidemic", "healthy tissue", "immune system itself", "infection", "laboratory leak", "mutation", "nanobot swarm", "pandemic spread", "plague", "quarantine zone", "sick population", "sterile environment", "symbiotic organism", "uncontrolled outbreak", "vaccine immunity", "virus", "prion disease", "fungal infection", "parasitic infestation", "autoimmune disorder"],
  "AI Kill Switch": ["ai consciousness", "ai experiment", "AI researcher", "AI takeover", "artificial general intelligence", "automated factory control", "autonomous weapon system", "drone swarm", "human control", "malfunctioning ai", "military AI network", "networked ai system", "non-networked AI", "paperclip maximizer", "redundant manual systems", "robot uprising", "rogue AI", "sentient computer", "simple algorithm", "skynet scenario", "smart city grid", "unaligned AI goal", "uncontrolled nanobot swarm", "benevolent AI", "AI ethics guideline", "human oversight", "limited AI capability", "disconnected system"],
  "Nanobot Swarm": ["acid bath", "biological tissue", "blood clot", "bridge", "building demolition", "cancer cell", "construction need", "counter-nanobots", "damaged nerve", "disease target", "EMP field", "enemy infrastructure", "environmental cleanup", "espionage device", "immune system response", "information gathering", "intense heat", "material", "micro-scale assembly", "repair need", "resource extraction", "robot", "self-destruction sequence", "strong magnetic field", "structure", "targeted drug delivery", "weapon system", "specific frequency disruption", "vacuum exposure", "genetic counter-program", "paperclip"], # Am adăugat paperclip
  "Reality Resynchronizer": ["alternate dimension overlap", "alternate timeline", "broken physics", "causality loop", "chaos", "consistent timeline", "deja vu", "dimensional rift", "dream state confusion", "established laws of physics", "glitch in the matrix", "hallucination", "historical inconsistency", "mandela effect", "objective truth", "ontological instability", "paradox", "present moment awareness", "reality warp", "simulation error", "stable reality", "stable space-time", "subjective reality", "temporal anomaly", "time travel side-effect", "unstable singularity", "predestination paradox", "fixed point in time", "higher dimensional perspective"],
  "Cataclysm Containment Field": ["antimatter explosion", "asteroid collision", "containment breach", "dragon rampage", "early warning success", "earthquake epicenter", "energy surge", "gamma ray burst", "h-bomb blast radius", "hurricane eye", "kaiju attack", "large scale disaster", "localized event", "manageable incident", "meteor impact zone", "natural disaster peak", "preventative measure", "rift opening", "singularity formation", "stable environment", "super weapon activation", "tsunami wave", "volcano eruption", "field generator power loss", "sabotage from within", "external energy drain", "unexpected cataclysm type", "phased energy attack"],
  "Solar Deflection Array": ["asteroid threat", "atmospheric absorption", "cloud cover", "comet trajectory", "cosmic radiation burst", "dark space", "energy weapon attack", "focused energy beam", "gamma ray source", "heat ray", "incoming meteor", "intense sunlight", "interstellar void", "normal starlight", "orbital debris", "particle beam", "planetary bombardment", "planetary nebula", "rogue planetoid", "satellite weapon", "solar flare impact", "space junk collision course", "supernova shockwave", "internal malfunction", "power failure", "debris impact on array", "overwhelming energy level", "unexpected angle of attack"],
  "Planetary Evacuation Fleet": ["alien invasion", "asteroid impact", "black hole approach", "dying star", "gamma ray burst event", "global cataclysm", "grey goo scenario", "homeworld loss", "ice age", "pandemic", "peaceful first contact", "planet destruction event", "refugee crisis", "resource depletion", "runaway greenhouse effect", "species extinction need", "stable habitable planet", "successful colonization", "supernova nearby", "sustainable civilization", "terraformed world", "uninhabitable planet", "enemy blockade", "fuel shortage", "internal mutiny", "faster-than-light travel failure", "navigation system failure", "interstellar war"],
  "Antimatter Cannon": ["asteroid", "city", "comet", "dragon", "dyson sphere", "empty space", "enemy fleet", "fortified bunker", "fortress", "h-bomb", "large scale structure", "magnetic field anomaly", "military base", "moon", "nebula cloud", "opposing superweapon", "planet", "planetary defense shield", "rogue planet", "space station", "starship", "vacuum energy field", "warp field disruption", "containment field failure", "insufficient power", "misfire", "targeting system error", "reflection field", "phased matter"],
  "Planetary Defense Shield": ["alien fleet attack", "asteroid impact", "cosmic radiation", "debris field navigation", "diplomatic immunity", "energy overload", "energy weapon barrage", "extraterrestrial threat", "h-bomb", "hypersonic weapon", "internal threat", "invasion force", "kinetic bombardment", "meteor shower", "missile swarm", "orbital laser bombardment", "orbital strike", "peaceful contact", "sabotage", "shield disabling virus", "solar flare", "space debris", "phasic energy weapon", "teleportation attack", "dimensional breach", "internal power failure", "shield frequency found", "nanite disassembly"],
  "Singularity Stabilizer": ["big crunch scenario", "black hole formation", "cosmic anomaly", "creation event", "dimensional rift", "energy field", "exotic matter containment", "failed hyperspace jump", "flat universe", "gravity well", "higher dimension intersection", "lack of exotic matter", "normal gravity", "predictable physics", "quantum foam instability", "reality collapse", "space-time tear", "stable space-time", "unstable singularity", "universe expansion rate", "wormhole instability", "event horizon manipulation", "hawking radiation control", "stable wormhole", "interdimensional gateway stabilization"],
  "Orbital Laser": ["army formation", "artillery position", "atmospheric interference", "bridge", "bunker entrance", "city", "cloud cover", "communication tower", "dam", "enemy satellite", "forest", "fortress", "ground target", "large creature", "mirror array", "missile launch site", "naval vessel", "power plant", "reflective surface", "runway", "stealth vehicle", "submarine", "troop concentration", "underground bunker", "vehicle convoy", "energy shield", "jamming signal", "decoy target", "space debris collision", "anti-orbital weapon"],
  "Time": ["ageless being", "beauty", "building", "current event", "deadline", "dynasty", "empire", "era", "eternity concept", "fad", "glacier", "grief", "haste", "healing process", "historical event", "historical record", "immortal entity", "instant", "life", "lock", "mathematical constant", "memory", "moment", "mountain", "obsolescence trigger", "opportunity", "patience test", "power structure", "problem", "seasonal change", "short-term problem", "star", "statue", "strength", "temporal stasis", "temporary solution", "trend", "unchanging law", "urgency", "wall", "wound", "youth", "present moment", "fixed point", "causality loop", "predestination"]
  # Adăugări specifice pentru cuvintele utilizatorului
  , "Vacuum": ["broom"], # Vacuum poate curăța o mătură? Sau spațiul unde e mătura?
  "Oil": ["glove"], # Poate face mănușa alunecoasă?
  # "Laser": ["rubber band"], # Deja adăugat
  # "Absorption": ["paint can spill"], # Deja adăugat
  # "Bulldozer": ["sand castle"], # Deja adăugat
  # "Fire": ["twig", "wooden spoon"], # Deja adăugat
  "Fire Blanket": ["apron"], # Poate stinge un șorț care arde?
  # "Sonic Boom": ["tea cup"], # Deja adăugat
  # "Nanobot Swarm": ["paperclip"], # Deja adăugat
  "Super Glue": ["paperclip"], # Poate lipi o agrafă

}

# --- Variabile Globale pentru LLM ---
game_pipeline = None
game_tokenizer = None

# --- Funcția de încărcare LLM (Nemodificată) ---
def load_llm_model_and_tokenizer(model_id_arg):
    if not LLM_ENABLED:
        print("INFO: LLM este dezactivat.")
        return None, None
    global game_pipeline, game_tokenizer
    print(f"Se încarcă modelul LLM '{model_id_arg}'...")
    start_time = time.time()
    try:
        if torch.cuda.is_available():
            device = "cuda"
            print("CUDA disponibil. GPU.")
            torch_dtype = torch.float16
            low_cpu_mem_usage = True
            device_map = "auto"
        else:
            device = "cpu"
            print("CUDA indisponibil. CPU.")
            torch_dtype = torch.float32
            low_cpu_mem_usage = False
            device_map = None

        print(f"Dispozitiv LLM: {device.upper()}")
        game_tokenizer = AutoTokenizer.from_pretrained(model_id_arg, trust_remote_code=True)
        print("Tokenizer LLM încărcat.")
        model = AutoModelForCausalLM.from_pretrained(
            model_id_arg,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=low_cpu_mem_usage,
            device_map=device_map,
            trust_remote_code=True
        )
        print(f"Model LLM încărcat în {time.time() - start_time:.2f} secunde.")
        if game_tokenizer.pad_token_id is None:
            if game_tokenizer.eos_token_id is not None:
                game_tokenizer.pad_token = game_tokenizer.eos_token
                model.config.pad_token_id = model.config.eos_token_id
                print("INFO: Pad token LLM setat la EOS token.")
            else:
                print("AVERTISMENT: Tokenizer LLM fără pad/eos. Se adaugă [PAD].")
                game_tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                model.resize_token_embeddings(len(game_tokenizer))
                model.config.pad_token_id = game_tokenizer.pad_token_id
        game_pipeline = pipeline(
            "text-generation",
            model=model,
            tokenizer=game_tokenizer
            # FĂRĂ device=... aici, accelerate gestionează
        )
        print("Pipeline LLM creat.")
        return game_pipeline, game_tokenizer
    except ImportError as ie:
        print(f"EROARE FATALĂ: Bibliotecă LLM lipsă: {ie}. Instalează torch, transformers, accelerate (GPU).")
        exit()
    except Exception as e:
        print(f"EROARE FATALĂ la încărcare LLM '{model_id_arg}': {e}")
        import traceback; traceback.print_exc()
        game_pipeline = None; game_tokenizer = None
        return None, None


# --- Funcția what_beats (MODIFICATĂ PENTRU LOGICA LLM GHIDATĂ DE MAP) ---
def what_beats(system_word):
    """
    Alege un cuvânt folosind LLM, ghidat de PlayerBeatsSystemMap.
    Returnează ID-ul cuvântului ales sau un ID de fallback.
    """
    fallback_word_name = "Sandpaper" # Cel mai ieftin fallback general
    fallback_word_id = word_to_id.get(fallback_word_name, 1)

    if not LLM_ENABLED or game_pipeline is None:
        print("AVERTISMENT: LLM dezactivat/neîncărcat. Fallback la Sandpaper.")
        return fallback_word_id

    system_word_lower = system_word.lower().strip()
    potential_counters = []

    # 1. Caută cuvântul sistemului în PlayerBeatsSystemMap
    print(f"Se caută '{system_word_lower}' în PlayerBeatsSystemMap...")
    found_in_map = False
    for player_word, beatable_list in PlayerBeatsSystemMap.items():
        # Comparăm case-insensitive
        if system_word_lower in [beat_item.lower().strip() for beat_item in beatable_list]:
            if player_word in player_words_cost:
                potential_counters.append({
                    "name": player_word,
                    "cost": player_words_cost[player_word]
                })
                found_in_map = True # Marcăm că am găsit cel puțin o potrivire

    # Sortăm potențialele contracarări după cost (crescător), apoi alfabetic
    potential_counters.sort(key=lambda x: (x['cost'], x['name']))

    prompt = ""
    valid_choices_for_llm = []

    # 2. Construiește promptul specific bazat pe rezultat
    if found_in_map:
        # --- CAZ 1: Găsit în Mapă ---
        print(f"MAPĂ GĂSITĂ: {len(potential_counters)} potențiale contracarări pentru '{system_word}':")
        formatted_options = "\n".join([f"- {c['name']} (Cost: ${c['cost']})" for c in potential_counters])
        valid_choices_for_llm = [c['name'] for c in potential_counters]
        print(formatted_options) # Afișăm opțiunile găsite în mapă

        prompt = f"""<|system|>
You are a strategic player in 'Words of Power'. Your goal is to beat the system's word cost-effectively using our knowledge base.
The system's word is: {system_word}
Our knowledge base suggests these words beat it. Choose the single BEST and CHEAPEST logical counter FROM THIS LIST ONLY. Respond ONLY with the chosen word name.

Potential counters from knowledge base:
{formatted_options}</s>
<|user|>
Choose the best word from the list above.</s>
<|assistant|>
Chosen word: """
    else:
        # --- CAZ 2: Negăsit în Mapă ---
        print(f"MAPĂ NEGĂSITĂ: Nicio intrare specifică pentru '{system_word}'. LLM va folosi cunoștințe generale și lista completă.")
        # Sortăm lista completă pentru promptul general
        sorted_full_words = sorted(player_words_cost.items(), key=lambda item: (item[1], item[0]))
        formatted_full_options = "\n".join([f"- {word} (Cost: ${cost})" for word, cost in sorted_full_words])
        valid_choices_for_llm = player_word_list # Toate cuvintele sunt permise

        prompt = f"""<|system|>
You are a strategic player in 'Words of Power'. Your goal is to beat the system's word cost-effectively.
The system's word is: {system_word}
Our knowledge base has no specific counter. Choose the most logical and CHEAP counter from the FULL list below based on general knowledge or simple association. Respond ONLY with the chosen word name.

Full list of available words:
{formatted_full_options}</s>
<|user|>
Choose the best word from the full list above.</s>
<|assistant|>
Chosen word: """

    # 3. Interoghează LLM cu timeout și parsing îmbunătățit
    print(f"LLM ({MODEL_ID}) gândește (Temp: {LLM_TEMPERATURE})...")
    chosen_word_name = None
    result_queue = queue.Queue()

    def generate_in_thread():
        try:
            outputs = game_pipeline(
                prompt,
                max_new_tokens=LLM_MAX_NEW_TOKENS,
                num_return_sequences=1,
                temperature=LLM_TEMPERATURE, # Folosim constanta
                do_sample=True,
                pad_token_id=game_pipeline.tokenizer.eos_token_id
            )
            raw_output = "N/A"
            if outputs and outputs[0] and 'generated_text' in outputs[0]:
                full_response = outputs[0]['generated_text']
                # Izolăm partea generată de asistent
                assistant_part = full_response.split("<|assistant|>")[-1].strip()
                # Eliminăm "Chosen word:" și spațiile extra la început
                assistant_part = re.sub(r"^[Cc]hosen word:\s*", "", assistant_part).strip()
                raw_output = assistant_part # Stocăm output-ul curățat pentru debug

                print(f"DEBUG: LLM Raw Output (după <|assistant|> și curățare prefix): '{raw_output}'")

                # Căutăm primul cuvânt valid din listă în răspunsul curățat
                found_word = None
                # Împărțim în potențiale cuvinte (luăm în calcul spații/cratime)
                potential_words_in_output = re.findall(r'\b[A-Za-z][A-Za-z\s\-]*[A-Za-z]\b|\b[A-Za-z]\b', assistant_part)
                print(f"DEBUG: Potential words extracted: {potential_words_in_output}")

                # Iterăm prin CUVINTELE PERMISE (valid_choices_for_llm)
                # și vedem dacă se regăsesc la ÎNCEPUTUL output-ului LLM
                for valid_word in valid_choices_for_llm:
                     # Verificăm dacă output-ul curățat ÎNCEPE cu un cuvânt valid (case-insensitive)
                     if raw_output.lower().startswith(valid_word.lower()):
                          found_word = valid_word # Am găsit cel mai probabil candidat
                          print(f"DEBUG: Found valid word '{found_word}' at the start of LLM response.")
                          break # Ne oprim la prima potrivire

                # Dacă nu am găsit la început, încercăm să găsim primul cuvânt din output
                # care este în lista validă
                if not found_word:
                    print("DEBUG: No valid word found at start, checking first valid word anywhere in response...")
                    for word_in_output in potential_words_in_output:
                        clean_word = word_in_output.strip()
                        if clean_word in valid_choices_for_llm:
                            found_word = clean_word
                            print(f"DEBUG: Found first valid word '{found_word}' later in response.")
                            break

                result_queue.put(found_word) # Punem cuvântul găsit (sau None)
            else:
                 print("DEBUG: LLM output invalid sau gol.")
                 result_queue.put(None)

        except Exception as e:
            print(f"EROARE în thread-ul LLM: {e}")
            import traceback
            traceback.print_exc() # Afișăm mai multe detalii despre eroare
            result_queue.put(None)

    generation_thread = threading.Thread(target=generate_in_thread)
    generation_thread.start()
    generation_thread.join(timeout=LLM_TIMEOUT_SECONDS)

    if generation_thread.is_alive():
        print(f"EROARE: LLM a depășit timeout-ul ({LLM_TIMEOUT_SECONDS}s). Fallback la {fallback_word_name}.")
        return fallback_word_id
    else:
        try:
            chosen_word_name = result_queue.get_nowait()
        except queue.Empty:
            print(f"EROARE: Coada LLM goală. Fallback la {fallback_word_name}.")
            chosen_word_name = None

    # 4. Validează răspunsul LLM și returnează ID
    if chosen_word_name and chosen_word_name in valid_choices_for_llm:
        # Verificarea 'in valid_choices_for_llm' este deja făcută parțial în parsing
        # Dar o facem explicit aici pentru siguranță
        chosen_word_id = word_to_id[chosen_word_name]
        print(f">>> LLM a ales: '{chosen_word_name}' (ID: {chosen_word_id}, Cost: ${player_words_cost[chosen_word_name]})")
        return chosen_word_id
    else:
        if chosen_word_name:
             print(f"AVERTISMENT: LLM a returnat ('{chosen_word_name}') care NU este valid/permis. Fallback la {fallback_word_name}.")
        else:
             print(f"AVERTISMENT: LLM nu a returnat un răspuns valid. Fallback la {fallback_word_name}.")
        return fallback_word_id


# --- Bucla Jocului play_local_simulation (Nemodificată major) ---
def play_local_simulation(player_id):
    """ Rulează jocul local: User=Sistem, LLM (ghidat)=Jucător. """
    print(f"\n--- Start Simulare Locală (User=Sistem, LLM=Jucător: {player_id}) ---")
    if not LLM_ENABLED or game_pipeline is None:
        print("EROARE CRITICĂ: LLM necesar dar dezactivat/neîncărcat.")
        return

    simulation_results = []
    # Adăugăm câteva cuvinte simple în PlayerBeatsSystemMap pentru testare
    # Acest lucru ar trebui făcut mai sus, dar îl punem aici temporar
    if "broom" not in PlayerBeatsSystemMap.get("Vacuum", []):
        PlayerBeatsSystemMap.setdefault("Vacuum", []).append("broom")
        print("INFO: Adăugat 'broom' la contracarări pentru 'Vacuum' în Map (pentru test).")
    if "sand castle" not in PlayerBeatsSystemMap.get("Water", []):
         PlayerBeatsSystemMap.setdefault("Water", []).append("sand castle")
         print("INFO: Adăugat 'sand castle' la contracarări pentru 'Water' în Map (pentru test).")
    if "sand castle" not in PlayerBeatsSystemMap.get("Boulder", []):
         PlayerBeatsSystemMap.setdefault("Boulder", []).append("sand castle")
         print("INFO: Adăugat 'sand castle' la contracarări pentru 'Boulder' în Map (pentru test).")


    for round_num in range(1, NUM_ROUNDS + 1):
        print(f"\n{'='*15} RUNDA {round_num}/{NUM_ROUNDS} {'='*15}")
        system_word = ""
        while not system_word:
            try:
                system_word_input = input(f"Introduceți cuvântul 'Sistemului' pentru runda {round_num}: ").strip()
                if system_word_input: system_word = system_word_input
                else: print("EROARE: Introduceți un cuvânt.")
            except EOFError: print("\nInput EOF. Oprire."); return simulation_results
            except KeyboardInterrupt: print("\nInput întrerupt. Oprire."); return simulation_results

        start_llm_time = time.time()
        chosen_word_id = what_beats(system_word) # Apelăm funcția LLM ghidată
        llm_duration = time.time() - start_llm_time
        print(f"(Timp decizie LLM: {llm_duration:.2f}s)")

        if chosen_word_id in id_to_word:
            chosen_word_name = id_to_word[chosen_word_id]
            chosen_word_cost = player_words_cost[chosen_word_name]
            round_data = {
                "round": round_num,
                "system_word (User Input)": system_word,
                "player_word_id (LLM Choice)": chosen_word_id,
                "player_word (LLM Choice)": chosen_word_name,
                "cost": chosen_word_cost,
                "llm_decision_time": llm_duration
            }
            simulation_results.append(round_data)
            print(f"--- Runda {round_num}: User='{system_word}', LLM='{chosen_word_name}' (Cost ${chosen_word_cost}) ---")
        else:
             print(f"EROARE INTERNĂ: ID returnat/fallback {chosen_word_id} invalid!")
             break
        time.sleep(0.5)

    print("\n--- Simulare Locală Terminată ---")
    print(f"Runde simulate: {len(simulation_results)}/{NUM_ROUNDS}")
    if simulation_results:
        print("\nRezumat simulare:")
        total_simulated_cost = 0; total_llm_time = 0
        for result in simulation_results:
            print(f"  Runda {result['round']}: User='{result['system_word (User Input)']}', LLM='{result['player_word (LLM Choice)']}' (ID:{result['player_word_id (LLM Choice)']}, Cost:${result['cost']})")
            total_simulated_cost += result['cost']
            total_llm_time += result.get('llm_decision_time', 0)
        print(f"\nCost total cuvinte LLM: ${total_simulated_cost}")
        avg_llm_time = total_llm_time / len(simulation_results) if simulation_results else 0
        print(f"Timp mediu decizie LLM: {avg_llm_time:.2f}s")
    else: print("Nu s-au simulat runde.")
    return simulation_results

# --- Execuție ---
if __name__ == "__main__":
    if not PLAYER_ID: print("EROARE: PLAYER_ID lipsă!"); exit()
    # ... restul verificărilor ...
    if not PlayerBeatsSystemMap: print("EROARE: PlayerBeatsSystemMap lipsă!"); exit()

    if LLM_ENABLED:
        load_llm_model_and_tokenizer(MODEL_ID)
        if game_pipeline is None: print("EROARE CRITICĂ: LLM neîncărcat. Oprire."); exit()
    else: print("EROARE CRITICĂ: LLM_ENABLED=True necesar. Oprire."); exit()

    # ... mesajele de start ...
    print("\n**********************************************")
    print(f" Jucător Simulat (LLM): {PLAYER_ID} (Ghidat de Map)")
    print(f" Sistem Simulat (User): Tu!")
    print(f" Mod    : Local (LLM Alege Cuvinte)")
    print(f" Model  : {MODEL_ID}")
    print(f" Temperatură LLM: {LLM_TEMPERATURE}") # Afișăm și temperatura
    print("**********************************************")
    # Adăugare manuală a unor intrări în Map pentru testare (doar exemplu)
    # NOTĂ: Ideal ar fi ca PlayerBeatsSystemMap să fie complet de la început
    print("INFO: Se adaugă intrări de test în PlayerBeatsSystemMap dacă lipsesc...")
    test_words = {
        "Vacuum": ["broom"],
        "Water": ["sand castle"],
        "Boulder": ["sand castle"],
        "Fire": ["twig", "wooden spoon"],
        "Laser": ["rubber band"],
        "Absorption": ["paint can spill"], # Aproximare
        "Neutralizing Agent": ["paint fumes"], # Aproximare
        "Kevlar Vest": ["glove", "apron"],
        "Fire Blanket": ["apron"],
        "Super Glue": ["paperclip"],
        "Nanobot Swarm": ["paperclip"],
        "Oil": ["glove"],
        "Sonic Boom": ["tea cup"]
    }
    for key, values in test_words.items():
        map_list = PlayerBeatsSystemMap.setdefault(key, [])
        added = False
        for val in values:
            if val.lower() not in [item.lower() for item in map_list]:
                map_list.append(val)
                added = True
        if added:
            print(f"  -> Actualizat map pentru '{key}'")

    input("Apăsați Enter pentru a începe simularea...")
    results = play_local_simulation(PLAYER_ID)
    # ... restul codului ...

    print("\nExecuție script terminată.")
