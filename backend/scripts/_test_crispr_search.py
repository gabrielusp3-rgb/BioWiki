import asyncio

from app.pipeline.fetchers import ncbi

TERM = (
    'CRISPR[Title] AND (array[Title] OR "repeat region"[Title] OR locus[Title]) '
    "AND 100:50000[SLEN]"
)

if __name__ == "__main__":
    report = asyncio.run(ncbi.ingest(term=TERM, limit=5, seq_type="crispr"))
    print(report.as_dict())
