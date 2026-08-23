# Smoke test for the BIOWIKI v1 API (real data only).
$base = "http://127.0.0.1:8000/api/v1"

function Probe($name, $url) {
    try {
        $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 20
        $body = $r.Content
        if ($body.Length -gt 220) { $body = $body.Substring(0, 220) + "..." }
        "{0,-38} {1}  {2}" -f $name, $r.StatusCode, ($body -replace "`n", " ")
    } catch {
        $status = $_.Exception.Response.StatusCode.value__
        "{0,-38} {1}  {2}" -f $name, $status, $_.ErrorDetails.Message
    }
}

Probe "GET /sequences?type=rna"        "$base/sequences?type=rna&limit=2"
Probe "GET /sequences/NM_000207"       "$base/sequences/NM_000207"
Probe "GET /rna"                       "$base/rna?limit=2"
Probe "GET /crispr (vazio honesto)"    "$base/crispr?limit=2"
Probe "GET /proteins"                  "$base/proteins?limit=2"
Probe "GET /viruses (vazio honesto)"   "$base/viruses?limit=2"
Probe "GET /virus (legado)"            "$base/virus?limit=2"
Probe "GET /organisms"                 "$base/organisms?limit=2"
Probe "GET /organisms/homo-sapiens"    "$base/organisms/homo-sapiens"
Probe "GET /organisms/9606 (taxId)"    "$base/organisms/9606"
Probe "GET /organisms/featured"        "$base/organisms/featured?limit=2"
Probe "GET /genomes"                   "$base/genomes?limit=2"
Probe "GET /publications"              "$base/publications?limit=2"
Probe "GET /publications?accession"    "$base/publications?accession=NM_000207&limit=3"
Probe "GET /publications?gene=INS"     "$base/publications?gene=INS&limit=3"
Probe "GET /publications?organism"     "$base/publications?organism=Homo%20sapiens&limit=3"
Probe "GET /publications/3313277"      "$base/publications/3313277"
Probe "GET /publications/999999999"    "$base/publications/999999999"
Probe "GET /search?q=insulin"          "$base/search?q=insulin&limit=3"
Probe "GET /download"                  "$base/download"
Probe "GET /download/sequences fasta"  "$base/download/sequences?format=fasta&type=rna&limit=10"
Probe "GET /download/sequences csv"    "$base/download/sequences?format=csv&limit=10"
Probe "GET /download/seq fasta"        "$base/download/sequence/NM_000207?format=fasta"
Probe "GET /download/seq genbank"      "$base/download/sequence/NM_000207?format=genbank"
Probe "GET /download/seq json"         "$base/download/sequence/P01308?format=json"
Probe "GET /download bad format"       "$base/download/sequences?format=xml"
Probe "GET /sequences bad type"        "$base/sequences?type=foo"
Probe "GET /statistics"                "$base/statistics"
