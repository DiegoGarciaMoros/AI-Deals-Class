import json
import os
import zipfile
import io

import pytest

from citeextract import analyze, courtlistener
from citeextract.exporters import EXPORTS, export
from citeextract.extractor import clean_case_text, parse

HERE = os.path.dirname(__file__)
SAMPLE = open(os.path.join(HERE, "..", "samples", "sample_opinion.txt"), encoding="utf-8").read()


def by_cite(result, cite):
    return next(a for a in result["authorities"] if a["citation"] == cite)


@pytest.fixture(scope="module")
def sample():
    return parse(SAMPLE)


def test_counts(sample):
    s = sample["stats"]
    assert s["cases"] == 13
    assert s["statutes"] == 3  # § 1983, § 2000e-2, 29 C.F.R. § 1604.11
    assert s["journals"] == 2
    assert s["unresolved"] == 1  # "Smith, supra" has no antecedent


def test_parallel_citations_grouped_and_deduped(sample):
    twombly = by_cite(sample, "550 U.S. 544")
    assert twombly["case_name"] == "Bell Atlantic Corp. v. Twombly"
    assert twombly["parallel_citations"] == ["127 S. Ct. 1955", "167 L. Ed. 2d 929"]
    assert twombly["counts"] == {"full": 2, "short": 2}
    assert twombly["pin_cites"] == ["570", "555", "556"]
    assert twombly["year"] == 2007


def test_case_names_repaired(sample):
    names = {a["case_name"] for a in sample["authorities"] if a["kind"] == "case"}
    assert "Flagg Bros., Inc. v. Brooks" in names
    assert "Meritor Savings Bank, FSB v. Vinson" in names


def test_short_forms_resolve(sample):
    littlejohn = by_cite(sample, "795 F.3d 297")
    assert littlejohn["counts"] == {"full": 1, "short": 1, "id": 1}
    assert littlejohn["full_citation"] == "Littlejohn v. City of New York, 795 F.3d 297 (2d Cir. 2015)"
    monell = by_cite(sample, "436 U.S. 658")
    assert monell["counts"] == {"full": 1, "supra": 1}
    assert "690" in monell["pin_cites"]


def test_signals_and_parentheticals(sample):
    lugar = by_cite(sample, "457 U.S. 922")
    assert lugar["signals"] == ["See, e.g."]
    assert lugar["parentheticals"] == ["articulating two-part test for attributing private conduct to the State"]
    assert by_cite(sample, "534 U.S. 506")["signals"] == ["But see"]


def test_statutes_and_rules():
    r = parse("See 42 U.S.C. § 2000e-2(a); 17 C.F.R. § 240.10b-5(b); 15 U.S.C. § 78j(b). Id. § 78j(a). "
              "Fed. R. Civ. P. 12(b)(6). Also 42 U.S.C. § 2000e-2(b).")
    cites = {a["citation"]: a for a in r["authorities"]}
    assert set(cites) == {"42 U.S.C. § 2000e-2", "17 C.F.R. § 240.10b-5", "15 U.S.C. § 78j", "Fed. R. Civ. P. 12"}
    assert cites["42 U.S.C. § 2000e-2"]["occurrence_count"] == 2
    assert cites["42 U.S.C. § 2000e-2"]["pin_cites"] == ["(a)", "(b)"]
    assert cites["15 U.S.C. § 78j"]["counts"] == {"full": 1, "id": 1}
    assert cites["17 C.F.R. § 240.10b-5"]["links"]["source"] == "https://www.law.cornell.edu/cfr/text/17/240.10b-5"
    assert cites["Fed. R. Civ. P. 12"]["links"]["source"] == "https://www.law.cornell.edu/rules/frcp/rule_12"


def test_normalization_dedupes_reporter_spacing():
    r = parse("Roe v. Wade, 410 U. S. 113 (1973). Later: Roe v. Wade, 410 U.S. 113, 115 (1973).")
    assert len(r["authorities"]) == 1
    roe = r["authorities"][0]
    assert roe["citation"] == "410 U.S. 113"
    assert roe["occurrence_count"] == 2
    assert roe["links"]["courtlistener_citation"] == "https://www.courtlistener.com/c/U.S./410/113/"


def test_cleaning_html_and_line_wraps():
    text = clean_case_text("<p>Harris v. Forklift Sys., Inc., 510 U.S. 17, 21\n(1993).</p><p>Next&nbsp;para</p>")
    r = parse("<p>Harris v. Forklift Sys., Inc., 510 U.S. 17, 21\n(1993).</p>")
    assert "<p>" not in text
    assert r["authorities"][0]["year"] == 1993


def test_context_highlights_match(sample):
    occ = by_cite(sample, "556 U.S. 662")["occurrences"][0]
    assert occ["context"]["match"] == "556 U.S. 662"
    assert "Ashcroft v. Iqbal" in occ["context"]["before"]


def test_exports(sample):
    for fmt in EXPORTS:
        name, mime, content = export(sample, fmt)
        assert content, fmt
    assert "Bell Atlantic Corp. v. Twombly" in export(sample, "toa_md")[2].decode()
    data = json.loads(export(sample, "json")[2])
    assert data["stats"]["unique_authorities"] == len(sample["authorities"])
    zf = zipfile.ZipFile(io.BytesIO(export(sample, "zip")[2]))
    assert len(zf.namelist()) == len(EXPORTS)


# --------------------------------------------------------------------------- #
# CourtListener (mocked HTTP)
# --------------------------------------------------------------------------- #
class FakeResponse:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responder):
        self.responder = responder
        self.calls = []

    def post(self, url, data=None, headers=None, timeout=None):
        self.calls.append({"url": url, "data": data, "headers": headers})
        return self.responder(data["text"])


def cl_item(text, cite, status=200, clusters=None):
    start = text.index(cite)
    return {"citation": cite, "normalized_citations": [cite], "start_index": start,
            "end_index": start + len(cite), "status": status, "error_message": "", "clusters": clusters or []}


def cluster(cid, name, url, date="2007-05-21"):
    return {"id": cid, "case_name": name, "absolute_url": url, "date_filed": date,
            "citations": [{"volume": 550, "reporter": "U.S.", "page": "544", "type": 1}]}


@pytest.fixture(autouse=True)
def _clear_cache():
    courtlistener.clear_cache()


def test_lookup_links_and_merges_parallel_cites():
    text = "Twombly, 550 U.S. 544 (2007). Later the court cited 127 S. Ct. 1955 (2007) and Foo v. Bar, 999 F.3d 1 (2d Cir. 2021)."

    def responder(body):
        items = []
        for cite in body.split("\n"):
            if cite in ("550 U.S. 544", "127 S. Ct. 1955"):
                items.append(cl_item(body, cite, 200, [cluster(145730, "Bell Atlantic Corp. v. Twombly",
                                                                "/opinion/145730/bell-atlantic-corp-v-twombly/")]))
            else:
                items.append(cl_item(body, cite, 404))
        return FakeResponse(200, items)

    session = FakeSession(responder)
    r = analyze(text, lookup=True, token="abc", session=session)
    assert session.calls[0]["headers"]["Authorization"] == "Token abc"
    assert r["lookup"]["merged_parallel"] == 1
    twombly = by_cite(r, "550 U.S. 544")
    assert twombly["parallel_citations"] == ["127 S. Ct. 1955"]
    assert twombly["links"]["courtlistener"] == "https://www.courtlistener.com/opinion/145730/bell-atlantic-corp-v-twombly/"
    assert twombly["courtlistener"]["status"] == "found"
    assert twombly["occurrence_count"] == 2
    foo = by_cite(r, "999 F.3d 1")
    assert foo["courtlistener"]["status"] == "not_found"
    assert r["stats"]["linked"] == 1


def test_lookup_fills_missing_case_name():
    def responder(body):
        return FakeResponse(200, [cl_item(body, "550 U.S. 544", 200, [cluster(1, "Bell Atlantic Corp. v. Twombly", "/opinion/1/x/")])])
    r = analyze("As held in 550 U.S. 544, 556 (2007), plausibility is required.", lookup=True, session=FakeSession(responder))
    assert r["authorities"][0]["case_name"] == "Bell Atlantic Corp. v. Twombly"


def test_lookup_ambiguous():
    def responder(body):
        return FakeResponse(200, [cl_item(body, "1 U.S. 1", 300, [cluster(1, "A v. B", "/opinion/1/a/"),
                                                                  cluster(2, "C v. D", "/opinion/2/c/")])])
    r = analyze("A v. B, 1 U.S. 1 (1754).", lookup=True, session=FakeSession(responder))
    cl = r["authorities"][0]["courtlistener"]
    assert cl["status"] == "ambiguous" and len(cl["candidates"]) == 2
    assert r["authorities"][0]["links"]["courtlistener"] is None


def test_lookup_auth_error_is_reported_not_raised():
    r = analyze("A v. B, 1 U.S. 1 (1754).", lookup=True, session=FakeSession(lambda body: FakeResponse(401, {})))
    assert "token" in r["lookup"]["error"].lower()
    assert r["authorities"][0]["links"]["courtlistener_citation"]


def test_lookup_chunks_large_requests():
    cites = [f"{i} U.S. {i}" for i in range(1, 600)]
    assert [len(c) for c in courtlistener._chunks(cites)] == [250, 250, 99]


def test_flask_endpoints():
    from app import app
    client = app.test_client()
    res = client.post("/api/analyze", json={"text": SAMPLE, "lookup": False})
    assert res.status_code == 200
    data = res.get_json()
    assert data["stats"]["cases"] == 13
    res = client.post("/api/export/authorities_csv", json=data)
    assert res.status_code == 200 and b"Bell Atlantic Corp. v. Twombly" in res.data
    assert client.post("/api/analyze", json={"text": " "}).status_code == 400
    assert client.post("/api/export/nope", json=data).status_code == 404
    assert client.get("/").status_code == 200
