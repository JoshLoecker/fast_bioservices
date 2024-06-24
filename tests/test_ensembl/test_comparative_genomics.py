from unittest.mock import patch

import pytest
from fast_bioservices.ensembl.comparative_genomics import GetHomology, HomologyResult


@pytest.fixture(scope="session")
def get_homology_instance():
    return GetHomology(cache=False, max_workers=1, show_progress=False)

def test_get_homology_instance_creation(get_homology_instance):
    assert get_homology_instance is not None
    assert get_homology_instance._max_workers == 1
    assert not get_homology_instance._show_progress


def test_get_homology_url_property(get_homology_instance):
    assert get_homology_instance.url == "https://rest.ensembl.org"


@patch("fast_bioservices.ensembl.comparative_genomics.GetHomology._get")
def test_by_species_with_symbol_or_id_returns_homology_results(mock_get, get_homology_instance):
    mock_response = {
        "data": [
            {
                "id": "ENSG00000157764",
                "homologies": [
                    {
                        "method_link_type": "ENSEMBL_ORTHOLOGUES",
                        "dn_ds": None,
                        "taxonomy_level": "Catarrhini",
                        "type": "ortholog_one2one",
                        "target": {
                            "align_seq": "MAALSGGGGGGAEPGQALFNGDMEPE----AGAAASSAADPAIPEEVWNIKQMIKLTQEHIEALLDKFGGEHNPPSIYLEAYEEYTSKLDALQQREQQLLEYLGNGTDFSVSSSASMDTVTSSSSSSLSVLPSSLSVFQNPTDVSRSNPKSPQKPIVRVFLPNKQRTVVPARCGVTVRDSLKKALMMRGLIPECCAVYRIQDGEKKPIGWDTDISWLTGEELHVEVLENVPLTTHNFVRKTFFTLAFCDFCRKLLFQGFRCQTCGYKFHQRCSTEVPLMCVNYDQLDLLFVSKFFEHHPIPQEEASLAETALTSGSSPSAPTSDSLGPQILTSPSPSKSIPIPQPFRPADEDHRNQFGQRDRSSSAPNVHINTIEPVNIDDLIRDQGFRGDGGSTTGLSATPPASLPGSLTNVKALQKSPGPQRERKSSSSSEDRNRMKTLGRRDSSDDWEIPDGQITVGQRIGSGSFGTVYKGKWHGDVAVKMLNVTAPTPQQLQAFKNEVGVLRKTRHVNILLFMGYSTKPQLAIVTQWCEGSSLYHHLHIIETKFEMIKLIDIARQTAQGMDYLHAKSIIHRDLKSNNIFLHEDLTVKIGDFGLATVKSRWSGSHQFEQLSGSILWMAPEVIRMQDKNPYSFQSDVYAFGIVLYELMTGQLPYSNINNRDQIIFMVGRGYLSPDLSKVRSNCPKAMKRLMAECLKKKRDERPLFPQILASIELLARSLPKIHRSASEPSLNRAGFQTEDFSLYACASPKTPIQAGGYGEFAAFK",
                            "id": "ENSMMUG00000042793",
                            "species": "macaca_mulatta",
                            "perc_id": 98.8204,
                            "perc_pos": 99.0826,
                            "cigar_line": "26M4D737M",
                            "taxon_id": 9544,
                            "protein_id": "ENSMMUP00000044832",
                        },
                        "source": {
                            "perc_pos": 98.6945,
                            "cigar_line": "766MD",
                            "taxon_id": 9606,
                            "protein_id": "ENSP00000493543",
                            "align_seq": "MAALSGGGGGGAEPGQALFNGDMEPEAGAGAGAAASSAADPAIPEEVWNIKQMIKLTQEHIEALLDKFGGEHNPPSIYLEAYEEYTSKLDALQQREQQLLESLGNGTDFSVSSSASMDTVTSSSSSSLSVLPSSLSVFQNPTDVARSNPKSPQKPIVRVFLPNKQRTVVPARCGVTVRDSLKKALMMRGLIPECCAVYRIQDGEKKPIGWDTDISWLTGEELHVEVLENVPLTTHNFVRKTFFTLAFCDFCRKLLFQGFRCQTCGYKFHQRCSTEVPLMCVNYDQLDLLFVSKFFEHHPIPQEEASLAETALTSGSSPSAPASDSIGPQILTSPSPSKSIPIPQPFRPADEDHRNQFGQRDRSSSAPNVHINTIEPVNIDDLIRDQGFRGDGGSTTGLSATPPASLPGSLTNVKALQKSPGPQRERKSSSSSEDRNRMKTLGRRDSSDDWEIPDGQITVGQRIGSGSFGTVYKGKWHGDVAVKMLNVTAPTPQQLQAFKNEVGVLRKTRHVNILLFMGYSTKPQLAIVTQWCEGSSLYHHLHIIETKFEMIKLIDIARQTAQGMDYLHAKSIIHRDLKSNNIFLHEDLTVKIGDFGLATVKSRWSGSHQFEQLSGSILWMAPEVIRMQDKNPYSFQSDVYAFGIVLYELMTGQLPYSNINNRDQIIFMVGRGYLSPDLSKVRSNCPKAMKRLMAECLKKKRDERPLFPQILASIELLARSLPKIHRSASEPSLNRAGFQTEDFSLYACASPKTPIQAGGYGAFPVH-",
                            "id": "ENSG00000157764",
                            "species": "homo_sapiens",
                            "perc_id": 98.4334,
                        },
                    }
                ],
            }
        ]
    }
    mock_get.return_value = [type("obj", (object,), {"json": mock_response})]
    results = get_homology_instance.by_species_with_symbol_or_id(
        reference_species="human",
        ensembl_id_or_symbol="ENSG00000157764",
        target_species="macaca_mulatta",
    )
    assert isinstance(results, list)
    assert len(results) > 0
    assert isinstance(results[0], HomologyResult)
    assert results[0].id == "ENSG00000157764"


@patch("fast_bioservices.ensembl.comparative_genomics.GetHomology._get")
def test_by_species_with_symbol_or_id_url_construction(mock_get, get_homology_instance):
    get_homology_instance.by_species_with_symbol_or_id(
        reference_species="human",
        ensembl_id_or_symbol="ENSG00000157764",
        aligned=False,
        cigar_line=False,
        compara="vertebrates",
        external_db="test_db",
        format="full",
        sequence="protein",
        target_species="macaca_mulatta",
        target_taxon=123,
        type="orthologues",
    )
    expected_url = [
        "https://rest.ensembl.org/homology/id/human/ENSG00000157764?compara=vertebrates;format=full;sequence=protein;type=orthologues;external_db=test_db;target_species=macaca_mulatta;target_taxon=123"
    ]
    mock_get.assert_called_with(urls=expected_url, headers={"Content-Type": "application/json"})
