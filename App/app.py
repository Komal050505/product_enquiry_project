import os
from flask import Flask, request
from flask_restful import Api
from sqlalchemy import and_

from db_connections.configurations import session
from product_model.table import ProductEnquiryForms

app = Flask(__name__)
api = Api(app)


@app.route('/post_records', methods=['POST'])
def post_records():
    request_body = request.get_json(force=True)
    for index, item in enumerate(request_body):
        record = ProductEnquiryForms(CustomerName=item["CustomerName"],
                                     Gender=item["Gender"],
                                     Age=item["Age"],
                                     Occupation=item["Occupation"],
                                     MobileNo=item["MobileNo"],
                                     Email=item["Email"],
                                     VehicleModel=item["VehicleModel"],
                                     State=item["State"],
                                     District=item["District"],
                                     City=item["City"],
                                     ExistingVehicle=item["ExistingVehicle"],
                                     DealerState=item["DealerState"],
                                     DealerTown=item["DealerTown"],
                                     DealerName=item["DealerName"],
                                     BriefAboutEnquiry=item["BriefAboutEnquiry"],
                                     ExpectedDateofPurchase=item["ExpectedDateofPurchase"],
                                     SentToDealer=item["SentToDealer"],
                                     DealerCode=item["DealerCode"],
                                     LeadId=item["LeadId"],
                                     CreatedDate=item["CreatedDate"],
                                     IsPurchased=item["IsPurchased"])

        session.add_all([record])
        session.commit()
    return "data inserted"


@app.route('/get-home-page', methods=['GET'])
def get_home_page():
    dealercode = request.args.get("dealercode")
    print("dealer code is", dealercode)
    result = session.query(ProductEnquiryForms).filter(ProductEnquiryForms.SentToDealer == 'False',
                                                       ProductEnquiryForms.DealerCode == dealercode).all()
    print(type(result))
    result = [item.__dict__ for item in result]
    mobileno_container = []
    for item in result:
        item.pop('_sa_instance_state')
        mobileno_container.append(item.get('MobileNo'))
    enable_sent_flag(mobileno_container)
    return str(result)


@app.route('/get-home-page1', methods=['GET'])
def get_home_page1():
    result = session.query(ProductEnquiryForms).all()
    print(type(result))
    result = [item.__dict__ for item in result]

    for item in result:
        item.pop('_sa_instance_state')

    return str(result)


def enable_sent_flag(mobileno_container):
    print("Container {}".format(mobileno_container))
    for mobileno in mobileno_container:
        session.query(ProductEnquiryForms).filter(ProductEnquiryForms.MobileNo == mobileno) \
            .update({"SentToDealer": True})
        session.commit()


def sent_flag(customer):
    print("customer {}".format(customer))
    # senttodealer flag is updated as True in original table
    for number in customer:
        session.query(ProductEnquiryForms).filter(ProductEnquiryForms.MobileNo == number). \
            update({"SentToDealer": True})
        session.commit()


@app.route('/get_single_record', methods=['GET'])
def get_single_record():
    leadid = request.args.get("leadid")
    result = session.query(ProductEnquiryForms).filter(ProductEnquiryForms.LeadId == leadid).all()
    result = [item.__dict__ for item in result]
    for item in result:
        item.pop('_sa_instance_state')
    return str(result)


# querying using limit
@app.route('/get_limited_records', methods=['GET'])
def get_limited_records():
    result = session.query(ProductEnquiryForms).limit(os.getenv("LIMIT")).offset(0).all()
    result = [item.__dict__ for item in result]
    for item in result:
        item.pop('_sa_instance_state')
    return str(result)


@app.route('/get_limited_records1', methods=['GET'])
def get_limited_records1():
    # Limit: How many leads to distribute, offset: Stating point
    result = session.query(ProductEnquiryForms).limit(3).offset(2).all()
    result = [item.__dict__ for item in result]
    for item in result:
        item.pop('_sa_instance_state')
    return str(result)


@app.route('/historic_leads', methods=['GET'])
def get_historic_leads():
    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    result = session.query(ProductEnquiryForms).filter(and_(ProductEnquiryForms.CreatedDate >= start_date,
                                                            ProductEnquiryForms.CreatedDate <= end_date)).all()
    result = [item.__dict__ for item in result]
    for item in result:
        item.pop('_sa_instance_state')
    return str(result)


@app.route('/purchased_historic_leads', methods=['GET'])
def get_purchased_leads():
    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    dealer_code = request.args.get("dealercode")
    result = session.query(ProductEnquiryForms).filter(and_(ProductEnquiryForms.CreatedDate >= start_date,
                                                            ProductEnquiryForms.CreatedDate <= end_date,
                                                            ProductEnquiryForms.IsPurchased == 'True',
                                                            ProductEnquiryForms.DealerCode == dealer_code)).all()
    result = [item.__dict__ for item in result]
    for item in result:
        item.pop('_sa_instance_state')
    return str(result)


# method to get not purchased leads for required time period in date format for each dealer code
@app.route('/not_purchased_historic_leads', methods=['GET'])
def get_not_purchased_leads():
    start_date = request.args.get("startdate")
    end_date = request.args.get("enddate")
    dealer_code = request.args.get("dealercode")
    result = session.query(ProductEnquiryForms).filter(and_(ProductEnquiryForms.CreatedDate >= start_date,
                                                            ProductEnquiryForms.CreatedDate <= end_date,
                                                            ProductEnquiryForms.IsPurchased == 'False',
                                                            ProductEnquiryForms.DealerCode == dealer_code)).all()
    result = [item.__dict__ for item in result]
    for item in result:
        item.pop('_sa_instance_state')
    return str(result)


@app.route('/put_record', methods=['PUT'])
def put_record():
    request_body = request.get_json(force=True)
    try:
        result = session.query(ProductEnquiryForms). \
            filter(ProductEnquiryForms.MobileNo == ProductEnquiryForms(request_body[0]["mobileno"])) \
            .update(record=ProductEnquiryForms(request_body[0]["briefaboutenquiry"]))
        session.commit()
        return str(result)
    finally:
        session.close()


@app.route('/patch_record', methods=['PATCH'])
def patch_record():
    print("parameter is {}".format(request.args))
    cust_name = request.args.get("customername")
    try:
        session.query(ProductEnquiryForms).filter(ProductEnquiryForms.CustomerName == cust_name) \
            .update({"DealerCode": 5})
        session.commit()
        return "It is Updated"
    finally:
        session.close()


@app.route('/del_single_record', methods=['DELETE'])
def del_record():
    from flask import request
    print("parameter is {}".format(request.args))
    date = request.args.get("expecteddateofpurchase")
    try:
        result = session.query(ProductEnquiryForms).filter(ProductEnquiryForms.ExpectedDateofPurchase < date).delete()
        session.commit()
        return str(result)
    finally:
        pass


if __name__ == "__main__":
    app.run(debug=True)
