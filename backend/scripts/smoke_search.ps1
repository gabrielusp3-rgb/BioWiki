# Smoke test for PASSO 31 global search (real data only).
$base = "http://127.0.0.1:8000/api/v1"

function Probe($name, $url) {
    try {
        $r = Invoke-RestMethod -Uri $url -TimeoutSec 20
        $seq = ($r.results | ForEach-Object { $_.accession }) -join ","
        $pub = ($r.publications | ForEach-Object { $_.pubmedId }) -join ","
        "{0,-34} seqTotal={1,-3} seqs=[{2}] pubTotal={3,-3} pubs=[{4}]" -f `
            $name, $r.total, $seq, $r.publicationsTotal, $pub
    } catch {
        "{0,-34} FAILED: {1}" -f $name, $_.Exception.Message
    }
}

Probe "texto livre: insulin"       "$base/search?q=insulin&limit=5"
Probe "accession: NM_000207"       "$base/search?q=NM_000207&limit=5"
Probe "accession parcial: P01308"  "$base/search?q=P01308&limit=5"
Probe "gene: INS"                  "$base/search?q=INS&limit=5"
Probe "organismo: Homo sapiens"    "$base/search?q=Homo%20sapiens&limit=5"
Probe "nome comum: human"          "$base/search?q=human&limit=5"
Probe "taxid: 9606"                "$base/search?q=9606&limit=5"
Probe "PMID: 3313277"              "$base/search?q=3313277&limit=5"
Probe "autor: Kozak"               "$base/search?q=Kozak&limit=5"
Probe "titulo: noncoding"          "$base/search?q=noncoding&limit=5"
Probe "filtro tipo rna"            "$base/search?q=insulin&types=rna&limit=5"
Probe "filtro tipo protein"        "$base/search?q=insulin&types=protein&limit=5"
Probe "filtro organismo"           "$base/search?q=insulin&organism=Homo%20sapiens&limit=5"
Probe "filtro comprimento >400"    "$base/search?q=insulin&min_length=400&limit=5"
Probe "filtro comprimento <200"    "$base/search?q=insulin&max_length=200&limit=5"
Probe "sem resultados: xyzabc"     "$base/search?q=xyzabc123&limit=5"
