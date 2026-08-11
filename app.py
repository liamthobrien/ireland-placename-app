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
st.sidebar.header("Navigation")
page = st.sidebar.radio(
    "Select Analysis Module:", 
    ["Geospatial Map", "TF-IDF Signatures", "PPMI Heatmaps", "3D PCA Clusters"]
)


# PAGE LOGIC & VISUALIZATIONS:

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

    # theme terminology was gathered from logainm's own guide found at ...
    themes = {
        "Arboreal": ['coill', 'doire', 'crann', 'cuileann', 'beith', 'bile'],
        "Water": ['loch', 'abhainn', 'tobar', 'áth', 'sruth', 'linn'],
        "Geography": ['cnoc', 'sliabh', 'gleann', 'carraig', 'droim', 'móin']
    }
    
    selected_theme = st.selectbox("Select Theme:", list(themes.keys()))
    target_words = themes[selected_theme]
    
    # filter down to the target words
    filtered_ppmi = ppmi_df[ppmi_df['w1'].isin(target_words)]
    
    # filters for the top 15 highest-scoring pairs per word to prevent horizontal crowding
    top_n = filtered_ppmi.sort_values('sppmi', ascending=False).groupby('w1').head(15)
    
    # pivot the smaller dataset
    pivot_df = top_n.pivot(index='w1', columns='w2', values='sppmi').fillna(0)
    
    color_scale = "Greens" if selected_theme == "Arboreal" else "Blues"
    
    # adds text_auto to render the numbers inside the heatmap squares
    fig = px.imshow(pivot_df, color_continuous_scale=color_scale, aspect="auto", text_auto=".1f")
    st.plotly_chart(fig, width="stretch")

    # STATISTICAL TEST TABLE
    # To validate the findings as statistically significant and not random chance that these placename features collocate...
    st.markdown("---")
    st.markdown("### Statistical Validation (Log-Likelihood Ratio)")
    st.markdown("The collocations above have been rigorously tested against a null hypothesis. An LLR score > **10.83** indicates **99.9% statistical significance**.")
    
    # Clean up the column names for public viewing
    display_stats = top_n[['w1', 'w2', 'count_w1_w2', 'sppmi', 'LLR_Score']].sort_values(by='LLR_Score', ascending=False)
    display_stats.columns = ["Target Word (w1)", "Context Word (w2)", "Total Co-occurrences", "SPPMI Score", "LLR Score"]
    
    # displays results as an interactive dataframe
    st.dataframe(display_stats, width=None)

elif page == "3D PCA Clusters":
    st.subheader("3D Semantic Clustering (TF-IDF PCA)")
    
    fig = px.scatter_3d(pca_df, x='PC1', y='PC2', z='PC3', color='County', hover_name='Name_GA')
    fig.update_traces(marker=dict(size=4))
    st.plotly_chart(fig, width="stretch")
