# imports with plotly and streamlit as a base
import streamlit as st
import pandas as pd
import plotly.express as px


# PAGE SETUP:
# configures the browser tab and sets the app to use the full width of the screen
st.set_page_config(page_title="Irish Placenames", layout="wide")
st.title("Irish Placenames: Linguistic & Spatial Analysis")


# DATA LOADING:
# The @st.cache_data line ensures these files are only loaded once when the app starts, keeping the app incredibly fast as users click around
@st.cache_data
def load_data():
    map_df = pd.read_csv("map_data.csv")
    tfidf_df = pd.read_csv("tfidf_results.csv")
    ppmi_df = pd.read_csv("ppmi_results.csv")
    pca_df = pd.read_csv("PCA_results.csv")
    
    
    return map_df, tfidf_df, ppmi_df, pca_df

# loads the data into memory
map_df, tfidf_df, ppmi_df, pca_df = load_data()

# SIDEBAR NAVIGATION:
# creates a menu on the left side of the screen for navigation between graphs/maps/charts
st.sidebar.header("Menu")
page = st.sidebar.radio(
    "Select Analysis Tool:", 
    ["Home & Overview","Geospatial Map", "TF-IDF Signatures", "PPMI Heatmaps", "3D PCA Clusters", "References & Links"]
)

# PAGE LOGIC & VISUALIZATIONS:

if page == "Home & Overview":
    st.header("Mapping the Linguistic Landscape of Ireland")
    st.markdown("""
    Welcome to the Irish Placenames (Logainmneacha) Analysis tool. This application uses Natural Language Processing (NLP) and geospatial data to uncover the hidden environmental, cultural, and historical patterns encoded in over 67,000 Irish townlands and geographical features.
    
    ### How to Use This App
    Use the sidebar on the left to navigate through four distinct analytical modules:
    
    *   **Geospatial Map:** An interactive, grammatically aware search engine. Type a geographical term (like *coill* for wood) to see its exact distribution across the island.
    *   **TF-IDF Signatures:** Discover the unique "linguistic DNA" of each county. This module reveals which words define a specific region compared to the rest of the country.
    *   **PPMI Heatmaps:** Explore cultural naming conventions. This tool measures the statistical bond between words (e.g., discovering which animals are historically associated with which terrains).
    *   **3D PCA Clusters:** A machine-learning visualization that groups placenames based on their structural and semantic similarities.
    
    *Data sourced from Logainm.ie / The Placenames Database of Ireland.*
    """)

if page == "Geospatial Map":
    st.subheader("Geospatial Distribution of Irish Toponyms")
    st.markdown("Visualize the physical locations of specific Irish placename features.")
    
    
    search_term = st.text_input("Enter a term to map (e.g., 'coill'):")
    filtered_map = map_df[map_df['Name_GA'].str.contains(search_term, case=False, na=False)]
    
    
    fig = px.scatter_map(filtered_map, lat="Latitude", lon="Longitude", hover_name="Name_GA", zoom=5)
    fig.update_layout(map_style="carto-positron")
    
    # sets chart to adequate width in UI
    st.plotly_chart(fig, width="stretch")

elif page == "TF-IDF Signatures":
    st.subheader("County-Level Linguistic Signatures")
    
    selected_county = st.selectbox("Choose a County", tfidf_df["County"].unique())
    filtered_tfidf = tfidf_df[tfidf_df["County"] == selected_county]
    st.dataframe(filtered_tfidf)

elif page == "PPMI Heatmaps":
    st.subheader("Collocation Heatmaps (Shifted PPMI)")
    
    st.info("""
    **How to read this heatmap:** 
    Pointwise Mutual Information (PMI) measures the strength of the bond between two words. A dark color means that when Word A appears, Word B is highly likely to be right next to it.
    
    **Note on Rare Events:** PMI mathematically favors rare combinations. For example, if you see a massive score for *sionnaigh* (fox) and *ruball* (tail), it is because *ruball* is incredibly rare in Irish placenames—but when it does appear, it is almost exclusively chained to the word *sionnaigh*. 
    
    Always cross-reference the heatmap with the **Statistical Validation Table** below to see if a dark square represents a widespread cultural naming convention (high co-occurrence count) or a highly localized historical quirk (low co-occurrence count).
    """)
    
    # theme terminology was gathered from logainm's own guide found at ... https://www.logainm.ie/en/resources/education 
    themes = {
        "Arboreal": ['coill', 'doire', 'crann','fiodh', 'dair', 'draighean', 'sceach', 'ros'],
        "Water": ['loch', 'abhainn', 'tobar', 'áth', 'bá', 'bun', 'glas', 'inis', 'cuan', 'eas'],
        "Geography": ['cnoc', 'sliabh', 'gleann', 'carraig', 'droim', 'móin'],
        "Fauna": ['bó', 'sionnaigh', 'sionnach', 'fianna', 'fia', 'broc', 'mbroc', 'capall', 'gcapall', 'cait', 'cat', 'bradáin', 'bradán']
    }
    
    selected_theme = st.selectbox("Select Theme:", list(themes.keys()))
    target_words = themes[selected_theme]
    
    # If Fauna, search w2. Otherwise, search w1. 
    # Fauna is predominantly found in the second part of placenames because it denotes ownership (e.g. páirc bhfianna = park of the deer)
    if selected_theme == "Fauna":
        filtered_ppmi = ppmi_df[ppmi_df['w2'].isin(target_words)]
        # Group by w2 to get the top features for each animal
        top_n = filtered_ppmi.sort_values('sppmi', ascending=False).groupby('w2').head(15)
    else:
        filtered_ppmi = ppmi_df[ppmi_df['w1'].isin(target_words)]
        top_n = filtered_ppmi.sort_values('sppmi', ascending=False).groupby('w1').head(15)
    
    # Pivot the dataframe
    # If Fauna, flip the axes so Animals are on the Y-axis and Features on the X-axis
    if selected_theme == "Fauna":
        pivot_df = top_n.pivot(index='w2', columns='w1', values='sppmi').fillna(0)
        color_scale = "Oranges"
    else:
        pivot_df = top_n.pivot(index='w1', columns='w2', values='sppmi').fillna(0)
        color_scale = "Greens" if selected_theme == "Arboreal" else "Blues"
    
    # Draw the heatmap and add text_auto to render the numbers inside the heatmap squares
    fig = px.imshow(pivot_df, color_continuous_scale=color_scale, aspect="auto", text_auto=".1f")
    st.plotly_chart(fig, width="stretch")

    # STATISTICAL VALIDATION TABLE
    # Displays LLR scores for each term collocation finding, providing statistical significance to results
    st.markdown("---")
    st.markdown("### Statistical Validation (Log-Likelihood Ratio)")
    st.markdown("The collocations above have been rigorously tested against a null hypothesis. An LLR score > **10.83** indicates **99.9% statistical significance**.")

    # Clean up the column names for public viewing
    display_stats = top_n[['w1', 'w2', 'count_w1_w2', 'sppmi', 'LLR_Score']].sort_values(by='LLR_Score', ascending=False)
    display_stats.columns = ["Target Word (w1)", "Context Word (w2)", "Total Co-occurrences", "SPPMI Score", "LLR Score"]
    
    # displays results as an interactive dataframe
    st.dataframe(display_stats, width="stretch")

elif page == "3D PCA Clusters":
    st.subheader("3D Semantic Clustering (TF-IDF PCA)")
    
    fig = px.scatter_3d(pca_df, x='PC1', y='PC2', z='PC3', color='County', hover_name='Name_GA')
    fig.update_traces(marker=dict(size=4))
    st.plotly_chart(fig, width="stretch")

elif page == "References & Links":
    st.header("References & Important Links")
    st.markdown("Here are the primary data sources, methodologies, and tools used to build this analysis.")
    
    st.markdown("""
    ### Main Data Sources
    *   **The Placenames Database of Ireland (Logainm):** Comprehensive database of Irish toponymy and geographical features. [Visit logainm.ie](https://www.logainm.ie/)
    *   **National Corpus of Irish (NCI):** A baseline reference for standard everyday Irish language collocations and word frequencies. [Visit Gaois / NCI](https://www.gaois.ie/en/corpora/)
    
    ---
    
    ### Methodology & Papers
    *    Brenndoerfer, M. (2025a, March 24). Co-occurrence matrices: Distributional semantics in NLP. Michael Brenndoerfer. Mbrenndoerfer.Com. https://mbrenndoerfer.com/writing/co-occurrence-matrices-distributional-semantics-nlp#co-occurrence-matrices
    *    Brenndoerfer, M. (2025b, March 31). Pointwise mutual information: Word associations in NLP. Michael Brenndoerfer. Mbrenndoerfer.Com. https://mbrenndoerfer.com/writing/pointwise-mutual-information-word-associations-nlp#setup-and-data
    *    Church, K. W., & Hanks, P. (1990). Word association norms, mutual information, and lexicography. Computational Linguistics, *16*(1), 22–29. https://aclanthology.org/J90-1003/
    *    Fiontar & Scoil na Gaeilge (DCU). (2026). Educational resources. Logainm.Ie. https://www.logainm.ie/en/resources/educationForas na Gaeilge. (2025). New english-Irish dictionary from Foras na Gaeilge. In Focloir.ie. https://www.focloir.ie/en
    *    fr4nk.xyz. (2023). Understanding pointwise mutual information: A beginner’s guide. In Medium. https://medium.com/@fr4nk/understanding-pointwise-mutual-information-a-beginners-guide-dcfed0f83ff2
    *    Jones, A. (2021, November). A multi-page interactive dashboard with streamlit and plotly. TDS Archive. Medium. https://medium.com/data-science/a-multi-page-interactive-dashboard-with-streamlit-and-plotly-c3182443871a
    *    Suri, M. (2022). A dummy’s guide to Word2Vec. In Medium. https://medium.com/@manansuri/a-dummys-guide-to-word2vec-456444f3c673
  
    ---
    
    ### Technologies & Frameworks
    *   **[Streamlit Community Cloud](https://streamlit.io/):** Used for hosting this interactive web application.
    *   **[Plotly for Python](https://plotly.com/python/):** Used for rendering all interactive maps and models.
    *   **[Apache Spark (PySpark)](https://spark.apache.org/):** Used for the process of Irish language tokenization, NLP parsing, and K-Means clustering.
    *   **[Spark NLP Irish lemmatizer](https://sparknlp.org/2020/07/29/lemma_ga.html):** Used in the pre-processing of data. 

    --- 
    ### Author Details
    *    This work is part of an undergraduate research paper conducted by Liam T. O'Brien on behalf of the [London Interdisciplinary School](https://www.lis.ac.uk/).
    *    Access the web-app code directly on my [github](https://github.com/liamthobrien). 
    """)
