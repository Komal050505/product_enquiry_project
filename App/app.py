"""
This module contains the actual api's implementations.

"""
# These are Standard library imports (built-in modules)
import os
from datetime import date, datetime

# These are Flask imports (for handling web requests and responses)
from flask import Flask, request, jsonify
from flask_restful import Api

# These are SQLAlchemy imports (for ORM and database operations)
from sqlalchemy import and_, inspect, func
from sqlalchemy.exc import SQLAlchemyError

# These are Application-specific imports (for email handling and session management)
from App.email_configurations import RECEIVER_EMAIL, SENDER_EMAIL
from App.email_operations import notify_failure, notify_success, format_enquiries_for_email, format_dealers_for_email
from db_connections.configurations import session
from product_model.table import ProductEnquiryForms

# These are Logging imports (for logging operations in the application)
from logging_package.logging_utility import log_info, log_error, log_debug, log_warning
from utils.reusables import record_to_dict

app = Flask(__name__)
api = Api(app)


@app.route('/get-primary-key-details', methods=['GET'])
def get_primary_key_details():
    """
    Endpoint to retrieve primary key details for the ProductEnquiryForms table.

    :return: JSON response with primary key details or an error message.
    """
    log_info("GET /get_primary_key_details - Started processing request.")

    try:
        mapper = inspect(ProductEnquiryForms)
        primary_keys = mapper.primary_key

        if not primary_keys:
            log_warning("GET /get_primary_key_details - No primary keys found for ProductEnquiryForms.")
            return jsonify({
                "message": "No primary keys found for ProductEnquiryForms."
            }), 404

        primary_key_details = [column.name for column in primary_keys]
        record_count = len(primary_key_details)

        log_info(f"GET /get_primary_key_details - Retrieved {record_count} primary key(s) for ProductEnquiryForms.")

        notification_message = (
                f"Primary Key Details:\n\n"
                f"Total Primary Keys: {record_count}\n\n"
                f"Keys:\n" + "\n".join(primary_key_details)
        )
        notify_success(
            "Primary Key Details Retrieved Successfully",
            notification_message
        )

        return jsonify({
            "message": "Primary key details retrieved successfully",
            "total_primary_keys": record_count,
            "primary_keys": primary_key_details
        }), 200

    except Exception as e:
        log_error(f"GET /get_primary_key_details - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while retrieving primary key details.\n\nError details:\n{str(e)}"
        )
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

    finally:
        session.close()
        log_info("GET /get_primary_key_details - Session closed.")
        log_info("GET /get_primary_key_details - Finished processing request.")


@app.route('/get-enquiries-by-date', methods=['GET'])
def get_enquiries_by_date():
    """
      Retrieve product enquiries based on a date range.

      This function allows users to search for product enquiries between a specified start date
      and end date. Both `start_date` and `end_date` should be provided as query parameters
      in the 'dd-mm-yyyy' format. The function returns all matching enquiries, along with the
      total count of records found.

      Parameters:
          - start_date (str): The start of the date range in 'dd-mm-yyyy' format.
          - end_date (str): The end of the date range in 'dd-mm-yyyy' format.

      Returns:
           A JSON response of records with detailed email notification
      """
    try:
        log_info("Starting function: get_enquiries_by_date")

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        log_info(f"Received start_date: {start_date}, end_date: {end_date}")

        if not start_date or not end_date:
            log_warning("Missing required parameters: start_date or end_date")
            return jsonify({'error': 'start_date and end_date are required parameters'}), 400

        start_date_obj = datetime.strptime(start_date, '%d-%m-%Y')
        end_date_obj = datetime.strptime(end_date, '%d-%m-%Y')

        log_debug(f"Converted start_date: {start_date_obj}, end_date: {end_date_obj}")

        enquiries = session.query(ProductEnquiryForms).filter(
            ProductEnquiryForms.CreatedDate >= start_date_obj,
            ProductEnquiryForms.CreatedDate <= end_date_obj
        ).all()

        total_count = len(enquiries)
        log_info(f"Total enquiries retrieved: {total_count}")

        enquiries_data = [record_to_dict(enquiry) for enquiry in enquiries]

        subject = "Enquiry Retrieval Success"
        body = f"""Successfully retrieved {total_count} enquiries between {start_date} and {end_date}.
        \nDetails of the records:
        {format_enquiries_for_email(enquiries_data)}
        """
        notify_success(subject, body)

        log_info(f"Successfully retrieved {total_count} enquiries")

        return jsonify({'total_count': total_count, 'enquiries': enquiries_data}), 200

    except Exception as e:
        log_error(f"Error retrieving enquiries by date range: {str(e)}")

        subject = "Enquiry Retrieval Failure"
        body = f"""
        Failed to retrieve enquiries between {start_date} and {end_date}.
        \nError: {str(e)}
        """
        notify_failure(subject, body)

        return jsonify({'error': 'Failed to retrieve enquiries'}), 500

    finally:
        log_info("Ending function: get_enquiries_by_date")


@app.route('/get-enquiries-by-vehicle-model', methods=['GET'])
def get_enquiries_by_vehicle_model():
    """
       Fetch enquiries based on the vehicle model.

       This function allows users to search for product enquiries by providing the vehicle model
       as a query parameter. You can choose whether the search is case-sensitive or not by setting
       the `case_sensitive` flag. The function will return a list of matching enquiries, along with
       the total number of results found.

       Parameters:
           - vehicle_model (str): The vehicle model to search for.

       Returns:
           JSON response with detaied records and total records with matching details

       """
    try:
        log_info("Starting function: get_enquiries_by_vehicle_model")

        vehicle_model = request.args.get('vehicle_model')
        case_sensitive = request.args.get('case_sensitive', 'false').lower() == 'true'
        log_info(f"Received vehicle_model: {vehicle_model}, case_sensitive: {case_sensitive}")

        if not vehicle_model:
            log_warning("Vehicle model is required but not provided")
            return jsonify({"error": "Vehicle model is required"}), 400

        if case_sensitive:  # If vehicle model contains like Thar-4X, Maruti-VDI which involves in case sensitive
            log_info("Performing case-sensitive partial search")
            enquiries = session.query(ProductEnquiryForms).filter(
                ProductEnquiryForms.VehicleModel.like(f'%{vehicle_model}%')
            ).all()
        else:  # Else it performs case-insensitive search
            log_info("Performing case-insensitive partial search")
            enquiries = session.query(ProductEnquiryForms).filter(
                func.lower(ProductEnquiryForms.VehicleModel).like(f'%{vehicle_model.lower()}%')
            ).all()

        if not enquiries:
            log_info(f"No enquiries found for vehicle model: {vehicle_model}")
            return jsonify({"message": "No enquiries found for this vehicle model"}), 404

        total_count = len(enquiries)
        log_info(f"Found {total_count} enquiries for vehicle model: {vehicle_model}")

        enquiries_data = [record_to_dict(enquiry) for enquiry in enquiries]

        subject = "Enquiry Retrieval Success by Vehicle Model"
        body = f"""
        Successfully retrieved {total_count} enquiries for vehicle model: {vehicle_model}.
        Case-sensitive search: {'Yes' if case_sensitive else 'No'}.
        \nDetails of the records:
        {format_enquiries_for_email(enquiries_data)}
        """
        notify_success(subject, body)

        log_info(f"Successfully retrieved {total_count} enquiries for vehicle model: {vehicle_model}")

        return jsonify({"total_count": total_count, "enquiries": enquiries_data}), 200

    except Exception as e:
        log_error(f"Error retrieving enquiries by vehicle model: {str(e)}")

        subject = "Enquiry Retrieval Failure by Vehicle Model"
        body = f"""Failed to retrieve enquiries for vehicle model: {vehicle_model}.
        Case-sensitive search: {'Yes' if case_sensitive else 'No'}.
        \nError: {str(e)}
        """
        notify_failure(subject, body)

        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        log_info("Ending function: get_enquiries_by_vehicle_model")


@app.route('/mark-sent-to-dealer', methods=['PUT'])
def mark_sent_to_dealer():
    """
    Mark an enquiry as sent to the dealer based on the provided mobile number.

    This function updates the `SentToDealer` status of an enquiry to `True` for the specified
    mobile number. It returns a success message if the update is successful or an error message
    if the enquiry is not found or an internal server error occurs.

    Parameters:
        - mobile_no (str): The mobile number of the enquiry to be updated.

    Returns:
        - A JSON response of records with email notifications
    """
    try:
        log_info("Starting function: mark_sent_to_dealer")

        mobile_no = request.args.get('mobileno')
        log_info(f"Received mobile_no: {mobile_no}")

        if not mobile_no:
            log_warning("Mobile number is required but not provided")
            return jsonify({"error": "Mobile number is required"}), 400

        enquiry = session.query(ProductEnquiryForms).filter_by(MobileNo=mobile_no).first()

        if not enquiry:
            log_warning(f"Enquiry not found for mobile number: {mobile_no}")
            return jsonify({"error": "Enquiry not found"}), 404

        enquiry.SentToDealer = True
        session.commit()

        enquiry_details = record_to_dict(enquiry)
        enquiry_details_str = format_enquiries_for_email([enquiry_details])

        subject = "Enquiry Marked as Sent to Dealer"
        body = f"""The enquiry with mobile number {mobile_no} has been successfully marked as sent to the dealer.
        
        Details of the enquiry:
        {enquiry_details_str}"""
        notify_success(subject, body)

        log_info(f"Enquiry with mobile number {mobile_no} marked as sent to dealer successfully")

        return jsonify({
            "message": "Enquiry marked as sent to dealer",
            "enquiry": enquiry_details
        }), 200

    except Exception as e:
        log_error(f"Error marking enquiry as sent to dealer: {str(e)}")

        subject = "Failed to Mark Enquiry as Sent to Dealer"
        body = f"""Failed to mark the enquiry with mobile number {mobile_no} as sent to the dealer.

           Error: {str(e)}
           """
        notify_failure(subject, body)

        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        log_info("Ending function: mark_sent_to_dealer")


@app.route('/search-enquiries', methods=['GET'])
def search_enquiries():
    """
    Search for enquiries based on customer name, mobile number, or email.

    This function allows searching for enquiries by filtering based on the provided customer
    name, mobile number, and email. It performs case-insensitive searches for customer names
    and exact matches for mobile numbers and emails.

    Parameters:
        - customer_name (str): The name of the customer to search for (case-insensitive).
        - mobile_no (str): The mobile number of the customer to search for (exact match).
        - email (str): The email of the customer to search for (exact match).

    Returns:
        - A JSON response of records with email notifications
    """
    try:
        log_info("Starting function: search_enquiries")

        customer_name = request.args.get('customername')
        mobile_no = request.args.get('mobileno')
        email = request.args.get('email')
        log_info(f"Received parameters: customer_name={customer_name}, mobile_no={mobile_no}, email={email}")

        query = session.query(ProductEnquiryForms)

        if customer_name:
            query = query.filter(ProductEnquiryForms.CustomerName.ilike(f"%{customer_name}%"))
            log_info(f"Filtering by customer_name: {customer_name}")
        if mobile_no:
            query = query.filter_by(MobileNo=mobile_no)
            log_info(f"Filtering by mobile_no: {mobile_no}")
        if email:
            query = query.filter_by(Email=email)
            log_info(f"Filtering by email: {email}")

        enquiries = query.all()

        if not enquiries:
            log_info("No enquiries found for the provided information")
            return jsonify({"message": "No enquiries found for the provided information"}), 404

        enquiries_data = [record_to_dict(enquiry) for enquiry in enquiries]

        subject = "Enquiries Search Success"
        body = f"""Successfully retrieved enquiries based on the following search criteria:
        - Customer Name: {customer_name}
        - Mobile Number: {mobile_no}
        - Email: {email}\n\nTotal enquiries found: {len(enquiries_data)}
        \nDetails of the records:{format_enquiries_for_email(enquiries_data)}
        """
        notify_success(subject, body)

        log_info(f"Successfully retrieved {len(enquiries_data)} enquiries")

        return jsonify({
            "total_count": len(enquiries_data),
            "enquiries": enquiries_data
        }), 200

    except Exception as e:
        log_error(f"Error searching enquiries: {str(e)}")

        subject = "Failed to Search Enquiries"
        body = f"""
        Failed to search enquiries with the following parameters:
        - Customer Name: {customer_name}
        - Mobile Number: {mobile_no}
        - Email: {email}

        Error: {str(e)}
        """
        notify_failure(subject, body)

        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        log_info("Ending function: search_enquiries")


@app.route('/get-dealer-codes-and-names', methods=['GET'])
def get_dealer_codes_and_names():
    """
    Retrieves and returns dealer codes and names for the given state.

    This function fetches dealer codes and names from the database based on the provided
    state parameter and returns them in a formatted manner.

    Parameters:
        - state (str): The state for which dealer codes and names are to be retrieved.

    Returns:
        - A JSON response with dealer codes and names and email notifications
    """
    try:
        log_info("Starting function: get_dealer_codes_and_names")

        state = request.args.get('state')
        log_info(f"Received state: {state}")

        if not state:
            log_warning("State parameter is required but not provided")
            return jsonify({"error": "State parameter is required"}), 400

        dealers = session.query(ProductEnquiryForms).filter_by(DealerState=state).all()

        if not dealers:
            log_info(f"No dealers found for state: {state}")
            return jsonify({"message": "No dealers found for the provided state"}), 404

        dealers_data = [{'dealercode': dealer.DealerCode, 'dealername': dealer.DealerName} for dealer in dealers]

        formatted_dealers = format_dealers_for_email(dealers_data)

        subject = "Dealer Codes and Names Retrieval Success"
        body = f"""Successfully retrieved dealer codes and names for the state: {state}.\n\n
        Total dealers found: {len(dealers_data)}

        Details of the records:
        {formatted_dealers}
        """
        notify_success(subject, body)

        log_info(f"Successfully retrieved {len(dealers_data)} dealers for state: {state}")

        return jsonify({'total_count': len(dealers_data), 'dealers': dealers_data}), 200

    except Exception as e:
        log_error(f"Error retrieving dealer codes and names: {str(e)}")

        subject = "Failed to Retrieve Dealer Codes and Names"
        body = f"""Failed to retrieve dealer codes and names for state: {state}.
        \nError: {str(e)}
        """
        notify_failure(subject, body)

        return jsonify({'error': 'Failed to retrieve dealer codes and names'}), 500

    finally:
        log_info("Ending function: get_dealer_codes_and_names")


@app.route('/dealer-interactions', methods=['GET'])
def dealer_interactions():
    """
    Retrieve dealer interactions based on provided filters.

    This function retrieves enquiries that have been marked as sent to a dealer. You can filter
    the results based on the dealer's name, state, and town. It returns a list of enquiries that
    match the filters or a message if no enquiries are found.

    Parameters:
        - dealer_name (str): The name of the dealer to filter by (case-insensitive).
        - dealer_state (str): The state of the dealer to filter by.
        - dealer_town (str): The town of the dealer to filter by.

    Returns:
        - A JSON response with email notifications
    """
    try:
        log_info("Starting function: dealer_interactions")

        dealer_name = request.args.get('dealername')
        dealer_state = request.args.get('dealerstate')
        dealer_town = request.args.get('dealertown')
        log_info(f"Received parameters: dealer_name={dealer_name}, dealer_state={dealer_state},"
                 f" dealer_town={dealer_town}")

        query = session.query(ProductEnquiryForms).filter_by(SentToDealer=True)

        if dealer_name:
            query = query.filter(ProductEnquiryForms.DealerName.ilike(f"%{dealer_name}%"))
            log_info(f"Filtering by dealer_name: {dealer_name}")
        if dealer_state:
            query = query.filter_by(DealerState=dealer_state)
            log_info(f"Filtering by dealer_state: {dealer_state}")
        if dealer_town:
            query = query.filter_by(DealerTown=dealer_town)
            log_info(f"Filtering by dealer_town: {dealer_town}")

        enquiries = query.all()

        if not enquiries:
            log_info("No dealer interactions found for the provided filters")
            return jsonify({"message": "No dealer interactions found"}), 404

        enquiries_data = [record_to_dict(enquiry) for enquiry in enquiries]

        subject = "Dealer Interactions Retrieval Success"
        body = f"""Successfully retrieved dealer interactions with the following filters:
        - Dealer Name: {dealer_name}
        - Dealer State: {dealer_state}
        - Dealer Town: {dealer_town}

        Total dealer interactions found: {len(enquiries_data)}
        \nDetails of the records:
        {format_enquiries_for_email(enquiries_data)}
        """
        notify_success(subject, body)

        log_info(f"Successfully retrieved {len(enquiries_data)} dealer interactions")

        return jsonify({
            "total_count": len(enquiries_data),
            "enquiries": enquiries_data
        }), 200

    except Exception as e:
        log_error(f"Error retrieving dealer interactions: {str(e)}")

        subject = "Failed to Retrieve Dealer Interactions"
        body = f"""Failed to retrieve dealer interactions with the following filters:
        - Dealer Name: {dealer_name}
        - Dealer State: {dealer_state}
        - Dealer Town: {dealer_town}

        Error: {str(e)}
        """
        notify_failure(subject, body)

        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        log_info("Ending function: dealer_interactions")


@app.route('/post-records', methods=['POST'])
def post_records():
    """
    End point to insert new record into Database.

    :return: JSON with new record details or else error
    """
    log_info("POST /post_records - Started processing request.")

    try:
        request_body = request.get_json(force=True)
        log_debug(f"Request body received: {request_body}")
        records_inserted = 0
        inserted_records_details = []

        for index, item in enumerate(request_body):
            log_info(f"Processing record {index + 1}/{len(request_body)}: {item}")

            record = ProductEnquiryForms(
                CustomerName=item["CustomerName"],
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
                IsPurchased=item["IsPurchased"]
            )

            # This will Add each record to the session
            session.add(record)
            records_inserted += 1
            log_debug(f"Record {index + 1} added to session.")

            # Appends into the inserted record details
            inserted_records_details.append({
                "CustomerName": item["CustomerName"],
                "MobileNo": item["MobileNo"],
                "Email": item["Email"],
                "VehicleModel": item["VehicleModel"],
                "DealerName": item["DealerName"],
                "ExpectedDateofPurchase": item["ExpectedDateofPurchase"]
            })

        session.commit()
        log_info(f"Successfully inserted {records_inserted} records into the database.")

        subject = "Success: Records Inserted"
        body = (f"{records_inserted} records were successfully inserted into the database.\n\nDetails of inserted "
                f"records are:\n")
        for i, record in enumerate(inserted_records_details, start=1):
            body += (f"Record {i}:\n"
                     f"Customer Name: {record['CustomerName']}\n"
                     f"Mobile No: {record['MobileNo']}\n"
                     f"Email: {record['Email']}\n"
                     f"Vehicle Model: {record['VehicleModel']}\n"
                     f"Dealer Name: {record['DealerName']}\n"
                     f"Expected Date of Purchase: {record['ExpectedDateofPurchase']}\n\n")

        notify_success(subject, body)
        log_info(f"Success email notification sent to {RECEIVER_EMAIL} from {SENDER_EMAIL}.")

        response = jsonify({
            "message": f"{records_inserted} records inserted successfully",
            "inserted_records": inserted_records_details
        }), 201
        log_info("POST /post_records - Records insertion successful.")
        return response

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"Database error: {error_message}")

        subject = "Failure: Database Error During Record Insertion"
        body = f"An error occurred while inserting the records into the database. Error: {error_message}"

        notify_failure(subject, body)
        log_error("Failure email notification sent.")

        return jsonify({"error": "An error occurred while inserting the records", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        log_error(f"Unexpected error: {str(e)}")

        subject = "Failure: Unexpected Error During Record Insertion"
        body = f"An unexpected error occurred while inserting the records. Error: {str(e)}"

        notify_failure(subject, body)
        log_error("Failure email notification sent.")

        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        session.close()
        log_info("POST /post_records - Session closed and Finished processing request.")


@app.route('/get-home-page1', methods=['GET'])
def get_home_page1():
    """
    Endpoint to retrieve all records from ProductEnquiryForms.

    :return: JSON response with all records or an error message
    """
    log_info("GET /get-home-page1 - Started processing request.")

    try:
        results = session.query(ProductEnquiryForms).all()
        record_count = len(results)
        log_info(f"GET /get-home-page1 - Retrieved {record_count} records from the database.")

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result_list = "\n\n".join(
            [f"Record {i + 1}:\n\n" + "\n".join([f"{key}: {value}" for key, value in item.items()])
             for i, item in enumerate(result_list)]
        )

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Details:\n\n{formatted_result_list}"
        )

        notify_success(
            "Records Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /get-home-page1 - Successfully processed {record_count} records.")

        return jsonify({
            "message": "Records retrieved successfully",
            "total_count": record_count,
            "records": result_list
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /get-home-page1 - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({"error": "An error occurred while fetching the records", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /get-home-page1 - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{str(e)}"
        )
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        session.close()
        log_info("GET /get-home-page1 - Session closed.")
        log_info("GET /get-home-page1 - Finished processing request.")


@app.route('/get-single-record', methods=['GET'])
def get_single_record():
    """
    Endpoint to retrieve a single record from ProductEnquiryForms based on LeadId.

    :return: JSON response with the record or an error message
    """
    leadid = request.args.get("leadid")
    log_info(f"GET /get_single_record - Started processing request for LeadId: {leadid}")

    try:
        results = session.query(ProductEnquiryForms).filter(ProductEnquiryForms.LeadId == leadid).all()

        record_count = len(results)

        if record_count == 0:
            log_info(f"GET /get_single_record - No record found for LeadId: {leadid}")
            notify_failure(
                "Record Not Found",
                f"No record found for LeadId: {leadid} in ProductEnquiryForms."
            )
            return jsonify({"message": "No record found", "leadid": leadid}), 404

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result = "\n".join([f"{key}: {value}" for key, value in result_list[0].items()])

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Record Details for LeadId: {leadid}\n\n"
            f"{formatted_result}"
        )

        notify_success(
            "Record Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /get_single_record - Successfully processed {record_count} record(s) for LeadId: {leadid}")

        return jsonify({
            "message": "Record retrieved successfully",
            "total_count": record_count,
            "record": result_list
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /get_single_record - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching the record with LeadId:"
            f" {leadid} from ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({"error": "An error occurred while fetching the record", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /get_single_record - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching the record with LeadId:"
            f" {leadid} from ProductEnquiryForms.\n\nError details:\n{str(e)}"
        )
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        session.close()
        log_info("GET /get_single_record - Session closed.")
        log_info("GET /get_single_record - Finished processing request.")


# querying using limit
@app.route('/get-limited-records-by-env-variable', methods=['GET'])
def get_limited_records_using_env_variable():
    """
    Endpoint to retrieve a limited number of records from ProductEnquiryForms.

    It retrieves the records based on offset, if offset(0) then it will retrieves from 0th/first row, if it is 1 then
    retrieves 2nd row so on... And limit defines number of records to be retrieved (If limit = 10) then total 10 records
    will be retrieved.

    :return: JSON response with the limited records or an error message
    """
    log_info("GET /get_limited_records - Started processing request.")

    try:
        # Retrieves the limit from environment variable
        limit = int(os.getenv("LIMIT", 10))

        results = session.query(ProductEnquiryForms).limit(limit).offset(0).all()
        record_count = len(results)
        log_info(f"GET /get_limited_records - Retrieved {record_count} records from the database with limit {limit}.")

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result_list = "\n\n".join(
            [f"Record {i + 1}:\n\n" + "\n".join([f"{key}: {value}" for key, value in item.items()])
             for i, item in enumerate(result_list)]
        )

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Details:\n\n{formatted_result_list}"
        )

        notify_success(
            "Records Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /get_limited_records - Successfully processed {record_count} records.")

        return jsonify({
            "message": "Records retrieved successfully",
            "total_count": record_count,
            "records": result_list
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /get_limited_records - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({"error": "An error occurred while fetching the records", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /get_limited_records - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching records from"
            f"ProductEnquiryForms.\n\nError details:\n{str(e)}"
        )
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        session.close()
        log_info("GET /get_limited_records - Session closed.")
        log_info("GET /get_limited_records - Finished processing request.")


@app.route('/get-limited-records-by-hard-coding', methods=['GET'])
def get_limited_records_by_hard_coding():
    """
    Endpoint to retrieve a limited number of records from ProductEnquiryForms.

    It retrieves the records based on offset, and limit defines the number of records to be retrieved.
    Default limit is set to 3, starting from offset 2.

    :return: JSON response with the limited records or an error message
    """
    log_info("GET /get_limited_records1 - Started processing request.")

    try:
        limit = 3
        offset = 2

        results = session.query(ProductEnquiryForms).limit(limit).offset(offset).all()
        record_count = len(results)
        log_info(f"GET /get_limited_records1 - Retrieved {record_count} records from the database with limit "
                 f"{limit} and offset {offset}.")

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result_list = "\n\n".join(
            [f"Record {i + 1}:\n\n" + "\n".join([f"{key}: {value}" for key, value in item.items()])
             for i, item in enumerate(result_list)]
        )

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Details:\n\n{formatted_result_list}"
        )

        notify_success(
            "Records Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /get_limited_records1 - Successfully processed {record_count} records.")

        return jsonify({
            "message": "Records retrieved successfully",
            "total_count": record_count,
            "records": result_list
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /get_limited_records1 - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({"error": "An error occurred while fetching the records", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /get_limited_records1 - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{str(e)}"
        )
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

    finally:
        session.close()
        log_info("GET /get_limited_records1 - Session closed.")
        log_info("GET /get_limited_records1 - Finished processing request.")


@app.route('/historic-leads', methods=['GET'])
def get_historic_leads():
    """
    Endpoint to retrieve historic leads between a given date range (startdate and enddate).

    Query params:
    - startdate: The start date for the filter.
    - enddate: The end date for the filter.

    :return: JSON response with the historic leads or an error message.
    """
    log_info("GET /historic_leads - Started processing request.")

    try:
        start_date = request.args.get("startdate")
        end_date = request.args.get("enddate")

        if not start_date or not end_date:
            log_error("GET /historic_leads - Missing required parameters: startdate or enddate.")
            return jsonify({
                "error": "Missing required parameters",
                "message": "Please provide both 'startdate' and 'enddate'."
            }), 400

        results = session.query(ProductEnquiryForms).filter(
            and_(
                ProductEnquiryForms.CreatedDate >= start_date,
                ProductEnquiryForms.CreatedDate <= end_date
            )
        ).all()

        record_count = len(results)
        log_info(f"GET /historic_leads - Retrieved {record_count} records from the database "
                 f"between {start_date} and {end_date}.")

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result_list = "\n\n".join(
            [f"Record {i + 1}:\n\n" + "\n".join([f"{key}: {value}" for key, value in item.items()])
             for i, item in enumerate(result_list)]
        )

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Details:\n\n{formatted_result_list}"
        )

        notify_success(
            "Historic Leads Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /historic_leads - Successfully processed {record_count} records.")

        return jsonify({
            "message": "Records retrieved successfully",
            "total_count": record_count,
            "records": result_list
        }), 200

    except ValueError as e:
        log_error(f"GET /historic_leads - Invalid date format: {str(e)}")
        notify_failure(
            "Date Format Error",
            f"Invalid date format provided for startdate or enddate. Details:\n{str(e)}"
        )
        return jsonify({
            "error": "Invalid date format",
            "details": str(e)
        }), 400

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /historic_leads - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({
            "error": "An error occurred while fetching the records",
            "details": error_message
        }), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /historic_leads - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching records from "
            f"ProductEnquiryForms.\n\nError details:\n{str(e)}"
        )
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

    finally:
        session.close()
        log_info("GET /historic_leads - Session closed.")
        log_info("GET /historic_leads - Finished processing request.")


@app.route('/purchased-historic-leads', methods=['GET'])
def get_purchased_leads():
    """
    Endpoint to retrieve purchased leads between a given date range (startdate and enddate),
    filtered by dealer code.

    Query params:
    - startdate: The start date for the filter.
    - enddate: The end date for the filter.
    - dealercode: The dealer code to filter by.

    :return: JSON response with the purchased leads or an error message.
    """
    log_info("GET /purchased_historic_leads - Started processing request.")

    try:
        start_date = request.args.get("startdate")
        end_date = request.args.get("enddate")
        dealer_code = request.args.get("dealercode")

        if not start_date or not end_date or not dealer_code:
            log_error("GET /purchased_historic_leads - Missing required parameters: startdate, enddate, or dealercode.")
            return jsonify({
                "error": "Missing required parameters",
                "message": "Please provide 'startdate', 'enddate', and 'dealercode'."
            }), 400

        results = session.query(ProductEnquiryForms).filter(
            and_(
                ProductEnquiryForms.CreatedDate >= start_date,
                ProductEnquiryForms.CreatedDate <= end_date,
                ProductEnquiryForms.IsPurchased == True,
                ProductEnquiryForms.DealerCode == dealer_code
            )
        ).all()

        record_count = len(results)
        log_info(f"GET /purchased_historic_leads - Retrieved {record_count} records from the database "
                 f"between {start_date} and {end_date} for dealer code {dealer_code}.")

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result_list = "\n\n".join(
            [f"Record {i + 1}:\n\n" + "\n".join([f"{key}: {value}" for key, value in item.items()])
             for i, item in enumerate(result_list)]
        )

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Details:\n\n{formatted_result_list}"
        )

        notify_success(
            "Purchased Leads Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /purchased_historic_leads - Successfully processed {record_count} records.")

        return jsonify({
            "message": "Purchased leads retrieved successfully",
            "total_count": record_count,
            "records": result_list
        }), 200

    except ValueError as e:
        log_error(f"GET /purchased_historic_leads - Invalid date format: {str(e)}")
        notify_failure(
            "Date Format Error",
            f"Invalid date format provided for startdate or enddate. Details:\n{str(e)}"
        )
        return jsonify({
            "error": "Invalid date format",
            "details": str(e)
        }), 400

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /purchased_historic_leads - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching purchased leads from "
            f"ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({
            "error": "An error occurred while fetching the records",
            "details": error_message
        }), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /purchased_historic_leads - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching purchased leads.\n\nError details:\n{str(e)}"
        )
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

    finally:
        session.close()
        log_info("GET /purchased_historic_leads - Session closed.")
        log_info("GET /purchased_historic_leads - Finished processing request.")


@app.route('/not-purchased-historic-leads', methods=['GET'])
def get_not_purchased_leads():
    """
    Endpoint to retrieve non-purchased leads between a given date range (startdate and enddate),
    filtered by dealer code.

    Query params:
    - startdate: The start date for the filter.
    - enddate: The end date for the filter.
    - dealercode: The dealer code to filter by.

    :return: JSON response with the non-purchased leads or an error message.
    """
    log_info("GET /not_purchased_historic_leads - Started processing request.")

    try:
        start_date = request.args.get("startdate")
        end_date = request.args.get("enddate")
        dealer_code = request.args.get("dealercode")

        if not start_date or not end_date or not dealer_code:
            log_error(
                "GET /not_purchased_historic_leads - Missing required parameters: startdate, enddate, or dealercode.")
            return jsonify({
                "error": "Missing required parameters",
                "message": "Please provide 'startdate', 'enddate', and 'dealercode'."
            }), 400

        results = session.query(ProductEnquiryForms).filter(
            and_(
                ProductEnquiryForms.CreatedDate >= start_date,
                ProductEnquiryForms.CreatedDate <= end_date,
                ProductEnquiryForms.IsPurchased == False,
                ProductEnquiryForms.DealerCode == dealer_code
            )
        ).all()

        record_count = len(results)
        log_info(f"GET /not_purchased_historic_leads - Retrieved {record_count} records from the database "
                 f"between {start_date} and {end_date} for dealer code {dealer_code}.")

        result_list = []
        for item in results:
            item_dict = item.__dict__.copy()
            item_dict.pop('_sa_instance_state', None)
            for key, value in item_dict.items():
                if isinstance(value, (date, datetime)):
                    item_dict[key] = value.isoformat()
            result_list.append(item_dict)

        formatted_result_list = "\n\n".join(
            [f"Record {i + 1}:\n\n" + "\n".join([f"{key}: {value}" for key, value in item.items()])
             for i, item in enumerate(result_list)]
        )

        notification_message = (
            f"Total records retrieved: {record_count}\n\n"
            f"Details:\n\n{formatted_result_list}"
        )

        notify_success(
            "Non-Purchased Leads Retrieved Successfully",
            notification_message
        )

        log_info(f"GET /not_purchased_historic_leads - Successfully processed {record_count} records.")

        return jsonify({
            "message": "Non-purchased leads retrieved successfully",
            "total_count": record_count,
            "records": result_list
        }), 200

    except ValueError as e:
        log_error(f"GET /not_purchased_historic_leads - Invalid date format: {str(e)}")
        notify_failure(
            "Date Format Error",
            f"Invalid date format provided for startdate or enddate. Details:\n{str(e)}"
        )
        return jsonify({
            "error": "Invalid date format",
            "details": str(e)
        }), 400

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"GET /not_purchased_historic_leads - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while fetching non-purchased leads from "
            f"ProductEnquiryForms.\n\nError details:\n{error_message}"
        )
        return jsonify({
            "error": "An error occurred while fetching the records",
            "details": error_message
        }), 500

    except Exception as e:
        session.rollback()
        log_error(f"GET /not_purchased_historic_leads - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while fetching non-purchased leads.\n\nError details:\n{str(e)}"
        )
        return jsonify({
            "error": "An unexpected error occurred",
            "details": str(e)
        }), 500

    finally:
        session.close()
        log_info("GET /not_purchased_historic_leads - Session closed.")
        log_info("GET /not_purchased_historic_leads - Finished processing request.")


@app.route('/update-record', methods=['PUT'])
def update_record():
    """
    Endpoint to update a product enquiry record based on the given mobile number.

    Request Body (JSON):
    - mobileno: The mobile number to identify the record to update (required).
    - customername: (Optional) Updated customer name.
    - gender: (Optional) Updated gender.
    - age: (Optional) Updated age.
    - occupation: (Optional) Updated occupation.
    - email: (Optional) Updated email.
    - vehiclemodel: (Optional) Updated vehicle model.
    - state: (Optional) Updated state.
    - district: (Optional) Updated district.
    - city: (Optional) Updated city.
    - existingvehicle: (Optional) Updated existing vehicle information.
    - dealerstate: (Optional) Updated dealer state.
    - dealertown: (Optional) Updated dealer town.
    - dealername: (Optional) Updated dealer name.
    - briefaboutenquiry: (Optional) Updated brief about the enquiry.
    - expecteddateofpurchase: (Optional) Updated expected date of purchase (format: YYYY-MM-DD).
    - senttodealer: (Optional) Updated sent to dealer status (True/False).
    - dealercode: (Optional) Updated dealer code.
    - leadid: (Optional) Updated lead ID.
    - createddate: (Optional) Updated created date (format: YYYY-MM-DD).
    - ispurchased: (Optional) Updated purchased status (True/False).

    :return: JSON response indicating success or failure.
    """
    request_body = request.get_json(force=True)
    log_info("PUT /update_record - Started processing request.")

    try:
        if not request_body or not isinstance(request_body, dict):
            log_error("PUT /update_record - Invalid request body, expecting a JSON object.")
            return jsonify(
                {"error": "Invalid request body", "message": "Expected a JSON object with the fields to update."}), 400

        mobileno = request_body.get("mobileno")
        if not mobileno:
            log_error("PUT /update_record - Missing required field: mobileno.")
            return jsonify({"error": "Missing required field", "message": "Please provide 'mobileno'."}), 400

        # Validate that 'mobileno' is an integer
        try:
            mobileno = int(mobileno)
        except ValueError:
            log_error("PUT /update_record - Invalid mobileno format.")
            return jsonify({"error": "Invalid mobileno", "message": "Mobileno must be an integer."}), 400

        update_fields = {key: value for key, value in request_body.items() if key != "mobileno"}

        if not update_fields:
            log_error("PUT /update_record - No fields provided for update.")
            return jsonify({"error": "No fields provided",
                            "message": "At least one field other than 'mobileno' must be provided for update."}), 400

        result = session.query(ProductEnquiryForms).filter(
            ProductEnquiryForms.MobileNo == mobileno
        ).update(
            update_fields, synchronize_session='fetch'
        )

        if result == 0:
            log_info(f"PUT /update_record - No record found for mobileno: {mobileno}.")
            return jsonify({"message": "No record found for the given mobile number."}), 404

        session.commit()
        log_info(f"PUT /update_record - Successfully updated record for mobileno: {mobileno}.")

        updated_details = "\n".join([f"{field}: {value}" for field, value in update_fields.items()])

        notify_success(
            "Record Updated Successfully",
            f"The record for mobile number {mobileno} was updated successfully."
            f"\n\nHere are the details of the updated fields:\n\n{updated_details}"
        )

        return jsonify({
            "message": "Record updated successfully",
            "mobileno": mobileno,
            "updated_fields": update_fields
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get("orig", e))
        log_error(f"PUT /update_record - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while updating the record for mobile number "
            f"{mobileno}. Error details: {error_message}"
        )
        return jsonify({"error": "Database error", "details": error_message}), 500

    except Exception as e:
        session.rollback()
        log_error(f"PUT /update_record - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while updating the record. Error details: {str(e)}"
        )
        return jsonify({"error": "Unexpected error", "details": str(e)}), 500

    finally:
        session.close()
        log_info("PUT /update_record - Session closed.")
        log_info("PUT /update_record - Finished processing request.")


@app.route('/del-single-record', methods=['DELETE'])
def del_record():
    """
    Endpoint to delete product enquiry records where the expected date of purchase is before the given date.

    Query params:
    - expecteddateofpurchase: The cutoff date for the records to delete.

    :return: JSON response indicating the number of records deleted, with details about the deleted records.
    """
    log_info("DELETE /del_single_record - Started processing request.")

    try:
        expected_date = request.args.get("expecteddateofpurchase")

        if not date:
            log_error("DELETE /del_single_record - Missing required parameter: expecteddateofpurchase.")
            return jsonify({
                "error": "Missing required parameter",
                "message": "Please provide 'expecteddateofpurchase'."
            }), 400

        records_to_delete = session.query(ProductEnquiryForms).filter(
            ProductEnquiryForms.ExpectedDateofPurchase < expected_date
        ).all()

        record_count = len(records_to_delete)

        result = session.query(ProductEnquiryForms).filter(
            ProductEnquiryForms.ExpectedDateofPurchase < expected_date
        ).delete()

        session.commit()

        deleted_records_details = "\n\n".join(
            [f"Record {i + 1}:\n" + "\n".join(
                [f"{key}: {value}" for key, value in vars(record).items() if key != '_sa_instance_state'])
             for i, record in enumerate(records_to_delete)]
        )

        notification_message = (
            f"Total records deleted: {result}\n\n"
            f"Date used for filtering: {expected_date}\n\n"
            f"Details of deleted records:\n{deleted_records_details}"
        )

        notify_success(
            "Records Deleted Successfully",
            notification_message
        )

        log_info(f"DELETE /del_single_record - Successfully deleted {result} records before {expected_date}.")
        log_info(f"Details of deleted records:\n{deleted_records_details}")

        return jsonify({
            "message": f"Records deleted successfully. Total deleted: {result}",
            "deleted_count": result,
            "deleted_records_details": deleted_records_details
        }), 200

    except SQLAlchemyError as e:
        session.rollback()
        error_message = str(e.__dict__.get('orig', e))
        log_error(f"DELETE /del_single_record - Database error: {error_message}")
        notify_failure(
            "Database Error",
            f"An error occurred while deleting records. Error details:\n{error_message}"
        )
        return jsonify({
            "error": "Database error",
            "details": error_message
        }), 500

    except Exception as e:
        session.rollback()
        log_error(f"DELETE /del_single_record - Unexpected error: {str(e)}")
        notify_failure(
            "Unexpected Error",
            f"An unexpected error occurred while deleting records. Error details:\n{str(e)}"
        )
        return jsonify({
            "error": "Unexpected error",
            "details": str(e)
        }), 500

    finally:
        session.close()
        log_info("DELETE /del_single_record - Session closed.")
        log_info("DELETE /del_single_record - Finished processing request.")


if __name__ == "__main__":
    app.run(debug=True)
