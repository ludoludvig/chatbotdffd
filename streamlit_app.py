import streamlit as st
import pandas as pd
import openai

# === CONFIGURAZIONE ===
openai.api_key = st.secrets["OPENAI_API_KEY"]  # Imposta la tua API key su Streamlit secrets

# Dizionario GWP semplificato
GWP_DB = {
    "aluminium": 9.16,
    "stainless steel": 6.15,
    "carbon fiber": 20.0,
    "plywood": 0.35,
    "teak": 0.21,
    "PVC": 2.9,
    "brass": 7.2
}

# === FUNZIONE GPT ===
def identify_material(description):
    prompt = f"""
You are an expert in sustainable naval architecture.
Given the following component description: "{description}", identify the most likely standard material used, choosing from this list:
- aluminium
- stainless steel
- carbon fiber
- plywood
- teak
- PVC
- brass
Only return the material name.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        material = response['choices'][0]['message']['content'].strip().lower()
        return material if material in GWP_DB else "unknown"
    except Exception as e:
        return "error"

# === STREAMLIT UI ===
st.title("Yacht Lightship GWP Estimator (AI-based)")

uploaded_file = st.file_uploader("Upload your Lightship Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("## Preview of uploaded file:", df.head())

    if "Description" not in df.columns or "Weight (kg)" not in df.columns:
        st.error("The Excel must contain at least 'Description' and 'Weight (kg)' columns.")
    else:
        with st.spinner("Identifying materials using AI..."):
            df["Identified Material"] = df["Description"].apply(identify_material)
            df["GWP per kg"] = df["Identified Material"].apply(lambda x: GWP_DB.get(x, 0))
            df["GWP (kg CO2eq)"] = df["Weight (kg)"] * df["GWP per kg"]

            total_weight_ton = df["Weight (kg)"].sum() / 1000
            total_gwp_ton = df["GWP (kg CO2eq)"].sum() / 1000
            specific_gwp = total_gwp_ton / total_weight_ton if total_weight_ton else 0

        st.success("Analysis complete.")
        st.write("## Results:")
        st.dataframe(df)

        st.markdown(f"**Total weight:** {total_weight_ton:.2f} t")
        st.markdown(f"**Total GWP:** {total_gwp_ton:.2f} t CO2eq")
        st.markdown(f"**Specific GWP:** {specific_gwp:.2f} t CO2eq/t yacht")

        # Download
        st.download_button("Download Results as Excel", df.to_excel(index=False), "gwp_results.xlsx")
