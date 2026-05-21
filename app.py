import streamlit as st
from huggingface_hub import InferenceClient

# --- CONFIGURAZIONE ---
# Usa st.secrets["HF_TOKEN"] se carichi su Streamlit Cloud per sicurezza
HF_TOKEN = "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" 

client = InferenceClient(model="Qwen/Qwen2.5-72B-Instruct", token=HF_TOKEN)

# Ottimizzazione per Mobile: layout "centered" e titolo pulito
st.set_page_config(page_title="FlowAI Mobile", page_icon="📱", layout="centered")

st.title("📱 FlowAI Mobile")
st.markdown("Genera i tuoi schemi **Flowgorithm** in un tocco.")

if 'xml_generato' not in st.session_state:
    st.session_state['xml_generato'] = None

# Area di testo con altezza ottimizzata per il pollice
user_input = st.text_area("Descrivi l'algoritmo:", placeholder="Es: Media di 3 voti", height=150)

# Pulsante grande e visibile (use_container_width=True lo rende perfetto su mobile)
if st.button("🚀 GENERA SCHEMA", use_container_width=True):
    if user_input:
        with st.spinner("Lavoro per te..."):
            try:
                prompt = f"""Genera XML per Flowgorithm (.fprg) v4.2.
                REGOLE:
                1. CONCATENAZIONE: usa & (esempio: &quot;Voto: &quot; &amp; v)
                2. OUTPUT: <output expression="&quot;Risultato: &quot; &amp; var"/>
                3. Struttura: <flowgorithm fileversion="4.2"> con <function name="Main"> e <body>.
                Richiesta: {user_input}"""
                
                response = client.chat_completion(
                    messages=[
                        {"role": "system", "content": "Sei un esperto Flowgorithm. Rispondi solo con XML puro, niente testo extra."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=2000
                )
                
                xml_raw = response.choices[0].message.content
                xml_data = xml_raw.replace("```xml", "").replace("```", "").strip()
                if "<?xml" in xml_data:
                    xml_data = xml_data[xml_data.find("<?xml"):]
                
                st.session_state['xml_generato'] = xml_data
                st.balloons() # Effetto grafico carino al completamento
                
            except Exception as e:
                st.error(f"Errore: {e}")

if st.session_state['xml_generato']:
    st.success("Algoritmo pronto!")
    
    # Download Button grande per il pollice
    st.download_button(
        label="📥 SCARICA FILE .FPRG",
        data=st.session_state['xml_generato'].encode('utf-8'),
        file_name="algoritmo_mobile.fprg",
        mime="application/xml",
        use_container_width=True
    )
    
    with st.expander("🔍 Guarda l'anteprima"):
        st.code(st.session_state['xml_generato'], language="xml")

# --- SEZIONE MONETIZZAZIONE (Opzionale) ---
st.divider()
st.markdown("❤️ **Ti piace l'app?**")
st.link_button("☕ Offrimi un caffè", "https://www.buymeacoffee.com/tuo_nome", use_container_width=True)
