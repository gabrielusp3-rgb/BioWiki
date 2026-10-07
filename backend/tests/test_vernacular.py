"""Vernacular acceptance rules. These tests do not require the database."""

from app.pipeline.paleogenomics.vernacular import (
    LOCALES,
    accept_wikidata_name,
    looks_like_scientific_name,
    resolve_display,
)


def test_eleven_locales_include_english_and_arabic() -> None:
    assert len(LOCALES) == 11
    assert "en-GB" in LOCALES
    assert "ar-SA" in LOCALES
    assert "hi-IN" in LOCALES


def test_scientific_names_are_not_vernacular() -> None:
    assert looks_like_scientific_name("Raphus cucullatus", "Raphus cucullatus")
    assert looks_like_scientific_name("Bos taurus primigenius", "Bos primigenius")
    assert not looks_like_scientific_name("Dodo", "Raphus cucullatus")
    assert not looks_like_scientific_name("渡渡鸟", "Raphus cucullatus")


def test_rejects_north_island_moa_label_for_south_island_species() -> None:
    assert (
        accept_wikidata_name(
            slug="dinornis-robustus",
            scientific_name="Dinornis robustus",
            name="Moa Gigante De La Isla Norte",
            lang="es",
        )
        is None
    )
    assert (
        accept_wikidata_name(
            slug="dinornis-robustus",
            scientific_name="Dinornis robustus",
            name="Moa géant de l'île du Sud",
            lang="fr",
        )
        == "fr-FR"
    )


def test_rejects_dingcun_label_for_neanderthal() -> None:
    assert (
        accept_wikidata_name(
            slug="homo-neanderthalensis",
            scientific_name="Homo sapiens neanderthalensis",
            name="丁村人",
            lang="zh",
        )
        is None
    )


def test_missing_translation_falls_back_to_english_without_using_the_binomial() -> None:
    resolved = resolve_display(
        "hi-IN",
        {
            "en-GB": {
                "name": "Dodo",
                "locale": "en-GB",
                "source": "biowiki_paleogenomics_catalogue",
                "source_url": "https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=187135",
            }
        },
        english_name="Dodo",
        scientific_name="Raphus cucullatus",
    )
    assert resolved is not None
    assert resolved["name"] == "Dodo"
    assert resolved["fallback"] is True
    assert resolved["name"] != "Raphus cucullatus"


def test_exact_locale_is_not_a_fallback() -> None:
    resolved = resolve_display(
        "zh-CN",
        {"zh-CN": {"name": "渡渡鸟", "locale": "zh-CN", "source": "wikidata", "source_url": "https://www.wikidata.org/wiki/Q17101"}},
        english_name="Dodo",
        scientific_name="Raphus cucullatus",
    )
    assert resolved is not None
    assert resolved["name"] == "渡渡鸟"
    assert resolved["fallback"] is False


def test_no_english_name_does_not_invent_one() -> None:
    assert (
        resolve_display(
            "ja-JP",
            {},
            english_name=None,
            scientific_name="Raphus cucullatus",
        )
        is None
    )
