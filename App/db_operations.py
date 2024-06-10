from product_model.table import ProductEnquiryForms
from db_connections.configurations import session


def is_customer_valid(MobileNo):
    result = session.query(ProductEnquiryForms).filter(ProductEnquiryForms.name == MobileNo).all()
    if result:
        return True
    else:
        return False
