import streamlit as st
from huggingface_hub import InferenceClient
import xml.etree.ElementTree as ET
import re

# --- CONFIGURAZIONE TOKEN IN SICUREZZA ---
# Abbiamo rimosso completamente ogni token scritto in chiaro nel codice.
# In questo modo GitHub non bloccherà più il caricamento (commit)!
# 1. L'app cerca nei Secrets di Streamlit Cloud (per quando sarai online)
# 2. Se sei in locale, ti chiederà di inserire il tuo token nel box a sinistra.
HF_TOKEN = None

if "HF_TOKEN" in st.secrets:
    HF_TOKEN = st.secrets["HF_TOKEN"]

st.set_page_config(page_title="FlowAI - Graphic Preview", page_icon="🎨", layout="wide")
st.title("FlowAI - Anteprima Grafica Premium 🎨")
st.markdown("Genera l'algoritmo e osserva il diagramma a blocchi interattivo con i colori ufficiali di **Flowgorithm**.")

if 'xml_generato' not in st.session_state:
    st.session_state['xml_generato'] = None

# Layout a due colonne: a sinistra i controlli, a destra la visualizzazione grafica
col_controllo, col_grafica = st.columns([1, 2])

with col_controllo:
    st.subheader("⚙️ Configurazione")
    
    # Gestione del Token Sicuro senza fallback cablati nel codice
    if not HF_TOKEN:
        HF_TOKEN_ATTIVO = st.text_input(
            "Chiave Accesso Hugging Face (HF_TOKEN)", 
            type="password",
            placeholder="Incolla qui il tuo token hf_...",
            help="Crea un token gratuito su huggingface.co. Questo input è sicuro e non verrà salvato su GitHub!"
        )
    else:
        HF_TOKEN_ATTIVO = HF_TOKEN
        st.success("🔑 Token caricato in sicurezza dai Secrets di Streamlit!")

    user_input = st.text_area("Cosa deve fare l'algoritmo da disegnare?", placeholder="Es: Chiedi un numero, se è pari stampa 'Ok' altrimenti chiedilo di nuovo...", height=150)
    st.caption("L'IA utilizzerà le regole sintattiche calibrate per generare un file perfettamente digeribile da Flowgorithm desktop.")
    
    genera_btn = st.button("🚀 GENERA E DISEGNA", use_container_width=True)

# Parser XML -> Codice Mermaid.js per il rendering dei blocchi
def xml_to_mermaid(xml_content):
    try:
        # Pulisce l'XML da eventuali residui o spazi bianchi
        xml_content = re.sub(r'^\s*<\?xml.*\?>', '', xml_content).strip()
        root = ET.fromstring(xml_content)
    except Exception as e:
        return f"graph TD\n    error[Errore di Parsing XML: {str(e)}]"

    lines = ["flowchart TD"]
    
    # Classi CSS personalizzate con i colori ufficiali di Flowgorithm
    lines.append("    classDef inizioFine fill:#f3e5f5,stroke:#af7ac5,stroke-width:2px,color:#333,rx:20px,ry:20px;")
    lines.append("    classDef declareAssign fill:#fef9e7,stroke:#f5b041,stroke-width:2px,color:#333;")
    lines.append("    classDef inputBlock fill:#ebf5fb,stroke:#5dade2,stroke-width:2px,color:#333;")
    lines.append("    classDef outputBlock fill:#e8f8f5,stroke:#48c9b0,stroke-width:2px,color:#333;")
    lines.append("    classDef conditionBlock fill:#fdf2e9,stroke:#e59866,stroke-width:2px,color:#333;")
    
    node_counter = 0

    def get_node_id():
        nonlocal node_counter
        node_counter += 1
        return f"node_{node_counter}"

    def escape_text(text):
        if not text:
            return ""
        # Pulisce le virgolette XML per evitare di rompere Mermaid
        return text.replace('"', '&quot;').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # Trova il body della funzione Main
    main_body = root.find(".//function[@name='Main']/body")
    if main_body is None:
        return "graph TD\n    error[Funzione Main non trovata]"

    start_id = "start_node"
    end_id = "end_node"
    
    lines.append(f"    {start_id}([\"Inizio\"]) ::: inizioFine")

    def parse_element_list(elements, parent_id):
        current_parent = parent_id
        for el in elements:
            tag = el.tag
            node_id = get_node_id()

            if tag == 'declare':
                var_name = escape_text(el.get('name'))
                var_type = escape_text(el.get('type'))
                lines.append(f"    {node_id}[\"Dichiara {var_name}: {var_type}\"] ::: declareAssign")
                lines.append(f"    {current_parent} --> {node_id}")
                current_parent = node_id

            elif tag == 'assign':
                var_name = escape_text(el.get('variable'))
                expr = escape_text(el.get('expression'))
                lines.append(f"    {node_id}[\"{var_name} = {expr}\"] ::: declareAssign")
                lines.append(f"    {current_parent} --> {node_id}")
                current_parent = node_id

            elif tag == 'input':
                var_name = escape_text(el.get('variable'))
                lines.append(f"    {node_id}[/\"Input: {var_name}\"/] ::: inputBlock")
                lines.append(f"    {current_parent} --> {node_id}")
                current_parent = node_id

            elif tag == 'output':
                expr = escape_text(el.get('expression'))
                lines.append(f"    {node_id}[\\\"Output: {expr}\\\"] ::: outputBlock")
                lines.append(f"    {current_parent} --> {node_id}")
                current_parent = node_id

            elif tag == 'if':
                expr = escape_text(el.get('expression'))
                lines.append(f"    {node_id}{{\"{expr}\"}} ::: conditionBlock")
                lines.append(f"    {current_parent} --> {node_id}")
                
                then_branch = el.find('then')
                else_branch = el.find('else')
                
                join_id = get_node_id()
                lines.append(f"    {join_id}((\" \")) ::: conditionBlock")

                # Elaborazione ramo VERO (then)
                if then_branch is not None and len(then_branch) > 0:
                    last_then = parse_element_list(then_branch, f"{node_id} -- Vero -->")
                    if last_then != f"{node_id} -- Vero -->":
                        lines.append(f"    {last_then} --> {join_id}")
                    else:
                        lines.append(f"    {node_id} -- Vero --> {join_id}")
                else:
                    lines.append(f"    {node_id} -- Vero --> {join_id}")

                # Elaborazione ramo FALSO (else)
                if else_branch is not None and len(else_branch) > 0:
                    last_else = parse_element_list(else_branch, f"{node_id} -- Falso -->")
                    if last_else != f"{node_id} -- Falso -->":
                        lines.append(f"    {last_else} --> {join_id}")
                    else:
                        lines.append(f"    {node_id} -- Falso --> {join_id}")
                else:
                    lines.append(f"    {node_id} -- Falso --> {join_id}")

                current_parent = join_id

            elif tag == 'while':
                expr = escape_text(el.get('expression'))
                # Nodo di ingresso/controllo ciclo
                lines.append(f"    {node_id}{{\"Mentre {expr}\"}} ::: conditionBlock")
                lines.append(f"    {current_parent} --> {node_id}")
                
                # Sotto-elementi interni al while
                internal_children = list(el)
                if internal_children:
                    last_internal = parse_element_list(internal_children, f"{node_id} -- Vero -->")
                    if last_internal != f"{node_id} -- Vero -->":
                        # Freccia che torna su all'inizio della condizione
                        lines.append(f"    {last_internal} --> {node_id}")
                
                # Creiamo un nodo finto per la continuazione dopo il ciclo
                exit_id = get_node_id()
                lines.append(f"    {exit_id}((\" \")) ::: conditionBlock")
                lines.append(f"    {node_id} -- Falso --> {exit_id}")
                current_parent = exit_id

            elif tag == 'for':
                var_name = escape_text(el.get('variable'))
                start = escape_text(el.get('start'))
                end = escape_text(el.get('end'))
                direction = escape_text(el.get('direction'))
                step = escape_text(el.get('step'))
                
                dir_label = "Incr" if direction == "inc" else "Decr"
                loop_desc = f"Per {var_name} = {start} a {end} (Passo {step} {dir_label})"
                
                lines.append(f"    {node_id}{{\"{loop_desc}\"}} ::: conditionBlock")
                lines.append(f"    {current_parent} --> {node_id}")
                
                internal_children = list(el)
                if internal_children:
                    last_internal = parse_element_list(internal_children, f"{node_id} -- Ripeti -->")
                    if last_internal != f"{node_id} -- Ripeti -->":
                        lines.append(f"    {last_internal} --> {node_id}")
                
                exit_id = get_node_id()
                lines.append(f"    {exit_id}((\" \")) ::: conditionBlock")
                lines.append(f"    {node_id} -- Fine --> {exit_id}")
                current_parent = exit_id

        return current_parent

    last_node = parse_element_list(main_body, start_id)
    lines.append(f"    {last_node} --> {end_id}")
    lines.append(f"    {end_id}([\"Fine\"]) ::: inizioFine")
    
    return "\n".join(lines)

# Esecuzione generazione
if genera_btn:
    if not HF_TOKEN_ATTIVO:
        st.error("🔑 Errore: Inserisci il tuo token Hugging Face nel campo a sinistra prima di generare!")
    elif user_input:
        with st.spinner("L'IA sta elaborando lo schema..."):
            try:
                # Creazione del client con il token recuperato in modo sicuro
                client = InferenceClient(model="Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN_ATTIVO)
                
                prompt = f"""Genera il codice XML sorgente nativo per un file Flowgorithm (.fprg) versione 4.2.
                
                REGOLE DI SINTASSI DI FERRO PER EVITARE CRASH E SCHEMI VUOTI:
                
                1. DICHIARAZIONE PREVENTIVA: Ogni variabile DEVE avere un tag <declare> all'inizio del Main.
                2. NO TAG BODY NEI CICLI: Non usare MAI il tag <body> dentro <while> o <for>. Inserisci i comandi direttamente.
                3. CONCATENAZIONE: Usa solo l'operatore & (es: &quot;Testo&quot; &amp; var).
                4. DIVISIONE: Usa '/' per la divisione (anche intera tra Integer).
                5. OPERATORI: Usa 'mod', 'and', 'or', 'not'.
                6. STRINGHE: Usa Char(stringa, indice) e Len(stringa).
                7. IF: Solo tag <then> ed <else> dentro <if expression="...">.
                
                REGOLE SPECIFICHE PER I CICLI (TASSATIVE):
                12. RISPETTO DEL CICLO: Se chiesto "While", usa <while>. Se chiesto "For", usa <for>.
                
                13. SINTASSI WHILE (SENZA BODY):
                    <declare name="i" type="Integer" array="False" size=""/>
                    <assign variable="i" expression="0"/> 
                    <while expression="i &lt; 10">
                        <output expression="i" newline="True"/>
                        <assign variable="i" expression="i + 1"/>
                    </while>

                14. SINTASSI FOR (SENZA BODY):
                    <declare name="i" type="Integer" array="False" size=""/>
                    <for variable="i" start="1" end="10" direction="inc" step="1">
                        <output expression="i" newline="True"/>
                    </for>

                15. INIZIALIZZAZIONE CRITICA (PER EVITARE SCHEMI VUOTI):
                    Prima di ogni ciclo <while>, la variabile usata nella condizione DEVE ricevere un valore tramite <assign> o <input>. 
                    Flowgorithm non visualizza i blocchi se la variabile di controllo del While è nulla all'ingresso.

                Usa questa struttura fissa (niente spiegazioni o markdown):
                <?xml version="1.0"?>
                <flowgorithm fileversion="4.2">
                    <attributes>
                        <attribute name="name" value="Algoritmo"/>
                    </attributes>
                    <function name="Main" type="None" variable="">
                        <parameters/>
                        <body>
                            [IL TUO CODICE QUI]
                        </body>
                    </function>
                </flowgorithm>
                
                Richiesta: {user_input}"""
                
                response = client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Sei un compilatore XML per Flowgorithm. Generi solo XML puro, senza markdown o testo."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                
                xml_raw = response.choices[0].message.content
                xml_data = xml_raw.replace("```xml", "").replace("```", "").strip()
                if "<?xml" in xml_data:
                    xml_data = xml_data[xml_data.find("<?xml"):]
                
                st.session_state['xml_generato'] = xml_data
                st.success("Algoritmo generato correttamente!")
                
            except Exception as e:
                st.error(f"Errore tecnico durante la generazione: {e}")
    else:
        st.warning("Scrivi la logica da testare prima!")

# Visualizzazione della grafica e download
with col_grafica:
    st.subheader("📊 Rendering Diagramma a Blocchi")
    
    if st.session_state['xml_generato']:
        # Generiamo il codice Mermaid a partire dall'XML
        mermaid_code = xml_to_mermaid(st.session_state['xml_generato'])
        
        # Componente HTML pulito con Mermaid.js caricato da CDN e configurazione di stile custom
        html_code = f"""
        <div id="mermaid-container" style="background-color: #fcfcfc; padding: 20px; border-radius: 12px; border: 1px solid #eaeaea; box-shadow: 0 4px 12px rgba(0,0,0,0.05); overflow-x: auto; text-align: center;">
            <pre class="mermaid" style="background: transparent; border: none; font-family: sans-serif;">
                {mermaid_code}
            </pre>
        </div>
        <script type="module">
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
            mermaid.initialize({{ 
                startOnLoad: true,
                theme: 'neutral',
                flowchart: {{
                    useMaxWidth: false,
                    htmlLabels: true,
                    curve: 'basis'
                }}
            }});
        </script>
        """
        st.components.v1.html(html_code, height=600, scrolling=True)
        
        # Opzioni aggiuntive (Scarica file)
        st.download_button(
            label="📥 SCARICA FILE .FPRG PER FLOWGORITHM DESKTOP",
            data=st.session_state['xml_generato'].encode('utf-8'),
            file_name="algoritmo.fprg",
            mime="application/xml",
            use_container_width=True
        )
    else:
        st.info("Genera un algoritmo usando il pannello di sinistra per osservare la visualizzazione dei blocchi interattivi.")
