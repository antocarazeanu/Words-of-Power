# 🦙 Words of Power - Simulare Locală cu TinyLlama
Acest proiect implementează un jucător automat ("LLM Player") pentru jocul Words of Power, folosind modelul TinyLlama-1.1B-Chat-v1.0.
LLM-ul (Large Language Model) alege strategic cel mai potrivit cuvânt pentru a contracara cuvântul introdus de utilizator, ghidat de o bază de date (PlayerBeatsSystemMap) sau, în lipsa acesteia, pe baza logicii generale.

🧩 Structură generală
Model utilizat: TinyLlama/TinyLlama-1.1B-Chat-v1.0 (de pe HuggingFace)

Interfață: Locală (input din terminal)

Strategie:

Dacă există sugestii din baza de cunoștințe (PlayerBeatsSystemMap), LLM alege dintre ele.

Dacă nu, LLM alege din întreaga listă de cuvinte (player_words_cost).

Fallback: Dacă LLM nu răspunde corect sau răspunde greșit, se folosește Sandpaper.

🚀 Cum rulezi proiectul?
1. Instalează cerințele
bash
Copy
Edit
pip install torch transformers accelerate
2. Rulează scriptul
bash
Copy
Edit
python words_of_power_simulation.py
3. Introdu cuvintele
La fiecare rundă, ți se va cere să introduci un cuvânt ("cuvântul Sistemului").

LLM-ul va răspunde cu alegerea sa optimă.

⚙️ Setări principale

Setare	Valoare	Descriere
LLM_ENABLED	True	Activează/dezactivează folosirea modelului
MODEL_ID	TinyLlama/TinyLlama-1.1B-Chat-v1.0	Modelul de LLM folosit
LLM_TIMEOUT_SECONDS	20.0	Timeout maxim pentru răspuns LLM
LLM_MAX_NEW_TOKENS	40	Număr maxim de tokeni generați de LLM
LLM_TEMPERATURE	0.4	Temperatură mai joasă pentru răspunsuri mai consistente
NUM_ROUNDS	10	Numărul de runde de jucat
📂 Structură internă
load_llm_model_and_tokenizer(model_id): Încarcă modelul și tokenizerul TinyLlama.

what_beats(system_word): Alege cel mai potrivit cuvânt folosind LLM.

play_local_simulation(player_id): Rulează jocul interactiv în terminal.

PlayerBeatsSystemMap: Dicționar folosit pentru sugestii bazate pe cunoștințe predefinite.

player_words_cost: Listă cu toate cuvintele și costurile asociate.

📋 Notițe
Modelul poate folosi GPU (dacă este disponibil) sau CPU (automat).

Dacă nu există o intrare specifică în mapă pentru un cuvânt dat, LLM-ul va încerca să aleagă logic dintre toate opțiunile disponibile.

Pentru un comportament optim, este recomandat să îmbogățești PlayerBeatsSystemMap cu cât mai multe relații posibile.

🛠 Posibile îmbunătățiri
Adăugarea salvării automatelor rezultate într-un fișier .json sau .csv.

Extinderea PlayerBeatsSystemMap pentru o acuratețe și strategie mai bune.

Integrarea unui server local pentru a putea simula și meciuri remote.

🔥 Exemplu de rulare
plaintext
Copy
Edit
--- Jucător (Simulat): LLM_Player_Guided_v2 ---
--- Server: N/A (Mod Local - User este Sistemul) ---
--- Runde: 10 ---
--- Strategie Jucător: LLM (TinyLlama/TinyLlama-1.1B-Chat-v1.0) ghidat de PlayerBeatsSystemMap ---
--- LLM Activat: True ---

=============== RUNDA 1/10 ===============
Introduceți cuvântul 'Sistemului' pentru runda 1: Fire
Se caută 'fire' în PlayerBeatsSystemMap...
MAPĂ NEGĂSITĂ: Nicio intrare specifică pentru 'fire'. LLM va folosi cunoștințe generale și lista completă.
LLM gândește...
>>> LLM a ales: 'Fire Extinguisher' (Cost: $50)
