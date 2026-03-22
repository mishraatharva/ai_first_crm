from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, Column, Integer, String, Text
Base = declarative_base()

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True)
    hcp_name = Column(String(255))
    date = Column(String(50))
    time = Column(String(50))
    topics = Column(Text)
    sentiment = Column(String(50))
    materials = Column(Text)
    interaction_type = Column(String(50))

def save_to_db(data):

    engine = create_engine("mysql+pymysql://root:toor@localhost/aivoa")
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    
    obj = Interaction(
        hcp_name=data.get("hcp_name"),
        date=data.get("date"),
        time=data.get("time"),
        topics=data.get("topics"),
        sentiment=data.get("sentiment"),
        materials=",".join(data.get("materials", [])),
        interaction_type = data.get("interaction_type")
    )
    
    db.add(obj)
    db.commit()
    db.refresh(obj)
    
    db.close()
    return obj.id