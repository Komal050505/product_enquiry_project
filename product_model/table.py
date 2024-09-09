"""
This Module is for defining SQLAlchemy ORM models related to product enquiry forms.

This module includes the `ProductEnquiryForms` class, which maps to the
`product_enquiry` table in the database. It captures customer information
regarding their enquiries about vehicle products, along with their interaction
details with dealers.
"""

from sqlalchemy import Column, String, Integer, Date, BOOLEAN
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
"""
The `declarative_base()` function from SQLAlchemy is used to create a base 
class for all ORM models, which is assigned to the variable `Base`. This base 
class provides a foundation for defining database models, handling object-relational 
mapping, and enabling inheritance between models.

Classes defined in this module will inherit from `Base`, ensuring they are properly 
mapped to their corresponding database tables.
"""


class ProductEnquiryForms(Base):
    """
    SQLAlchemy ORM class representing the 'product_enquiry' table.

    This table stores customer information, vehicle model inquiries, and dealer
    interactions regarding potential vehicle purchases.

    Attributes:
        CustomerName (str): The name of the customer making the enquiry.
        Gender (str): The gender of the customer.
        Age (int): The age of the customer.
        Occupation (str): The occupation of the customer.
        MobileNo (int): The primary key representing the mobile number of the customer.
        Email (str): The email address of the customer.
        VehicleModel (str): The vehicle model the customer is interested in.
        State (str): The state where the customer resides.
        District (str): The district where the customer resides.
        City (str): The city where the customer resides.
        ExistingVehicle (str): The vehicle model that the customer currently owns.
        DealerState (str): The state where the dealer is located.
        DealerTown (str): The town where the dealer is located.
        DealerName (str): The name of the dealer handling the enquiry.
        BriefAboutEnquiry (str): A brief description of the enquiry.
        ExpectedDateofPurchase (date): The expected purchase date from the customer.
        SentToDealer (bool): Boolean indicating if the enquiry was sent to the dealer.
        DealerCode (int): Code of the dealer handling the enquiry.
        LeadId (int): Lead identifier associated with the enquiry.
        CreatedDate (date): The date when the enquiry was created.
        IsPurchased (bool): Boolean indicating whether the customer purchased the vehicle.
    """
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
