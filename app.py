
import streamlit as st
from huggingface_hub import InferenceClient

# --- CONFIGURAZIONE ---
if "HF_TOKEN" in st.secrets:
    HF_TOKEN = st.secrets["HF_TOKEN"]
else:
    HF_TOKEN = "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"

client = InferenceClient(model="Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN)

# Ottimizzazione per Mobile
st.set_page_config(page_title="FlowAI Mobile", page_icon="📱", layout="centered")

st.title("📱 FlowAI Mobile")
st.markdown("Genera i tuoi schemi **Flowgorithm** in un tocco.")

if 'xml_generato' not in st.session_state:
    st.session_state['xml_generato'] = None

user_input = st.text_area("Cosa deve fare l'algoritmo?", placeholder="Es: Chiedi un numero e vedi se è pari", height=150)

if st.button("🚀 GENERA SCHEMA", use_container_width=True):
    if user_input:
        with st.spinner("L'IA sta disegnando lo schema..."):
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
                
                # Pulizia codice
                xml_data = xml_raw.replace("```xml", "").replace("```", "").strip()
                if "<?xml" in xml_data:
                    xml_data = xml_data[xml_data.find("<?xml"):]
                
                st.session_state['xml_generato'] = xml_data
                st.balloons() # Animazione!
                
            except Exception as e:
                st.error(f"Errore tecnico: {e}")
    else:
        st.warning("Per favore, descrivi l'algoritmo.")

if st.session_state['xml_generato']:
    st.success("Algoritmo generato con successo!")
    
    st.download_button(
        label="📥 SCARICA FILE .FPRG",
        data=st.session_state['xml_generato'].encode('utf-8'),
        file_name="algoritmo_flow.fprg",
        mime="application/xml",
        use_container_width=True
    )
    
    with st.expander("🔍 Guarda l'anteprima"):
        st.code(st.session_state['xml_generato'], language="xml")

```
