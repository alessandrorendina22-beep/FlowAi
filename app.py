
import streamlit as st
import streamlit.components.v1 as components
from huggingface_hub import InferenceClient
import xml.etree.ElementTree as ET

# --- CONFIGURAZIONE ---
if "HF_TOKEN" in st.secrets:
    HF_TOKEN = st.secrets["HF_TOKEN"]
else:
    HF_TOKEN = ""

if HF_TOKEN:
    client = InferenceClient(model="Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN)
else:
    client = None

# Ottimizzazione per Mobile
st.set_page_config(page_title="FlowAI Mobile", page_icon="📱", layout="centered")

st.title("📱 FlowAI Mobile")
st.markdown("Genera e **visualizza subito** i tuoi schemi Flowgorithm dal telefono!")

if 'xml_generato' not in st.session_state:
    st.session_state['xml_generato'] = None
if 'mermaid_code' not in st.session_state:
    st.session_state['mermaid_code'] = None

# Funzione per pulire le stringhe ed evitare che Mermaid si rompa con i caratteri speciali
def pulisci_per_mermaid(testo):
    if not testo:
        return ""
    # Rimuoviamo virgolette esterne o interne ed entità speciali che rompono Mermaid
    testo = testo.replace("&quot;", "").replace('"', "").replace("'", "")
    testo = testo.replace("&amp;", " & ")
    testo = testo.replace("<", "lt").replace(">", "gt")
    # Sostituiamo caratteri parentesi quadre o graffe se presenti
    testo = testo.replace("[", "(").replace("]", ")").replace("{", "(").replace("}", ")")
    return testo.strip()

# Funzione per convertire l'XML di Flowgorithm in un diagramma Mermaid per cellulare
def converti_xml_a_mermaid(xml_text):
    try:
        # Rimuove l'intestazione xml per evitare bug di parsing
        if "<?xml" in xml_text:
            xml_text = xml_text[xml_text.find("?>")+2:].strip()
        
        root = ET.fromstring(xml_text)
        main_function = root.find(".//function[@name='Main']")
        if main_function is None:
            # Se non trova Main, proviamo a cercare una qualsiasi funzione
            main_function = root.find(".//function")
            
        if main_function is None:
            return None
            
        body = main_function.find("body")
        if body is None:
            return None

        linee = ["graph TD"]
        # Stili accattivanti simili ai colori reali di Flowgorithm
        linee.append("classDef inizioFine fill:#e1bee7,stroke:#8e24aa,stroke-width:2px,rx:20px,ry:20px,color:#000;")
        linee.append("classDef inputOutput fill:#bbdefb,stroke:#1e88e5,stroke-width:2px,color:#000;")
        linee.append("classDef dichiarazione fill:#fff9c4,stroke:#fdd835,stroke-width:2px,color:#000;")
        linee.append("classDef decisione fill:#ffcdd2,stroke:#e53935,stroke-width:2px,color:#000;")
        linee.append("classDef azione fill:#e8f5e9,stroke:#43a047,stroke-width:2px,color:#000;")

        nodo_id = 0
        
        def parsing_nodi(element, parent_id):
            nonlocal nodo_id
            ultimo_id = parent_id
            
            for child in element:
                tag = child.tag
                if tag == "declare":
                    nodo_id += 1
                    current_id = f"n{nodo_id}"
                    name = child.get("name", "")
                    tipo = child.get("type", "Integer")
                    testo_pulito = pulisci_per_mermaid(f"Dichiara {tipo} {name}")
                    linee.append(f'{ultimo_id} --> {current_id}["{testo_pulito}"]:::dichiarazione')
                    ultimo_id = current_id
                    
                elif tag == "input":
                    nodo_id += 1
                    current_id = f"n{nodo_id}"
                    var = child.get("variable", "")
                    testo_pulito = pulisci_per_mermaid(f"Leggi {var}")
                    linee.append(f'{ultimo_id} --> {current_id}[/"{testo_pulito}"/]:::inputOutput')
                    ultimo_id = current_id
                    
                elif tag == "output":
                    nodo_id += 1
                    current_id = f"n{nodo_id}"
                    expr = child.get("expression", "")
                    testo_pulito = pulisci_per_mermaid(f"Scrivi: {expr}")
                    linee.append(f'{ultimo_id} --> {current_id}[\\"{testo_pulito}\\"/]:::inputOutput')
                    ultimo_id = current_id
                    
                elif tag == "assign":
                    nodo_id += 1
                    current_id = f"n{nodo_id}"
                    var = child.get("variable", "")
                    expr = child.get("expression", "")
                    testo_pulito = pulisci_per_mermaid(f"{var} = {expr}")
                    linee.append(f'{ultimo_id} --> {current_id}["{testo_pulito}"]:::azione')
                    ultimo_id = current_id

                elif tag == "if":
                    nodo_id += 1
                    cond_id = f"n{nodo_id}"
                    expr = child.get("expression", "")
                    testo_pulito = pulisci_per_mermaid(f"Se {expr}")
                    linee.append(f'{ultimo_id} --> {cond_id}{{\"{testo_pulito}\"}}:::decisione')
                    
                    # Ramo Then (Vero)
                    then_element = child.find("then")
                    id_ramo_then = cond_id
                    if then_element is not None and len(then_element) > 0:
                        id_ramo_then = parsing_nodi(then_element, cond_id)
                        
                    # Ramo Else (Falso)
                    else_element = child.find("else")
                    id_ramo_else = cond_id
                    if else_element is not None and len(else_element) > 0:
                        id_ramo_else = parsing_nodi(else_element, cond_id)
                    
                    # Punto di giunzione dopo l'IF
                    nodo_id += 1
                    merge_id = f"n{nodo_id}"
                    linee.append(f'{merge_id}((" "))')
                    
                    if id_ramo_then != cond_id:
                        linee.append(f'{id_ramo_then} --> {merge_id}')
                    else:
                        linee.append(f'{cond_id} -- Vero --> {merge_id}')
                        
                    if id_ramo_else != cond_id:
                        linee.append(f'{id_ramo_else} --> {merge_id}')
                    else:
                        linee.append(f'{cond_id} -- Falso --> {merge_id}')
                        
                    ultimo_id = merge_id
            
            return ultimo_id

        # Inizio e Fine fissi
        linee.append('inizio("Inizio"):::inizioFine')
        ultimo = parsing_nodi(body, "inizio")
        linee.append(f'{ultimo} --> fine("Fine"):::inizioFine')
        
        return "\n".join(linee)
    except Exception as e:
        return None

user_input = st.text_area("Cosa deve fare l'algoritmo?", placeholder="Es: Chiedi un numero e vedi se è pari", height=120)

if st.button("🚀 GENERA E VISUALIZZA", use_container_width=True):
    if not HF_TOKEN:
        st.error("Errore: Manca l'HF_TOKEN nei Secrets di Streamlit Cloud.")
    elif user_input:
        with st.spinner("L'IA sta elaborando lo schema..."):
            try:
                prompt = f"""Genera il codice XML sorgente per Flowgorithm (.fprg) versione 4.2.
                
                REGOLE DI SINTASSI CRITICHE PER FLOWGORITHM:
                1. CONCATENAZIONE: Per unire testo e variabili usa SEMPRE l'operatore & (esempio: &quot;Testo&quot; &amp; variabile).
                2. NON USARE MAI il simbolo + per unire stringhe e variabili.
                3. OUTPUT: <output expression="&quot;Messaggio: &quot; &amp; variabile" newline="True"/>
                4. INPUT: <input variable="nomeVariabile"/>
                5. DICHIARAZIONE: <declare name="x" type="Integer" array="False" size=""/>
                6. IF: <if expression="x &gt; 0">
                
                Struttura fissa obbligatoria:
                <?xml version="1.0"?>
                <flowgorithm fileversion="4.2">
                    <attributes><attribute name="name" value="Algoritmo"/></attributes>
                    <function name="Main" type="None" variable="">
                        <parameters/>
                        <body>
                            [INSERISCI QUI IL CODICE]
                        </body>
                    </function>
                </flowgorithm>
                
                Richiesta dell'utente: {user_input}"""
                
                response = client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Sei un robot esperto di Flowgorithm. Scrivi SOLO XML puro. Usa &quot; per le virgolette e &amp; per concatenare."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                
                xml_raw = response.choices[0].message.content
                xml_data = xml_raw.replace("```xml", "").replace("```", "").strip()
                if "<?xml" in xml_data:
                    xml_data = xml_data[xml_data.find("<?xml"):]
                
                st.session_state['xml_generato'] = xml_data
                st.session_state['mermaid_code'] = converti_xml_a_mermaid(xml_data)
                st.balloons()
                
            except Exception as e:
                st.error(f"Errore tecnico: {e}")
    else:
        st.warning("Per favore, descrivi l'algoritmo.")

if st.session_state['xml_generato']:
    st.success("Algoritmo pronto!")
    
    # 📱 VISUALIZZATORE GRAFICO DIRETTAMENTE SUL TELEFONO
    if st.session_state['mermaid_code']:
        st.markdown("### 📊 Anteprima dello Schema:")
        
        # Codice HTML per renderizzare Mermaid sul telefono in modo reattivo
        html_code = f"""
        <div class="mermaid" style="display: flex; justify-content: center; background: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow-x: auto;">
        {st.session_state['mermaid_code']}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose' }});
        </script>
        """
        components.html(html_code, height=450, scrolling=True)

    st.download_button(
        label="📥 SCARICA FILE .FPRG (Per PC)",
        data=st.session_state['xml_generato'].encode('utf-8'),
        file_name="algoritmo_flow.fprg",
        mime="application/xml",
        use_container_width=True
    )
    
    with st.expander("🔍 Guarda il codice XML"):
        st.code(st.session_state['xml_generato'], language="xml")


