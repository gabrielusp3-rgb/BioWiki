from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AccessionPath, api_key_guard, get_session
from app.models.enums import SequenceType
from app.models.sequence import Sequence
from app.services import export_service

router = APIRouter(tags=["download"], dependencies=[Depends(api_key_guard)])


@router.get("/download", summary="Available export formats and dataset sizes")
async def download_index(session: AsyncSession = Depends(get_session)):
    rows = (
        await session.execute(
            select(Sequence.seq_type, func.count()).group_by(Sequence.seq_type)
        )
    ).all()
    datasets = [{"type": t.value, "records": int(c)} for t, c in rows]
    total = sum(d["records"] for d in datasets)
    return {
        "formats": ["fasta", "csv", "json", "genbank"],
        "datasets": datasets,
        "totalRecords": total,
    }


@router.get(
    "/download/sequences", summary="Bulk export of sequence records (FASTA, CSV or JSON)"
)
async def download_sequences(
    format: str = Query("fasta", max_length=16, description="fasta | csv | json"),
    type: str | None = Query(
        None, max_length=16, description="Sequence type: dna | rna | protein | crispr | virus | genome"
    ),
    q: str | None = Query(None, max_length=256, description="Free text over name/accession."),
    organism: str | None = Query(None, max_length=256),
    source: str | None = Query(None, max_length=64),
    gene: str | None = Query(None, max_length=120),
    limit: int = Query(1000, ge=1, le=10000),
    session: AsyncSession = Depends(get_session),
):
    content, media_type, filename = await export_service.export_sequences(
        session, format=format, type=type, q=q, organism=organism,
        source=source, gene=gene, limit=limit,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/download/sequence/{accession}",
    summary="Export a single sequence record (FASTA, GenBank or JSON)",
)
async def download_sequence(
    accession: AccessionPath,
    format: str = Query("fasta", max_length=16, description="fasta | genbank | json"),
    session: AsyncSession = Depends(get_session),
):
    _ = SequenceType  # keep import used for schema clarity
    result = await export_service.export_single(
        session, accession=accession, format=format
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Sequence not found")
    content, media_type, filename = result
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
