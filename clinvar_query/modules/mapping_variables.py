from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, MetaData, insert, Text, delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, class_mapper


#define table as Python classes using a declarative base

class base_table(DeclarativeBase):
    pass

class patient_information(base_table):
    __tablename__ = "patient_information"

    patient_id =  mapped_column(String (20))
    id_test_type = mapped_column(String(25), primary_key=True)

    variants_rows = relationship("variants", back_populates="patient_information")
class variants(base_table):
    __tablename__ = "variants"

    patient_variant = Column(Integer, primary_key=True, autoincrement=True)
    variant_id = mapped_column(String (25))
    id_test_type = mapped_column(String(25), ForeignKey("patient_information.id_test_type"))

    patient_information = relationship("patient_information", back_populates = "variants_rows")
    variant_info_rows = relationship("variant_info", back_populates = "variants")

class clinvar(base_table):
    __tablename__ = "clinvar"

    mane_select = mapped_column(String (25), ForeignKey("variant_info.mane_select"), primary_key=True)
    consensus_classification = mapped_column(String (25))
    hgnc_id = mapped_column(String (25), ForeignKey("variant_info.hgnc_id"))

    variant_info = relationship("variant_info", back_populates = "clinvar_rows", foreign_keys = [hgnc_id])


class variant_info(base_table):
    __tablename__ = "variant_info"
    variant_id = mapped_column(String(25), ForeignKey("variants.variant_id"), primary_key=True)
    chromosome = mapped_column (String(5))
    hgnc_id = mapped_column(String (25))
    gene_symbol =  mapped_column (String(20))
    mane_select = mapped_column (String(25))

    variants = relationship("variants", back_populates ="variant_info_rows")
    clinvar_rows = relationship("clinvar", back_populates= "variant_info", foreign_keys = [clinvar.hgnc_id])

engine = create_engine("sqlite:///clinvar_query/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db")
litesession = sessionmaker(bind=engine)
search_register = {}




def initialise_database():
    """This initialises the dummy database"""
    base_table.metadata
    MetaData()
    engine = create_engine("sqlite:///clinvar_query/ClinVar_Site/Clinvar_Database_folder/ClinVar_Database.db")
    litesession = sessionmaker(bind=engine)
    base_table.metadata.create_all(engine)
    insert_patient_info = insert(patient_information).values([
            {"patient_id" : "123456789", "id_test_type": "123456789PD"},
            {"patient_id" : "987654321", "id_test_type": "987654321PD"},
            {"patient_id" : "112112321", "id_test_type": "112112321PD"},
    ])
    insert_variants = insert(variants).values([
            {"patient_variant" : 1,  "variant_id" : "12-40294866-G-T", "id_test_type": "123456789PD"},
            {"patient_variant" : 2, "variant_id" : "6-162262690-T-C", "id_test_type": "987654321PD"},
            {"patient_variant" : 3, "variant_id" : "17-44349727-G-A", "id_test_type": "112112321PD"},
            {"patient_variant" : 4, "variant_id" : "17-44349727-G-A", "id_test_type": "123456789PD"},
            {"patient_variant" : 5, "variant_id" : "6-162262690-T-C", "id_test_type": "112112321PD"},
    ])
    insert_variant_info = insert(variant_info).values([
            {"variant_id" : "12-40294866-G-T", "chromosome" : "12" , "hgnc_id" : "HGNC:18618", "gene_symbol" : "LRRK2" , "mane_select" : "NM_198578.4:c.2830G>T" },
            {"variant_id" : "6-162262690-T-C", "chromosome": "6" , "hgnc_id" : "HGNC:8607","gene_symbol" : "PRKN", "mane_select" : "NM_004562.3:c.247A>G"},
            {"variant_id" : "17-44349727-G-A", "chromosome": "17", "hgnc_id":  "HGNC:4601", "gene_symbol" : "GRN", "mane_select": "NM_002087.4:c.325G>A"},
    ])
    insert_clinvar = insert(clinvar).values([
            {"mane_select" : "NM_198578.4:c.2830G>T", "consensus_classification" : "not provided, 0 stars", "hgnc_id" : "HGNC:18618"},
            {"mane_select" :"NM_004562.3:c.247A>G", "consensus_classification" : "Uncertain significance, 2 stars", "hgnc_id" : "HGNC:8607"},
            {"mane_select" : "NM_002087.4:c.325G>A", "consensus_classification" : "Uncertain significance, 1 star","hgnc_id":  "HGNC:4601"},
    ])    

    with litesession() as session:
        session.execute(insert_patient_info)
        session.execute(insert_variants)
        session.execute(insert_variant_info)
        session.execute(insert_clinvar)
        session.commit()


def search_register_creation():
    """This creates a registry to map all the ORM mappings/relationships in the database,
    so that they can be looped over pythonically
    This returns a search register, 
    in which searches can be mapped on to any column in the database
    to see where there would be matches"""
    for data in base_table.registry.mappers:
        register = data.class_
        mapper = class_mapper(register)

        text_columns = [col for col in mapper.columns
            if isinstance(col.type, (String, Text))]
        
        if text_columns:
            search_register[register] = text_columns
        
    return search_register

def convert_gene_to_hgnc(session, query_data):
    """ , a function was added to convert the gene symbol (gene_symbol) into hgnc_id. 
    This will query the current session and look through it to find if the query data, the data put into the search bar,
    matches any given gene name in the variant info table. If it does, then it will find the corresponding HGNC_id.
    Example input: PRKN
    Example output: search?q=HGNC:8607 """
    variant_info_entry = session.query(variant_info).filter(
        (variant_info.gene_symbol.ilike(query_data)) | (variant_info.hgnc_id.ilike(query_data))
    ).first()

    if not variant_info_entry:
        return query_data
    
    return variant_info_entry.hgnc_id

def convert_lookup_to_dictionary(base_table):
    return {
        c.name: getattr(base_table)
    }

def update_tables():
    """This updates the table, this currently uses dummy values, but essentially
    when the process is sent off to the apis, the data will then populate the database
    this is an example of how it could work.
    The function is added to the start of result, 
    thus should evaluate changes and update accordingly"""
    update_patient_info = insert(patient_information).values([
        {"patient_id" : "123454321", "id_test_type": "123454321PD"},
    ])
    insert_new_variants = insert(variants).values([
        {"patient_variant" : 6,  "variant_id" : "19-41985036-A-C", "id_test_type": "123456789PD"},
        {"patient_variant" : 7,  "variant_id" : "4-89822305-C-G", "id_test_type": "987654321PD"},
        {"patient_variant" : 8,  "variant_id" : "6-161973317-G-A", "id_test_type": "112112321PD"},
        {"patient_variant" : 9,  "variant_id" : "1-7962813-C-G", "id_test_type": "123454321PD"},

        
    ])
    with litesession() as session:
        session.execute(update_patient_info)
        session.execute(insert_new_variants)
        session.commit()

def remove_from_single_table():
    delete_patient_info = delete(patient_information).where(patient_information.id_test_type.in_(["123456789PD"]))

    with litesession() as session:
        session.execute(delete_patient_info)
        session.commit()    
def remove_from_all_tables():
    for data in base_table.__subclasses__():
        for column in data.__table__.columns:
            if isinstance(column.type, (Integer, String, Text)) and column.type == type("123456789PD"):
                delete_all_patient_info = delete(data).where(column=="123456789PD")
                with litesession() as session:
                    session.execute(delete_all_patient_info)
                    session.commit()  
if __name__ == "__main__":
    initialise_database()
    search_register_creation()
