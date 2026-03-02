import logging
import time
from flask import Blueprint, request, jsonify
from src.application.use_cases.simulate_loan import SimulateLoanUseCase, SimulateLoanRequestDTO
from src.application.use_cases.create_loan import CreateLoanUseCase, CreateLoanRequestDTO
from src.application.use_cases.register_payment import RegisterPaymentUseCase, IdempotencyError
from src.application.queries.get_loan_statement_query import GetLoanStatementQuery
from src.infrastructure.adapters.output.persistence.repositories.sqla_unit_of_work import SqlAlchemyUnitOfWork
from src.infrastructure.adapters.output.persistence.repositories.sqla_loan_read_repository import SqlAlchemyLoanReadRepository
from src.infrastructure.adapters.output.usury.mock_usury_service import MockUsuryRateService
from src.infrastructure.config.extensions import db

logger = logging.getLogger(__name__)
loans_bp = Blueprint('loans_v1', __name__, url_prefix='/api/v1/loans')

@loans_bp.route('/simulate', methods=['POST'])
def simulate_loan():
    """
    Endpoint to simulate a loan amortization.
    """
    start_time = time.time()
    data = request.get_json() or {}
    
    safe_data = data.copy()
    if 'document_number' in safe_data: 
        safe_data['document_number'] = "***MASKED***"

    logger.info("Received loan simulation request", extra={"payload": safe_data})

    try:
        req_dto = SimulateLoanRequestDTO(
            requested_amount=str(data['requested_amount']),
            interest_rate=str(data['interest_rate']),
            interest_rate_type=str(data['interest_rate_type']),
            term_months=int(data['term_months']),
            payment_modality=str(data['payment_modality']),
            start_date=data.get('start_date')
        )
        
        use_case = SimulateLoanUseCase()
        result = use_case.execute(req_dto)
        
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Simulation completed successfully in {execution_time_ms}ms")
        
        return jsonify(result), 200

    except KeyError as e:
        raise ValueError(f"Missing required field: {str(e)}")

@loans_bp.route('', methods=['POST'])
def create_loan():
    """
    Endpoint to originate a new Loan under ACID transactional rules.
    """
    start_time = time.time()
    data = request.get_json() or {}
    
    logger.info("Received loan creation request", extra={"payload": data})
    
    try:
        req_dto = CreateLoanRequestDTO(
            customer_id=str(data['customer_id']),
            requested_amount=str(data['requested_amount']),
            interest_rate=str(data['interest_rate']),
            interest_rate_type=str(data['interest_rate_type']),
            term_months=int(data['term_months']),
            payment_modality=str(data['payment_modality'])
        )
        
        # Dependency Injection (Manual for now, can be extracted to DI container)
        uow = SqlAlchemyUnitOfWork(db.session)
        usury_service = MockUsuryRateService()
        
        use_case = CreateLoanUseCase(uow=uow, usury_rate_service=usury_service)
        result = use_case.execute(req_dto)
        
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Loan creation completed in {execution_time_ms}ms")
        
        return jsonify({
            "message": "Loan created successfully",
            "data": result
        }), 201
        
    except KeyError as e:
        raise ValueError(f"Missing required field: {str(e)}")

@loans_bp.route('/<loan_id>/payments', methods=['POST'])
def register_payment(loan_id):
    """
    Endpoint to process a loan payment cascade.
    """
    start_time = time.time()
    data = request.get_json() or {}
    
    logger.info(f"Received payment request for loan {loan_id}", extra={"payload": data})
    
    try:
        uow = SqlAlchemyUnitOfWork(db.session)
        use_case = RegisterPaymentUseCase(uow=uow)
        
        result = use_case.execute(loan_id, data)
        
        execution_time_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Payment processed in {execution_time_ms}ms")
        
        return jsonify({
            "message": "Payment processed successfully",
            "data": result
        }), 201
        
    except KeyError as e:
        raise ValueError(f"Missing required field: {str(e)}")
    except IdempotencyError as e:
        # According to standard idempotency practices, we might return 200 OK with the existing status
        # but for simplicity, we return 409 Conflict.
        return jsonify({
            "error": "Conflict",
            "message": str(e)
        }), 409

@loans_bp.route('/<loan_id>/statement', methods=['GET'])
def get_loan_statement(loan_id):
    """
    Endpoint (CQRS Read) to fetch dynamically computed statement.
    """
    try:
        read_repo = SqlAlchemyLoanReadRepository(db.session)
        query_handler = GetLoanStatementQuery(read_repo=read_repo)
        
        dto = query_handler.execute(loan_id)
        
        # Convert dataclass to dict
        import dataclasses
        return jsonify({
            "data": dataclasses.asdict(dto)
        }), 200
        
    except ValueError as e:
        if "not found" in str(e).lower():
            return jsonify({
                "error": "Not Found",
                "message": str(e)
            }), 404
        raise e
