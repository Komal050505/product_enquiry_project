from sqlalchemy import Column, String, Integer, Date, BOOLEAN
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class ProductEnquiryForms(Base):
    __tablename__ = 'product_enquiry'
    CustomerName = Column("customername", String)
    Gender = Column("gender", String)
    Age = Column("age", Integer)
    Occupation = Column("occupation", String)
    MobileNo = Column("mobileno", Integer, primary_key=True)
    Email = Column("email", String)
    VehicleModel = Column("vehiclemodel", String)
    State = Column("state", String)
    District = Column("district", String)
    City = Column("city", String)
    ExistingVehicle = Column("existingvehicle", String)
    DealerState = Column("dealerstate", String)
    DealerTown = Column("dealertown", String)
    DealerName = Column("dealername", String)
    BriefAboutEnquiry = Column("briefaboutenquiry", String)
    ExpectedDateofPurchase = Column("expecteddateofpurchase", Date)
    SentToDealer = Column("senttodealer", BOOLEAN)
    DealerCode = Column("dealercode", Integer)
    LeadId = Column("leadid", Integer)
    CreatedDate = Column("createddate", Date)
    IsPurchased = Column("ispurchased", BOOLEAN)
