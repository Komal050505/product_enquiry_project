from sqlalchemy.exc import SQLAlchemyError

from logging_package.logging_utility import log_info, log_error
from product_model.table import ProductEnquiryForms
from db_connections.configurations import session


def is_customer_valid(MobileNo):
    result = session.query(ProductEnquiryForms).filter(ProductEnquiryForms.name == MobileNo).all()
    if result:
        return True
    else:
        return False


def record_to_dict(record):
    """
    Converts a SQLAlchemy model instance to a dictionary.

    :param record: SQLAlchemy model instance
    :return: Dictionary representation of the record
    """
    record_dict = {
        "CustomerName": record.CustomerName,
        "Gender": record.Gender,
        "Age": record.Age,
        "Occupation": record.Occupation,
        "MobileNo": record.MobileNo,
        "Email": record.Email,
        "VehicleModel": record.VehicleModel,
        "State": record.State,
        "District": record.District,
        "City": record.City,
        "ExistingVehicle": record.ExistingVehicle,
        "DealerState": record.DealerState,
        "DealerTown": record.DealerTown,
        "DealerName": record.DealerName,
        "BriefAboutEnquiry": record.BriefAboutEnquiry,
        "ExpectedDateofPurchase": record.ExpectedDateofPurchase.isoformat() if record.ExpectedDateofPurchase else None,
        "SentToDealer": record.SentToDealer,
        "DealerCode": record.DealerCode,
        "LeadId": record.LeadId,
        "CreatedDate": record.CreatedDate.isoformat() if record.CreatedDate else None,
        "IsPurchased": record.IsPurchased
    }
    return record_dict


def reset_sent_flag(dealercode):
    """
    Resets the SentToDealer flag for a given dealer code.
    :param dealercode: Dealer code to reset flags
    """
    try:
        records = session.query(ProductEnquiryForms).filter(
            ProductEnquiryForms.DealerCode == dealercode
        ).all()

        for record in records:
            record.SentToDealer = False
            session.add(record)

        session.commit()
        log_info(f"SentToDealer flags reset for dealer code: {dealercode}.")
    except SQLAlchemyError as e:
        session.rollback()
        log_error(f"Error resetting SentToDealer flags: {str(e)}")
    finally:
        session.close()
