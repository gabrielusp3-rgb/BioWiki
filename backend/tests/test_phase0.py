"""Phase 0 regression: taxonomy honesty, checkpoints, publication identity."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.publication import Publication, SequenceReference
from app.models.sequence import Sequence
from app.pipeline.errors import ValidationError
from app.pipeline.models import ParsedOrganism, ParsedPublication
from app.pipeline.phase0.checkpoint import (
    load_checkpoint,
    mark,
    needs_retry,
    record_key,
    save_checkpoint,
)
from app.pipeline.phase0.errors import classify_external_error
from app.pipeline.phase0.names import (
    MERGED_TAXID,
    UPDATED_CANONICAL_NAME,
    VALID_NAME,
    VALID_SYNONYM,
    classify_organism_taxonomy,
)
from app.pipeline.taxonomy import group_from_taxonomy, index_taxonomy_for_requested
from app.pipeline.validation import enrich, infer_group_from_lineage, validate
from app.services.connectors.errors import (
    ConnectorNotFound,
    ConnectorRateLimited,
    ConnectorTimeout,
    ConnectorUnavailable,
)
from tests.fixtures import make_fixture_dna


_MERGED_XML = """\
<TaxaSet>
  <Taxon>
    <TaxId>9606</TaxId>
    <ScientificName>Homo sapiens</ScientificName>
    <Division>Primates</Division>
    <Rank>species</Rank>
    <Lineage>cellular organisms; Eukaryota; Metazoa; Chordata; Mammalia; Primates; Hominidae; Homo</Lineage>
    <OtherNames>
      <Synonym>man</Synonym>
      <GenbankCommonName>human</GenbankCommonName>
    </OtherNames>
    <AkaTaxIds>
      <TaxId>63221</TaxId>
    </AkaTaxIds>
  </Taxon>
</TaxaSet>
"""


def test_empty_lineage_does_not_become_bacteria() -> None:
    assert infer_group_from_lineage([]) is None
    assert infer_group_from_lineage(None) is None
    assert group_from_taxonomy(lineage=[], division=None) is None
    assert group_from_taxonomy(lineage=[], division="Plants and Fungi") is None


def test_unknown_taxonomy_never_defaults_to_bacteria() -> None:
    ps = make_fixture_dna(
        organism=ParsedOrganism(
            scientific_name="synthetic construct",
            tax_id=32630,
            lineage=["other sequences", "artificial sequences"],
            group=None,
        )
    )
    enrich(ps)
    with pytest.raises(ValidationError, match="refusing to invent|synthetic or unclassified"):
        validate(ps)
    assert ps.organism is not None
    assert ps.organism.group != "bacteria"


def test_merged_taxid_is_indexed_from_aka_ids() -> None:
    indexed = index_taxonomy_for_requested(_MERGED_XML, [63221])
    assert 63221 in indexed
    assert indexed[63221]["tax_id"] == 9606
    assert indexed[63221]["scientific_name"] == "Homo sapiens"


def test_merged_taxid_single_response_without_aka() -> None:
    xml = """
    <TaxaSet>
      <Taxon>
        <TaxId>9606</TaxId>
        <ScientificName>Homo sapiens</ScientificName>
        <Lineage>Eukaryota; Metazoa; Homo</Lineage>
      </Taxon>
    </TaxaSet>
    """
    indexed = index_taxonomy_for_requested(xml, [63221])
    assert indexed[63221]["tax_id"] == 9606


def test_scientific_name_classifications() -> None:
    ncbi = {
        "tax_id": 9606,
        "scientific_name": "Homo sapiens",
        "synonyms": ["man"],
        "lineage": ["Eukaryota", "Metazoa"],
    }
    assert classify_organism_taxonomy(
        stored_tax_id=9606, stored_name="Homo sapiens", ncbi=ncbi
    )["status"] == VALID_NAME
    assert classify_organism_taxonomy(
        stored_tax_id=9606, stored_name="man", ncbi=ncbi
    )["status"] == VALID_SYNONYM
    assert classify_organism_taxonomy(
        stored_tax_id=9606, stored_name="Homo sapien", ncbi=ncbi
    )["status"] == UPDATED_CANONICAL_NAME
    assert classify_organism_taxonomy(
        stored_tax_id=63221, stored_name="Homo sapiens", ncbi=ncbi
    )["status"] == MERGED_TAXID
    assert classify_organism_taxonomy(
        stored_tax_id=1, stored_name="x", ncbi=None
    )["status"] == "UNRESOLVED"


def test_not_found_is_retried_after_method_fix() -> None:
    assert needs_retry({"status": "NOT_FOUND"}) is True
    assert needs_retry({"status": "VERIFIED"}) is False
    assert needs_retry({"status": "INVALID"}) is False


def test_checkpoint_resume_retries_only_temporary(tmp_path: Path) -> None:
    path = tmp_path / "phase0.json"
    data = load_checkpoint(path)
    mark(data["records"], record_key("NCBI", "LC942670", "1"), status="VERIFIED")
    mark(data["records"], record_key("UniProt", "P01308", "1"), status="TEMPORARILY_UNVERIFIED")
    save_checkpoint(path, data)
    loaded = load_checkpoint(path)
    assert needs_retry(loaded["records"][record_key("NCBI", "LC942670", "1")]) is False
    assert needs_retry(loaded["records"][record_key("UniProt", "P01308", "1")]) is True
    assert needs_retry(loaded["records"].get("missing")) is True
    assert loaded["verified"] == 1
    assert loaded["temporary_failures"] == 1


def test_checkpoint_survives_truncated_replace(tmp_path: Path) -> None:
    path = tmp_path / "phase0.json"
    data = load_checkpoint(path)
    mark(data["records"], "a", status="VERIFIED")
    save_checkpoint(path, data)
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()


def test_timeout_and_429_are_temporarily_unverified() -> None:
    assert classify_external_error(ConnectorTimeout("slow", source="ncbi")) == "TEMPORARILY_UNVERIFIED"
    assert classify_external_error(ConnectorUnavailable("reset", source="ncbi")) == "TEMPORARILY_UNVERIFIED"
    assert (
        classify_external_error(ConnectorRateLimited("wait", source="uniprot"))
        == "TEMPORARILY_UNVERIFIED"
    )
    assert classify_external_error(ConnectorNotFound("gone", status_code=404, source="pdb")) == "NOT_FOUND"
    assert classify_external_error(TimeoutError("timed out")) == "TEMPORARILY_UNVERIFIED"


def test_publication_can_exist_without_sequence_reference() -> None:
    assert "sequence_id" not in Publication.__table__.c
    names = {item.name for item in SequenceReference.__table__.constraints if getattr(item, "name", None)}
    assert "uq_sequence_references_pair" in names


def test_duplicate_pmid_prevented_by_unique_constraint() -> None:
    assert Publication.__table__.c.pubmed_id.unique is True
    assert Publication.__table__.c.doi.unique is True


def test_sequence_natural_key_unique_constraint() -> None:
    names = {item.name for item in Sequence.__table__.constraints if getattr(item, "name", None)}
    assert "sequences_source_accession_version" in names


def test_parsed_publication_does_not_require_a_sequence() -> None:
    parsed = ParsedPublication(title="A real article", pubmed_id=25359968)
    assert parsed.pubmed_id == 25359968
    assert parsed.title.startswith("A real")
