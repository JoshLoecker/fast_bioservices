from enum import Enum

from fast_bioservices.common import from_string


class Input(Enum):
    """These are valid input database types for the BioDBNet API."""

    AFFY_GENECHIP_ARRAY = "Affy GeneChip Array"
    AFFY_ID = "Affy ID"
    AFFY_TRANSCRIPT_CLUSTER_ID = "Affy Transcript Cluster ID"
    AGILENT_ID = "Agilent ID"
    BIOCARTA_PATHWAY_NAME = "Biocarta Pathway Name"
    CODELINK_ID = "CodeLink ID"
    DBSNP_ID = "dbSNP ID"
    DRUGBANK_DRUG_ID = "DrugBank Drug ID"
    DRUGBANK_DRUG_NAME = "DrugBank Drug Name"
    EC_NUMBER = "EC Number"
    ENSEMBL_GENE_ID = "Ensembl Gene ID"
    ENSEMBL_PROTEIN_ID = "Ensembl Protein ID"
    ENSEMBL_TRANSCRIPT_ID = "Ensembl Transcript ID"
    EST_ACCESSION = "EST Accession"
    FLYBASE_GENE_ID = "FlyBase Gene ID"
    GENBANK_NUCLEOTIDE_ACCESSION = "GenBank Nucleotide Accession"
    GENBANK_PROTEIN_ACCESSION = "GenBank Protein Accession"
    GENE_ID = "Gene ID"
    GENE_SYMBOL = "Gene Symbol"
    GENE_SYMBOL_AND_SYNONYMS = "Gene Symbol and Synonyms"
    GENE_SYMBOL_ORDERED_LOCUS = "Gene Symbol Ordered Locus"
    GENE_SYMBOL_ORF = "Gene Symbol ORF"
    GI_NUMBER = "GI Number"
    GO_ID = "GO ID"
    GSEA_STANDARD_NAME = "GSEA Standard Name"
    H_INV_LOCUS_ID = "H-Inv Locus ID"
    H_INV_PROTEIN_ID = "H-Inv Protein ID"
    H_INV_TRANSCRIPT_ID = "H-Inv Transcript ID"
    HGNC_ID = "HGNC ID"
    HMDB_METABOLITE = "HMDB Metabolite"
    HOMOLOGENE_ID = "HomoloGene ID"
    ILLUMINA_ID = "Illumina ID"
    INTERPRO_ID = "InterPro ID"
    IPI_ID = "IPI ID"
    KEGG_COMPOUND_ID = "KEGG Compound ID"
    KEGG_COMPOUND_NAME = "KEGG Compound Name"
    KEGG_DISEASE_ID = "KEGG Disease ID"
    KEGG_DRUG_ID = "KEGG Drug ID"
    KEGG_DRUG_NAME = "KEGG Drug Name"
    KEGG_GENE_ID = "KEGG Gene ID"
    KEGG_PATHWAY_ID = "KEGG Pathway ID"
    MAIZEGDB_ID = "MaizeGDB ID"
    MGI_ID = "MGI ID"
    MIM_ID = "MIM ID"
    MIRBASE_ID = "miRBase ID"
    MIRBASE_MATURE_MIRNA_ACC = "miRBase Mature miRNA Acc"
    NCIPID_PATHWAY_NAME = "NCIPID Pathway Name"
    ORGANISM_SCIENTIFIC_NAME = "Organism Scientific Name"
    PDB_ID = "PDB ID"
    PFAM_ID = "Pfam ID"
    PHARMGKB_ID = "PharmGKB ID"
    PUBCHEM_ID = "PubChem ID"
    REACTOME_PATHWAY_NAME = "Reactome Pathway Name"
    REFSEQ_GENOMIC_ACCESSION = "RefSeq Genomic Accession"
    REFSEQ_MRNA_ACCESSION = "RefSeq mRNA Accession"
    REFSEQ_PROTEIN_ACCESSION = "RefSeq Protein Accession"
    SGD_ID = "SGD ID"
    TAIR_ID = "TAIR ID"
    TAXON_ID = "Taxon ID"
    UNIGENE_ID = "UniGene ID"
    UNIPROT_ACCESSION = "UniProt Accession"
    UNIPROT_ENTRY_NAME = "UniProt Entry Name"
    UNIPROT_PROTEIN_NAME = "UniProt Protein Name"
    UNISTS_ID = "UniSTS ID"

    @classmethod
    def from_string(cls, input_value: str) -> "Input":
        """Create an Input object from a string."""
        return from_string(input_value, cls)


class Output(Enum):
    """These are valid output database types for the BioDBNet API."""

    AFFY_ANNOTATION = "Affy Annotation"
    AFFY_ID = "Affy ID"
    AGILENT_ID = "Agilent ID"
    ALLERGOME_CODE = "Allergome Code"
    APIDB_CRYPTODB_ID = "ApiDB_CryptoDB ID"
    BIND_ID = "BIND ID"
    BIOCARTA_PATHWAY_DESCRIPTION = "Biocarta Pathway Description"
    BIOCARTA_PATHWAY_NAME = "Biocarta Pathway Name"
    BIOCARTA_PATHWAY_TITLE = "Biocarta Pathway Title"
    BIOCYC_ID = "BioCyc ID"
    CCDS_ID = "CCDS ID"
    CHEBI_ID = "ChEBI ID"
    CHROMOSOMAL_LOCATION = "Chromosomal Location"
    CLEANEX_ID = "CleanEx ID"
    CODELINK_ID = "CodeLink ID"
    COG_TERM = "COG Term"
    COSMIC_ID = "COSMIC ID"
    CPDB_PROTEIN_INTERACTOR = "CPDB Protein Interactor"
    CTD_DISEASE_INFO = "CTD Disease Info"
    CTD_DISEASE_NAME = "CTD Disease Name"
    CYGD_ID = "CYGD ID"
    DBSNP_ID = "dbSNP ID"
    DICTYBASE_ID = "dictyBase ID"
    DIP_ID = "DIP ID"
    DISPROT_ID = "DisProt ID"
    DPD_DIN = "DPD DIN"
    DRUGBANK_DRUG_ENZYME_ID = "DrugBank Drug Enzyme ID"
    DRUGBANK_DRUG_ID = "DrugBank Drug ID"
    DRUGBANK_DRUG_INFO = "DrugBank Drug Info"
    DRUGBANK_DRUG_NAME = "DrugBank Drug Name"
    DRUGBANK_DRUG_TARGET_ID = "DrugBank Drug Target ID"
    DRUGBANK_ID = "DrugBank ID"
    EC_NUMBER = "EC Number"
    ECHOBASE_ID = "EchoBASE ID"
    ECOGENE_ID = "EcoGene ID"
    ENSEMBL_BIOTYPE = "Ensembl Biotype"
    ENSEMBL_GENE_ID = "Ensembl Gene ID"
    ENSEMBL_GENE_INFO = "Ensembl Gene Info"
    ENSEMBL_PROTEIN_ID = "Ensembl Protein ID"
    ENSEMBL_TRANSCRIPT_ID = "Ensembl Transcript ID"
    EST_ACCESSION = "EST Accession"
    FLYBASE_GENE_ID = "FlyBase Gene ID"
    FLYBASE_PROTEIN_ID = "FlyBase Protein ID"
    FLYBASE_TRANSCRIPT_ID = "FlyBase Transcript ID"
    FUNCATDB_ID = "FunCatDB ID"
    GAD_DISEASE_INFO = "GAD Disease Info"
    GAD_DISEASE_NAME = "GAD Disease Name"
    GENBANK_NUCLEOTIDE_ACCESSION = "GenBank Nucleotide Accession"
    GENBANK_NUCLEOTIDE_GI = "GenBank Nucleotide GI"
    GENBANK_PROTEIN_ACCESSION = "GenBank Protein Accession"
    GENBANK_PROTEIN_GI = "GenBank Protein GI"
    GENE_ID = "Gene ID"
    GENE_INFO = "Gene Info"
    GENE_SYMBOL = "Gene Symbol"
    GENE_SYMBOL_AND_SYNONYMS = "Gene Symbol and Synonyms"
    GENE_SYMBOL_ORDERED_LOCUS = "Gene Symbol Ordered Locus"
    GENE_SYMBOL_ORF = "Gene Symbol ORF"
    GENE_SYNONYMS = "Gene Synonyms"
    GENEFARM_ID = "GeneFarm ID"
    GI_NUMBER = "GI Number"
    GO_BIOLOGICAL_PROCESS = "GO - Biological Process"
    GO_CELLULAR_COMPONENT = "GO - Cellular Component"
    GO_MOLECULAR_FUNCTION = "GO - Molecular Function"
    GO_ANNOTATION = "GO Annotation"
    GO_ID = "GO ID"
    GSEA_GROUP_MEMBERS = "GSEA Group Members"
    GSEA_STANDARD_NAME = "GSEA Standard Name"
    HINV_LOCUS_ID = "H-Inv Locus ID"
    HINV_PROTEIN_ID = "H-Inv Protein ID"
    HINV_TRANSCRIPT_ID = "H-Inv Transcript ID"
    HAMAP_ID = "HAMAP ID"
    HGNC_ID = "HGNC ID"
    HMDB_ENZYME_GENE_SYMBOL = "HMDB Enzyme - Gene Symbol"
    HMDB_ENZYME_UNIPROT_ENTRY_NAME = "HMDB Enzyme - UniProt Entry Name"
    HMDB_METABOLITE = "HMDB Metabolite"
    HMDB_METABOLITE_DESC = "HMDB Metabolite Desc"
    HMDB_METABOLITE_ID = "HMDB Metabolite ID"
    HOMOLOG_ALL_ENS_GENE_ID = "Homolog - All Ens Gene ID"
    HOMOLOG_ALL_ENS_PROTEIN_ID = "Homolog - All Ens Protein ID"
    HOMOLOG_ALL_GENE_ID = "Homolog - All Gene ID"
    HOMOLOG_HUMAN_ENS_GENE_ID = "Homolog - Human Ens Gene ID"
    HOMOLOG_HUMAN_ENS_PROTEIN_ID = "Homolog - Human Ens Protein ID"
    HOMOLOG_HUMAN_GENE_ID = "Homolog - Human Gene ID"
    HOMOLOG_MOUSE_ENS_GENE_ID = "Homolog - Mouse Ens Gene ID"
    HOMOLOG_MOUSE_ENS_PROTEIN_ID = "Homolog - Mouse Ens Protein ID"
    HOMOLOG_MOUSE_GENE_ID = "Homolog - Mouse Gene ID"
    HOMOLOG_RAT_ENS_GENE_ID = "Homolog - Rat Ens Gene ID"
    HOMOLOG_RAT_ENS_PROTEIN_ID = "Homolog - Rat Ens Protein ID"
    HOMOLOG_RAT_GENE_ID = "Homolog - Rat Gene ID"
    HOMOLOGENE_ID = "HomoloGene ID"
    HPA_ID = "HPA ID"
    HPRD_ID = "HPRD ID"
    HPRD_PROTEIN_COMPLEX = "HPRD Protein Complex"
    HPRD_PROTEIN_INTERACTOR = "HPRD Protein Interactor"
    ILLUMINA_ID = "Illumina ID"
    IMGT_GENEDB_ID = "IMGT/GENE-DB ID"
    INTACT_ID = "IntAct ID"
    INTERPRO_ID = "InterPro ID"
    IPI_ID = "IPI ID"
    KEGG_COMPOUND_ID = "KEGG Compound ID"
    KEGG_COMPOUND_NAME = "KEGG Compound Name"
    KEGG_DISEASE_ID = "KEGG Disease ID"
    KEGG_DISEASE_INFO = "KEGG Disease Info"
    KEGG_DRUG_ID = "KEGG Drug ID"
    KEGG_DRUG_INFO = "KEGG Drug Info"
    KEGG_DRUG_NAME = "KEGG Drug Name"
    KEGG_GENE_ID = "KEGG Gene ID"
    KEGG_ORTHOLOGY_ID = "KEGG Orthology ID"
    KEGG_PATHWAY_ID = "KEGG Pathway ID"
    KEGG_PATHWAY_INFO = "KEGG Pathway Info"
    KEGG_PATHWAY_TITLE = "KEGG Pathway Title"
    KEGG_REACTION_ID = "KEGG Reaction ID"
    LEGIOLIST_ID = "LegioList ID"
    LEPROMA_ID = "Leproma ID"
    LOCUS_TAG = "Locus Tag"
    MAIZEGDB_ID = "MaizeGDB ID"
    MEROPS_ID = "MEROPS ID"
    METACYC_REACTION = "MetaCyc Reaction"
    MGC_ZGC_XGC_ID = "MGC(ZGC/XGC) ID"
    MGC_ZGC_XGC_IMAGE_ID = "MGC(ZGC/XGC) Image ID"
    MGC_ZGC_XGC_INFO = "MGC(ZGC/XGC) Info"
    MGI_ID = "MGI ID"
    MIM_ID = "MIM ID"
    MIM_INFO = "MIM Info"
    MINT_ID = "MINT ID"
    MIRBASE_ID = "miRBase ID"
    MIRBASE_MATURE_MIRNA_ACC = "miRBase Mature miRNA Acc"
    MULTIFUN_ID = "MultiFun ID"
    NCIPID_PATHWAY_DESCRIPTION = "NCIPID Pathway Description"
    NCIPID_PATHWAY_NAME = "NCIPID Pathway Name"
    NCIPID_PATHWAY_TITLE = "NCIPID Pathway Title"
    NCIPID_PROTEIN_COMPLEX = "NCIPID Protein Complex"
    NCIPID_PROTEIN_INTERACTOR = "NCIPID Protein Interactor"
    NCIPID_PTM = "NCIPID PTM"
    ORGANISM_SCIENTIFIC_NAME = "Organism Scientific Name"
    ORPHANET_ID = "Orphanet ID"
    PANTHER_ID = "PANTHER ID"
    PARALOG_ENS_GENE_ID = "Paralog - Ens Gene ID"
    PBR_ID = "PBR ID"
    PDB_ID = "PDB ID"
    PEROXIBASE_ID = "PeroxiBase ID"
    PFAM_ID = "Pfam ID"
    PHARMGKB_DISEASE_ID = "PharmGKB Disease ID"
    PHARMGKB_DRUG_ID = "PharmGKB Drug ID"
    PHARMGKB_DRUG_INFO = "PharmGKB Drug Info"
    PHARMGKB_GENE_ID = "PharmGKB Gene ID"
    PIR_ID = "PIR ID"
    PIRSF_ID = "PIRSF ID"
    PPTASEDB_ID = "PptaseDB ID"
    PRINTS_ID = "PRINTS ID"
    PRODOM_ID = "ProDom ID"
    PROSITE_ID = "PROSITE ID"
    PSEUDOCAP_ID = "PseudoCAP ID"
    PUBCHEM_ID = "PubChem ID"
    PUBMED_ID = "PubMed ID"
    REACTOME_ID = "Reactome ID"
    REACTOME_PATHWAY_DESCRIPTION = "Reactome Pathway Description"
    REACTOME_PATHWAY_NAME = "Reactome Pathway Name"
    REBASE_ID = "REBASE ID"
    REFSEQ_GENOMIC_ACCESSION = "RefSeq Genomic Accession"
    REFSEQ_GENOMIC_GI = "RefSeq Genomic GI"
    REFSEQ_MRNA_ACCESSION = "RefSeq mRNA Accession"
    REFSEQ_NCRNA_ACCESSION = "RefSeq ncRNA Accession"
    REFSEQ_NUCLEOTIDE_GI = "RefSeq Nucleotide GI"
    REFSEQ_PROTEIN_ACCESSION = "RefSeq Protein Accession"
    REFSEQ_PROTEIN_GI = "RefSeq Protein GI"
    RFAM_ID = "Rfam ID"
    RGD_ID = "RGD ID"
    SCOP_ID = "SCOP ID"
    SGD_ID = "SGD ID"
    SMART_ID = "SMART ID"
    SNP_INFO = "SNP Info"
    SP_KEYWORDS_ACCESSION = "SP Keywords Accession"
    SP_SUBCELLULAR_LOCATION_ACC = "SP Subcellular Location Acc"
    STRING_PROTEIN_INTERACTOR = "STRING Protein Interactor"
    TAIR_ID = "TAIR ID"
    TAXON_ID = "Taxon ID"
    TCDB_ID = "TCDB ID"
    TIGRFAMS_ID = "TIGRFAMs ID"
    TISSUE_EXPRESSED_IN = "Tissue (expressed in)"
    TUBERCULIST_ID = "TubercuList ID"
    UCSC_ID = "UCSC ID"
    UMBBD_ENZYME_ID = "UM-BBD Enzyme ID"
    UMBBD_PATHWAY_ID = "UM-BBD Pathway ID"
    UNIGENE_ID = "UniGene ID"
    UNIGENE_SEQUENCE_ACCESSION = "UniGene Sequence Accession"
    UNIPROT_ACCESSION = "UniProt Accession"
    UNIPROT_ENTRY_NAME = "UniProt Entry Name"
    UNIPROT_INFO = "UniProt Info"
    UNIPROT_PROTEIN_NAME = "UniProt Protein Name"
    UNISTS_ID = "UniSTS ID"
    UNISTS_INFO = "UniSTS Info"
    VECTORBASE_GENE_ID = "VectorBase Gene ID"
    VEGA_GENE_ID = "VEGA Gene ID"
    VEGA_PROTEIN_ID = "VEGA Protein ID"
    VEGA_TRANSCRIPT_ID = "VEGA Transcript ID"
    WORMBASE_GENE_ID = "WormBase Gene ID"
    WORMPEP_PROTEIN_ID = "WormPep Protein ID"
    XENBASE_GENE_ID = "XenBase Gene ID"
    ZFIN_ID = "ZFIN ID"

    @classmethod
    def from_string(cls, input_value: str) -> "Output":
        """Create an Output object from a string."""
        return from_string(input_value, cls)
