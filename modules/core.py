"""Cached accessors for data and the ML model (Streamlit-aware)."""
import streamlit as st

from . import config, data_loader, model, settings


@st.cache_data(show_spinner="Loading booking data…")
def _load(rate: float, sig_base: str, sig_added: str):
    return data_loader.load_all(rate)


def data():
    cfg = settings.load()
    return _load(float(cfg["eur_to_inr"]),
                 data_loader.file_signature(config.BASE_CSV),
                 data_loader.file_signature(config.ADDED_CSV))


@st.cache_resource(show_spinner="Preparing the cancellation-risk model (first run only, ~20 s)…")
def _get_model(sig: str):
    bundle = model.load_bundle()
    if bundle is None:
        bundle = model.train(data())
    return bundle


def get_model():
    return _get_model(data_loader.file_signature(config.MODEL_FILE))


def retrain():
    bundle = model.train(data())
    _get_model.clear()
    return bundle


def clear_data_cache():
    _load.clear()
