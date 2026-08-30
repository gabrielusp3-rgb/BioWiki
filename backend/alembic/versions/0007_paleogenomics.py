"""Paleogenomics collection tables and optional organism extinction fields.

Revision ID: 0007_paleogenomics
Revises: 0006_crispr_evidence
Create Date: 2026-08-30

Does not add SequenceType values. Genome assemblies remain genome_records.
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_paleogenomics"
down_revision: Union[str, Sequence[str], None] = "0006_crispr_evidence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    organism_cols = {col["name"] for col in inspector.get_columns("organisms")}
    if "extinction_status" not in organism_cols:
        op.add_column("organisms", sa.Column("extinction_status", sa.String(length=40), nullable=True))
        op.create_index("ix_organisms_extinction_status", "organisms", ["extinction_status"])
    if "extinction_date_text" not in organism_cols:
        op.add_column("organisms", sa.Column("extinction_date_text", sa.String(length=160), nullable=True))
    if "geologic_period" not in organism_cols:
        op.add_column("organisms", sa.Column("geologic_period", sa.String(length=80), nullable=True))

    tables = set(inspector.get_table_names())
    uuid_type = postgresql.UUID(as_uuid=True)
    if "paleogenomic_profiles" not in tables:
        op.create_table(
            "paleogenomic_profiles",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("organism_id", uuid_type, nullable=False),
            sa.Column("slug", sa.String(length=160), nullable=False),
            sa.Column("common_name", sa.String(length=160), nullable=False),
            sa.Column("geographic_region", sa.String(length=160), nullable=True),
            sa.Column("subsection", sa.String(length=40), nullable=False),
            sa.Column("featured_rank", sa.Integer(), nullable=True),
            sa.Column("deextinction_status", sa.String(length=64), nullable=False, server_default="unknown"),
            sa.Column("last_reviewed_on", sa.Date(), nullable=True),
            sa.Column("taxonomic_uncertainty", sa.Text(), nullable=True),
            sa.Column("paleogenomic_data_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["organism_id"], ["organisms.id"], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("organism_id"),
            sa.UniqueConstraint("slug"),
        )
        op.create_index("ix_paleogenomic_profiles_slug", "paleogenomic_profiles", ["slug"])
        op.create_index("ix_paleogenomic_profiles_subsection", "paleogenomic_profiles", ["subsection"])

    if "paleogenomic_claims" not in tables:
        op.create_table(
            "paleogenomic_claims",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("profile_id", uuid_type, nullable=False),
            sa.Column("section_key", sa.String(length=40), nullable=False),
            sa.Column("title", sa.String(length=160), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("evidence_level", sa.String(length=32), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_reviewed_on", sa.Date(), nullable=True),
            sa.ForeignKeyConstraint(["profile_id"], ["paleogenomic_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("profile_id", "section_key", name="uq_paleogenomic_claims_section"),
        )
        op.create_index("ix_paleogenomic_claims_profile_id", "paleogenomic_claims", ["profile_id"])

    if "paleogenomic_claim_sources" not in tables:
        op.create_table(
            "paleogenomic_claim_sources",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("claim_id", uuid_type, nullable=False),
            sa.Column("publication_id", uuid_type, nullable=True),
            sa.Column("pubmed_id", sa.BigInteger(), nullable=True),
            sa.Column("doi", sa.String(length=255), nullable=True),
            sa.Column("url", sa.String(length=500), nullable=True),
            sa.Column("label", sa.String(length=300), nullable=True),
            sa.ForeignKeyConstraint(["claim_id"], ["paleogenomic_claims.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_paleogenomic_claim_sources_claim_id", "paleogenomic_claim_sources", ["claim_id"])
        op.create_index("ix_paleogenomic_claim_sources_publication_id", "paleogenomic_claim_sources", ["publication_id"])

    if "paleogenomic_sequence_membership" not in tables:
        op.create_table(
            "paleogenomic_sequence_membership",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("sequence_id", uuid_type, nullable=False),
            sa.Column("profile_id", uuid_type, nullable=False),
            sa.Column("record_kind", sa.String(length=32), nullable=False, server_default="other"),
            sa.Column("is_complete_mitogenome", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("specimen_label", sa.String(length=160), nullable=True),
            sa.Column("biosample", sa.String(length=64), nullable=True),
            sa.Column("bioproject", sa.String(length=64), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["sequence_id"], ["sequences.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["profile_id"], ["paleogenomic_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("sequence_id", name="uq_paleogenomic_sequence_membership_sequence"),
        )
        op.create_index("ix_paleogenomic_sequence_membership_profile_id", "paleogenomic_sequence_membership", ["profile_id"])
        op.create_index("ix_paleogenomic_sequence_membership_biosample", "paleogenomic_sequence_membership", ["biosample"])
        op.create_index("ix_paleogenomic_sequence_membership_bioproject", "paleogenomic_sequence_membership", ["bioproject"])

    if "paleogenomic_projects" not in tables:
        op.create_table(
            "paleogenomic_projects",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("profile_id", uuid_type, nullable=False),
            sa.Column("bioproject", sa.String(length=64), nullable=True),
            sa.Column("biosample", sa.String(length=64), nullable=True),
            sa.Column("run_accession", sa.String(length=64), nullable=True),
            sa.Column("experiment_accession", sa.String(length=64), nullable=True),
            sa.Column("library_strategy", sa.String(length=80), nullable=True),
            sa.Column("source_url", sa.String(length=500), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("controlled_access", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.ForeignKeyConstraint(["profile_id"], ["paleogenomic_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "bioproject",
                "biosample",
                "run_accession",
                name="uq_paleogenomic_projects_accessions",
            ),
        )
        op.create_index("ix_paleogenomic_projects_profile_id", "paleogenomic_projects", ["profile_id"])
        op.create_index("ix_paleogenomic_projects_bioproject", "paleogenomic_projects", ["bioproject"])
        op.create_index("ix_paleogenomic_projects_biosample", "paleogenomic_projects", ["biosample"])

    if "paleogenomic_introgression_regions" not in tables:
        op.create_table(
            "paleogenomic_introgression_regions",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("modern_organism_id", uuid_type, nullable=False),
            sa.Column("archaic_source", sa.String(length=32), nullable=False),
            sa.Column("gene_name", sa.String(length=80), nullable=True),
            sa.Column("locus_name", sa.String(length=160), nullable=True),
            sa.Column("reference_build", sa.String(length=32), nullable=True),
            sa.Column("chromosome", sa.String(length=16), nullable=True),
            sa.Column("start_position", sa.Integer(), nullable=True),
            sa.Column("end_position", sa.Integer(), nullable=True),
            sa.Column("publication_id", uuid_type, nullable=True),
            sa.Column("pubmed_id", sa.BigInteger(), nullable=True),
            sa.Column("doi", sa.String(length=255), nullable=True),
            sa.Column("method", sa.String(length=160), nullable=True),
            sa.Column("evidence_notes", sa.Text(), nullable=False),
            sa.Column("source_dataset", sa.String(length=160), nullable=True),
            sa.ForeignKeyConstraint(["modern_organism_id"], ["organisms.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "archaic_source",
                "gene_name",
                "reference_build",
                "chromosome",
                "start_position",
                "end_position",
                name="uq_paleogenomic_introgression_interval",
            ),
        )
        op.create_index(
            "ix_paleogenomic_introgression_regions_modern_organism_id",
            "paleogenomic_introgression_regions",
            ["modern_organism_id"],
        )
        op.create_index(
            "ix_paleogenomic_introgression_regions_archaic_source",
            "paleogenomic_introgression_regions",
            ["archaic_source"],
        )
        op.create_index(
            "ix_paleogenomic_introgression_regions_gene_name",
            "paleogenomic_introgression_regions",
            ["gene_name"],
        )
        op.create_index(
            "uq_paleogenomic_introgression_gene_level",
            "paleogenomic_introgression_regions",
            ["archaic_source", "gene_name"],
            unique=True,
            postgresql_where=sa.text("gene_name IS NOT NULL AND start_position IS NULL"),
        )

    if "paleogenomic_publication_membership" not in tables:
        op.create_table(
            "paleogenomic_publication_membership",
            sa.Column("id", uuid_type, server_default=sa.text("gen_random_uuid()"), nullable=False),
            sa.Column("profile_id", uuid_type, nullable=False),
            sa.Column("publication_id", uuid_type, nullable=False),
            sa.ForeignKeyConstraint(["profile_id"], ["paleogenomic_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["publication_id"], ["publications.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "profile_id",
                "publication_id",
                name="uq_paleogenomic_publication_membership",
            ),
        )
        op.create_index(
            "ix_paleogenomic_publication_membership_profile_id",
            "paleogenomic_publication_membership",
            ["profile_id"],
        )
        op.create_index(
            "ix_paleogenomic_publication_membership_publication_id",
            "paleogenomic_publication_membership",
            ["publication_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "paleogenomic_publication_membership" in tables:
        op.drop_table("paleogenomic_publication_membership")
    op.drop_table("paleogenomic_introgression_regions")
    op.drop_table("paleogenomic_projects")
    op.drop_table("paleogenomic_sequence_membership")
    op.drop_table("paleogenomic_claim_sources")
    op.drop_table("paleogenomic_claims")
    op.drop_table("paleogenomic_profiles")
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    organism_cols = {col["name"] for col in inspector.get_columns("organisms")}
    indexes = {idx["name"] for idx in inspector.get_indexes("organisms")}
    if "ix_organisms_extinction_status" in indexes:
        op.drop_index("ix_organisms_extinction_status", table_name="organisms")
    for name in ("geologic_period", "extinction_date_text", "extinction_status"):
        if name in organism_cols:
            op.drop_column("organisms", name)
