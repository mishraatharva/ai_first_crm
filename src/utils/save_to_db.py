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

def delete_by_id(interaction_id):
    engine = create_engine("mysql+pymysql://root:toor@localhost/aivoa")
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    
    obj = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if obj:
        db.delete(obj)
        db.commit()
        db.close()
        return True
    else:
        db.close()
        return False

def delete_by_filters(filters):
    engine = create_engine("mysql+pymysql://root:toor@localhost/aivoa")
    SessionLocal = sessionmaker(bind=engine)
    
    db = SessionLocal()
    query = db.query(Interaction)
    
    # APPLY FILTERS DYNAMICALLY
    for key, value in filters.items():
        if key == "hcp_name":
            query = query.filter(Interaction.hcp_name.ilike(f"%{value}%"))
        elif key == "materials":
            query = query.filter(Interaction.materials.ilike(f"%{value}%"))
        else:
            query = query.filter(getattr(Interaction, key) == value)
    
    results = query.all()
    if not results:
        db.close()
        return 0  # No records deleted
    
    count = 0
    for obj in results:
        db.delete(obj)
        count += 1
    
    db.commit()
    db.close()
    return count