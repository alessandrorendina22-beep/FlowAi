import streamlit as st
from huggingface_hub import InferenceClient

# Configurazione del token sicuro tramite Secrets di Streamlit Cloud
HF_TOKEN = st.secrets["HF_TOKEN"] 

client = InferenceClient(model="Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN)

st.set_page_config(page_title="FlowAI - Copilota Flowgorithm", page_icon="🧩", layout="centered")
st.title("FlowAI 🧩")
st.caption("Fase di test: genera algoritmi Flowgorithm unici e preparati all'interrogazione.")

# Inizializzazione della sessione
if 'xml_generato' not in st.session_state:
    st.session_state['xml_generato'] = None
if 'spiegazione' not in st.session_state:
    st.session_state['spiegazione'] = None

user_input = st.text_area(
    "Cosa deve fare l'algoritmo da testare?", 
    placeholder="Es: Calcola la media di N numeri inseriti dall'utente...", 
    height=150
)

if st.button("Genera e Ispeziona XML", use_container_width=True):
    if user_input:
        with st.spinner("L'IA sta elaborando lo schema e la guida per l'orale..."):
            try:
                SYSTEM_PROMPT = (
                    "Sei un compilatore XML preciso per Flowgorithm e un tutor scolastico. "
                    "Rispondi fornendo solo l'XML valido seguito dal separatore ===SPIEGAZIONE=== "
                    "e dalla guida per l'orale."
                )

                prompt_completo = f"""Sei un compilatore XML preciso per Flowgorithm (.fprg) versione 4.2 e un tutor didattico di informatica.

REGOLE DI SINTASSI DI FERRO PER EVITARE CRASH:

REGOLE TASSATIVE DI DICHIARAZIONE:
1. ANALISI VARIABILI: Prima di scrivere il corpo, individua TUTTE le variabili.
2. DICHIARAZIONE PREVENTIVA: Ogni variabile DEVE avere un tag <declare> all'inizio del body.
   Esempio: <declare name="nome" type="String" array="False" size=""/>
3. NO VARIABILI ORFANE: È vietato usare una variabile se non dichiarata prima.

REGOLE STRUTTURALI GENERALI E ANTI-PLAGIO:
4. VARIABILITÀ ANTI-PLAGIO (TASSATIVA): Usa nomi di variabili validi ma sempre unici e dinamici (es. al posto di 'i' usa 'contatore_pos', 'idx', 'numero_cicli'; al posto di 'somma' usa 'totale_accumulato', 'somma_parziale').
5. CONCATENAZIONE STRINGHE: Usa SEMPRE l'operatore & (es: &quot;Risultato: &quot; &amp; mia_variabile). NON usare MAI il segno '+'.
6. OUTPUT: Usa l'attributo 'expression' con virgolette codificate &quot;. Esempio: <output expression="&quot;Inserisci dati&quot;" newline="True"/>
7. INPUT: Usa sempre <input variable="nomeVariabile"/>
8. ASSEGNAZIONE: <assign variable="nomeVariabile" expression="valore"/>
9. DIVISIONE INTERA (CRITICA): Dichiara le variabili come Integer e usa '/'. 
10. OPERATORI LOGICI: Usa 'mod', 'and', 'or', 'not'.
11. CONDIZIONE IF: L'espressione va specificata dentro l'attributo 'expression' del tag 'if'. All'interno SOLO i tag 'then' ed 'else'.

SINTASSI DEI CICLI (NO TAG BODY INTERNI AI CICLI):
12. RISPETTO DEL CICLO: Usa <while> o <for> esattamente come richiesto.
13. WHILE: Istruzioni scritte DIRETTAMENTE dentro il tag <while>.
14. FOR: Attributi 'variable', 'start', 'end', 'direction', 'step'. Istruzioni DIRETTAMENTE dentro <for>.

FORMATO DI RISPOSTA RICHIESTO:
Genera prima l'XML del file Flowgorithm. Subito dopo l'XML, inserisci esattamente il separatore ===SPIEGAZIONE=== e aggiungi una spiegazione chiara per l'interrogazione.

Struttura esatta:
<?xml version="1.0"?>
<flowgorithm fileversion="4.2">
    <attributes>
        <attribute name="name" value="Algoritmo"/>
    </attributes>
    <function name="Main" type="None" variable="">
        <parameters/>
        <body>
            [IL TUO CODICE XML QUI]
        </body>
    </function>
</flowgorithm>
===SPIEGAZIONE===
### 🗣️ Come spiegare l'algoritmo alla lavagna
- Spiega la logica principale in 3-4 punti semplici.
- Motivazione delle scelte (es. perché hai usato quel determinato ciclo).

### ❓ Possibili domande trabocchetto del professore
- **Domanda 1:** ...
  **Risposta:** ...
- **Domanda 2:** ...
  **Risposta:** ...

Richiesta dell'utente: {user_input}"""

                response = client.chat_completion(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_completo}
                    ],
                    max_tokens=2500
                )
                
                full_response = response.choices[0].message.content

                # Separazione tra codice XML e Guida Orale
                if "===SPIEGAZIONE===" in full_response:
                    parts = full_response.split("===SPIEGAZIONE===")
                    xml_raw = parts[0]
                    st.session_state['spiegazione'] = parts[1].strip()
                else:
                    xml_raw = full_response
                    st.session_state['spiegazione'] = "Spiegazione per l'orale non disponibile per questa generazione."
                
                # Pulizia forzata dei blocchi di codice markdown
                xml_data = xml_raw.replace("```xml", "").replace("```", "").strip()
                if "<?xml" in xml_data:
                    xml_data = xml_data[xml_data.find("<?xml"):]
                
                st.session_state['xml_generato'] = xml_data
                st.success("Algoritmo e guida per l'orale generati con successo!")
                
            except Exception as e:
                st.error(f"Errore tecnico durante la generazione: {e}")
    else:
        st.warning("Per favore, scrivi un prompt logico prima di generare!")

# Interfaccia di output suddivisa in schede (Tabs)
if st.session_state['xml_generato']:
    tab_codice, tab_orale = st.tabs(["📄 Codice & File .FPRG", "🎓 Guida per l'Interrogazione"])

    with tab_codice:
        st.download_button(
            label="📥 SCARICA FILE .FPRG (Locale)",
            data=st.session_state['xml_generato'].encode('utf-8'),
            file_name="algoritmo_test.fprg",
            mime="application/xml",
            use_container_width=True
        )
        
        with st.expander("🔍 Ispeziona visivamente l'XML generato", expanded=True):
            st.code(st.session_state['xml_generato'], language="xml")

    with tab_orale:
        if st.session_state['spiegazione']:
            st.markdown(st.session_state['spiegazione'])
