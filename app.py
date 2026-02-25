import requests
import pypdf
import streamlit as st
from dotenv import load_dotenv
from google.api_core.exceptions import ResourceExhausted

from gemini_client import DEFAULT_MODEL, GeminiClient, list_available_models
from logger import generate_session_id, log_event, setup_logger
from summarizer import summarize_pdf, summarize_url

load_dotenv()

st.set_page_config(
    page_title="Files AI - Agnilonda Pakou",
    page_icon="📄",
    layout="centered",
)

if "session_id" not in st.session_state:
    st.session_state.session_id = generate_session_id()

if "logger" not in st.session_state:
    st.session_state.logger = setup_logger()

if "gemini" not in st.session_state:
    try:
        st.session_state.gemini = GeminiClient()
        st.session_state.available_models = list_available_models()
        st.session_state.selected_model = DEFAULT_MODEL
        log_event(
            st.session_state.logger,
            "INFO",
            "app_started",
            st.session_state.session_id,
            None,
            None,
            st.session_state.gemini.model_name,
        )
    except ValueError as exc:
        st.session_state.gemini = None
        st.session_state.available_models = []
        st.session_state.selected_model = DEFAULT_MODEL
        st.error(f"Configuration error: {exc}")

with st.sidebar:
    st.title("Agnilonda Pakou")
    st.caption("Your AI summarization assistant")
    st.divider()

    st.markdown("**Model**")
    model_options = st.session_state.available_models or [DEFAULT_MODEL]
    default_index = (
        model_options.index(st.session_state.selected_model)
        if st.session_state.selected_model in model_options
        else 0
    )
    chosen_model = st.selectbox(
        "Gemini model",
        options=model_options,
        index=default_index,
        label_visibility="collapsed",
    )
    if chosen_model != st.session_state.selected_model:
        try:
            st.session_state.gemini = GeminiClient(model_name=chosen_model)
            st.session_state.selected_model = chosen_model
        except Exception as exc:
            st.error(f"Could not load model '{chosen_model}': {exc}")

    st.divider()
    st.markdown("**How to use**")
    st.markdown(
        "- **URL tab** - paste any public article link and click *Summarize URL*\n"
        "- **PDF tab** - upload a text-based PDF and click *Summarize PDF*"
    )
    st.divider()

    st.markdown("**Session ID**")
    st.code(st.session_state.session_id, language=None)
    st.caption("Events are logged to `assistant_log.json`")

st.title("Files AI")
st.markdown("Summarize web articles and PDF documents with **Agnilonda Pakou**.")

if st.session_state.gemini is None:
    st.warning(
        "The assistant is not ready. Please set `GOOGLE_API_KEY` in your "
        "`.env` file and restart the app."
    )
    st.stop()

tab_url, tab_pdf = st.tabs(["🔗 Summarize a URL", "📄 Summarize a PDF"])

with tab_url:
    st.markdown(
        "Paste a link to any publicly accessible web article below. "
        "Agnilonda Pakou will fetch, read, and summarize it for you."
    )

    url_input = st.text_input(
        "Article URL",
        placeholder="https://example.com/article",
        label_visibility="collapsed",
    )

    if st.button("Summarize URL", type="primary", use_container_width=True, key="btn_url"):
        if not url_input.strip():
            st.warning("Please enter a URL before clicking Summarize.")
        else:
            with st.spinner("Fetching and summarizing - this may take a moment…"):
                try:
                    summary = summarize_url(
                        url_input.strip(),
                        st.session_state.gemini,
                        st.session_state.session_id,
                        st.session_state.logger,
                    )
                    st.success("Summary ready")
                    st.markdown(summary)

                except ValueError as exc:
                    st.error(f"Input error: {exc}")
                    log_event(
                        st.session_state.logger, "ERROR", "fetch_error",
                        st.session_state.session_id, "URL", url_input,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Could not reach that URL. "
                        "Check your internet connection and verify the address."
                    )
                    log_event(
                        st.session_state.logger, "ERROR", "fetch_error",
                        st.session_state.session_id, "URL", url_input,
                        st.session_state.gemini.model_name,
                        error_message="ConnectionError",
                    )

                except requests.exceptions.Timeout:
                    st.error(
                        "The request timed out after 10 seconds. "
                        "The site may be slow or unavailable."
                    )
                    log_event(
                        st.session_state.logger, "ERROR", "fetch_error",
                        st.session_state.session_id, "URL", url_input,
                        st.session_state.gemini.model_name,
                        error_message="Timeout",
                    )

                except requests.exceptions.HTTPError as exc:
                    st.error(f"HTTP error while fetching the page: {exc}")
                    log_event(
                        st.session_state.logger, "ERROR", "fetch_error",
                        st.session_state.session_id, "URL", url_input,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

                except ResourceExhausted as exc:
                    st.error(
                        "Gemini API quota exceeded. This is an API-level limit "
                        "on the Google Cloud project linked to your API key - "
                        "separate from a Gemini app subscription. "
                        "Enable billing at https://console.cloud.google.com/billing "
                        "or check your quota at https://ai.dev/rate-limit."
                    )
                    log_event(
                        st.session_state.logger, "ERROR", "gemini_error",
                        st.session_state.session_id, "URL", url_input,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

                except Exception as exc:
                    st.error(f"An unexpected error occurred: {exc}")
                    log_event(
                        st.session_state.logger, "ERROR", "gemini_error",
                        st.session_state.session_id, "URL", url_input,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

with tab_pdf:
    st.markdown(
        "Upload a text-based PDF (not a scanned image). "
        "Agnilonda Pakou will extract the text and summarize it."
    )

    uploaded_pdf = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Text-based PDFs only. Scanned or image-only PDFs are not supported.",
    )

    if uploaded_pdf is not None:
        size_kb = round(uploaded_pdf.size / 1024, 1)
        st.caption(f"Uploaded: **{uploaded_pdf.name}** ({size_kb} KB)")

    if st.button("Summarize PDF", type="primary", use_container_width=True, key="btn_pdf"):
        if uploaded_pdf is None:
            st.warning("Please upload a PDF file before clicking Summarize.")
        else:
            with st.spinner("Extracting text and summarizing - this may take a moment…"):
                try:
                    summary = summarize_pdf(
                        uploaded_pdf,
                        st.session_state.gemini,
                        st.session_state.session_id,
                        st.session_state.logger,
                    )
                    st.success("Summary ready")
                    st.markdown(summary)

                except ValueError as exc:
                    st.error(f"PDF error: {exc}")
                    log_event(
                        st.session_state.logger, "ERROR", "pdf_error",
                        st.session_state.session_id, "PDF", uploaded_pdf.name,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

                except pypdf.errors.PdfReadError as exc:
                    st.error(
                        "Could not read the PDF. "
                        "It may be corrupt or password-protected."
                    )
                    log_event(
                        st.session_state.logger, "ERROR", "pdf_error",
                        st.session_state.session_id, "PDF", uploaded_pdf.name,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

                except ResourceExhausted as exc:
                    st.error(
                        "Gemini API quota exceeded. This is an API-level limit "
                        "on the Google Cloud project linked to your API key - "
                        "separate from a Gemini app subscription. "
                        "Enable billing at https://console.cloud.google.com/billing "
                        "or check your quota at https://ai.dev/rate-limit."
                    )
                    log_event(
                        st.session_state.logger, "ERROR", "gemini_error",
                        st.session_state.session_id, "PDF", uploaded_pdf.name,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )

                except Exception as exc:
                    st.error(f"An unexpected error occurred: {exc}")
                    log_event(
                        st.session_state.logger, "ERROR", "gemini_error",
                        st.session_state.session_id, "PDF", uploaded_pdf.name,
                        st.session_state.gemini.model_name, error_message=str(exc),
                    )
