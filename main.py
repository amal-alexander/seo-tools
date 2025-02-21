import streamlit as st
import pandas as pd
from seo_analyzer import SEOAnalyzer
from content_analyzer import ContentAnalyzer
from sitemap_handler import SitemapHandler
from schema_handler import SchemaHandler
from utils import export_to_csv, validate_url

st.set_page_config(
    page_title="SEO Analysis Tool",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state for storing analysis results
if 'analyzed_url' not in st.session_state:
    st.session_state.analyzed_url = None
if 'meta_data' not in st.session_state:
    st.session_state.meta_data = None
if 'headers' not in st.session_state:
    st.session_state.headers = None
if 'links' not in st.session_state:
    st.session_state.links = None
if 'content_metrics' not in st.session_state:
    st.session_state.content_metrics = None
if 'ai_suggestions' not in st.session_state:
    st.session_state.ai_suggestions = None

def analyze_website(url):
    """Perform website analysis and store results in session state"""
    with st.spinner("Analyzing website..."):
        try:
            # Initialize analyzers
            seo_analyzer = SEOAnalyzer(url)
            content_analyzer = ContentAnalyzer()

            # Store analysis results in session state
            st.session_state.analyzed_url = url
            st.session_state.meta_data = seo_analyzer.get_meta_info()
            st.session_state.headers = seo_analyzer.analyze_headers()
            st.session_state.links = seo_analyzer.analyze_links()
            st.session_state.content_metrics = content_analyzer.analyze_content(
                seo_analyzer.get_main_content()
            )

            # Pre-generate AI suggestions
            st.session_state.ai_suggestions = content_analyzer.get_ai_suggestions(
                seo_analyzer.get_main_content(),
                st.session_state.meta_data
            )

            return True
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            return False

def main():
    st.title("🔍 SEO Analysis Tool")
    st.markdown("Analyze your website's SEO performance and get AI-powered suggestions")

    # Create tabs
    tabs = st.tabs([
        "🔍 On-Page SEO Analysis",
        "📝 Content Analysis",
        "🤖 AI Suggestions",
        "🗺️ Sitemap Tools",
        "📊 Schema Tools"
    ])

    # URL input in sidebar
    with st.sidebar:
        st.header("Website URL")
        url = st.text_input(
            "Enter URL to analyze:",
            placeholder="https://example.com",
            help="Enter the full URL including https:// or http://"
        )
        analyze_button = st.button("Analyze Website", type="primary")

    if url and analyze_button:
        if not validate_url(url):
            st.sidebar.error("Please enter a valid URL including https:// or http://")
            return

        if analyze_website(url):
            st.sidebar.success("Analysis completed successfully!")

    # Only show content if we have analyzed data
    if st.session_state.analyzed_url:
        # Tab 1: On-Page SEO Analysis
        with tabs[0]:
            st.header("On-Page SEO Analysis")

            with st.expander("Meta Information", expanded=True):
                st.json(st.session_state.meta_data)

            with st.expander("Header Tags Analysis", expanded=True):
                st.dataframe(pd.DataFrame(st.session_state.headers))

            with st.expander("Links Analysis", expanded=True):
                st.dataframe(pd.DataFrame(st.session_state.links))

            if st.button("Export SEO Analysis"):
                export_data = {
                    "meta": st.session_state.meta_data,
                    "headers": st.session_state.headers,
                    "links": st.session_state.links
                }
                csv_data = export_to_csv(export_data)
                st.download_button(
                    label="Download CSV",
                    data=csv_data,
                    file_name="seo_analysis.csv",
                    mime="text/csv"
                )

        # Tab 2: Content Analysis
        with tabs[1]:
            st.header("Content Analysis")

            metrics = st.session_state.content_metrics
            if metrics:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Word Count", metrics["word_count"])
                with col2:
                    st.metric("Readability Score", f"{metrics['readability_score']:.1f}")
                with col3:
                    st.metric("Keyword Density", f"{metrics['keyword_density']:.2%}")

                with st.expander("Trigram Analysis", expanded=True):
                    st.subheader("Top Trigram Phrases")
                    if metrics.get("trigram_analysis"):
                        trigram_df = pd.DataFrame(metrics["trigram_analysis"])
                        trigram_df["density"] = trigram_df["density"].apply(lambda x: f"{x:.2%}")
                        st.dataframe(trigram_df)

                with st.expander("Keyword Analysis", expanded=True):
                    st.subheader("Top Keywords")
                    st.dataframe(
                        pd.DataFrame(metrics["top_keywords"],
                        columns=["Keyword", "Count"])
                    )

        # Tab 3: AI Suggestions
        with tabs[2]:
            st.header("AI-Powered Suggestions")

            if st.session_state.ai_suggestions:
                suggestions = st.session_state.ai_suggestions

                st.subheader("Content Improvements")
                st.write(suggestions["content_improvements"])

                st.subheader("SEO Recommendations")
                st.write(suggestions["seo_recommendations"])

                st.subheader("Keyword Suggestions")
                st.write(suggestions["keyword_suggestions"])
            else:
                st.info("AI suggestions will be generated automatically when you analyze a website.")

        # Tab 4: Sitemap Tools
        with tabs[3]:
            st.header("Sitemap Tools")
            sitemap_handler = SitemapHandler()

            tab1, tab2 = st.tabs(["Validate Sitemap", "Generate Sitemap"])

            with tab1:
                sitemap_url = st.text_input(
                    "Enter sitemap URL:",
                    placeholder="https://example.com/sitemap.xml"
                )
                if sitemap_url and st.button("Validate Sitemap"):
                    with st.spinner("Validating sitemap..."):
                        result = sitemap_handler.validate_sitemap(sitemap_url)
                        if result.get("valid"):
                            st.success(f"Sitemap is valid! Found {result['total_urls']} URLs")
                            st.dataframe(pd.DataFrame(result["urls"], columns=["URLs"]))
                        else:
                            st.error(f"Sitemap validation failed: {result.get('error', '')}")
                            if "issues" in result:
                                st.dataframe(pd.DataFrame(result["issues"]))

            with tab2:
                if st.session_state.analyzed_url:
                    max_urls = st.slider("Maximum URLs to include", 10, 1000, 500)
                    if st.button("Generate Sitemap"):
                        with st.spinner("Generating sitemap..."):
                            sitemap_xml = sitemap_handler.generate_sitemap(
                                st.session_state.analyzed_url,
                                max_urls
                            )
                            st.code(sitemap_xml, language="xml")
                            st.download_button(
                                label="Download Sitemap",
                                data=sitemap_xml,
                                file_name="sitemap.xml",
                                mime="text/xml"
                            )
                else:
                    st.info("Please analyze a website first to generate its sitemap.")

        # Tab 5: Schema Tools
        with tabs[4]:
            st.header("Schema Tools")
            schema_handler = SchemaHandler()

            tab1, tab2 = st.tabs(["Validate Schema", "Generate Schema"])

            with tab1:
                if st.session_state.analyzed_url:
                    if st.button("Validate Schema"):
                        with st.spinner("Validating schema markup..."):
                            result = schema_handler.validate_schema(st.session_state.analyzed_url)
                            if result.get("valid"):
                                st.success(f"Found {result['schemas_found']} valid schema(s)")
                                for schema in result["schemas"]:
                                    st.json(schema)
                            else:
                                st.error(f"Schema validation failed: {result.get('error', '')}")
                                if "issues" in result:
                                    for issue in result["issues"]:
                                        st.warning(issue)
                else:
                    st.info("Please analyze a website first to validate its schema.")

            with tab2:
                schema_type = st.selectbox(
                    "Select Schema Type",
                    options=["Article", "Product", "LocalBusiness", "FAQ"]
                )

                # Pre-fill form with meta data if available
                schema_data = {}
                if schema_type == "Article" and st.session_state.meta_data:
                    schema_data["title"] = st.text_input(
                        "Article Title",
                        value=st.session_state.meta_data.get("title", "")
                    )
                    schema_data["description"] = st.text_area(
                        "Article Description",
                        value=st.session_state.meta_data.get("meta_description", "")
                    )
                    schema_data["author"] = st.text_input("Author Name")
                    schema_data["date"] = st.date_input("Publication Date")
                elif schema_type == "Product":
                    schema_data["name"] = st.text_input("Product Name")
                    schema_data["description"] = st.text_area("Product Description")
                    schema_data["price"] = st.number_input("Price")
                    schema_data["currency"] = st.selectbox("Currency", ["USD", "EUR", "GBP"])

                if st.button("Generate Schema"):
                    with st.spinner("Generating schema..."):
                        result = schema_handler.generate_schema(schema_type, schema_data)
                        if "error" not in result:
                            st.code(result["json_ld"], language="html")
                            st.download_button(
                                label="Download Schema",
                                data=result["json_ld"],
                                file_name="schema.json",
                                mime="application/json"
                            )
                        else:
                            st.error(result["error"])
    else:
        # Show welcome message when no URL is analyzed
        st.info("👈 Please enter a URL in the sidebar to begin the analysis")

if __name__ == "__main__":
    import os
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'
    os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
    os.environ['STREAMLIT_SERVER_ENABLE_CORS'] = 'false'
    main()