from typing import Any, Dict
from langchain.tools import BaseTool
from pydantic import Field
from sqlalchemy.orm import Session
from sqlalchemy import text
from loguru import logger
from app.database import SessionLocal
from app.models.models import VendorDatabase


class SQLValidatorTool(BaseTool):
    """Tool to validate extracted data against SQL database."""

    name: str = "sql_validator"
    description: str = (
        "Validate extracted data against the database. "
        "Input should be a JSON string with 'entity_type' (e.g., 'vendor') and 'entity_value' (value to validate). "
        "Returns validation result with details."
    )

    def _validate_vendor(self, db: Session, vendor_name: str) -> Dict[str, Any]:
        """Validate vendor name against vendor database."""
        try:
            # Try exact match first
            vendor = db.query(VendorDatabase).filter(
                VendorDatabase.vendor_name == vendor_name
            ).first()

            if vendor:
                return {
                    "valid": True,
                    "matched": True,
                    "match_type": "exact",
                    "vendor_id": vendor.vendor_id,
                    "is_approved": vendor.is_approved,
                    "details": {
                        "email": vendor.email,
                        "phone": vendor.phone,
                    }
                }

            # Try case-insensitive match
            vendor = db.query(VendorDatabase).filter(
                VendorDatabase.vendor_name.ilike(f"%{vendor_name}%")
            ).first()

            if vendor:
                return {
                    "valid": True,
                    "matched": True,
                    "match_type": "partial",
                    "vendor_id": vendor.vendor_id,
                    "is_approved": vendor.is_approved,
                    "confidence": 0.7,
                }

            # No match found
            return {
                "valid": False,
                "matched": False,
                "message": "Vendor not found in database",
            }

        except Exception as e:
            logger.error(f"Error validating vendor: {e}")
            return {
                "valid": False,
                "error": str(e),
            }

    def _validate_amount(self, db: Session, amount: float, entity_type: str) -> Dict[str, Any]:
        """Validate amount against business rules."""
        try:
            from app.config import settings

            # Check if amount exceeds threshold
            if amount > settings.invoice_threshold_amount:
                return {
                    "valid": True,
                    "threshold_exceeded": True,
                    "threshold": settings.invoice_threshold_amount,
                    "amount": amount,
                    "recommendation": "Flag for review",
                }

            return {
                "valid": True,
                "threshold_exceeded": False,
                "amount": amount,
            }

        except Exception as e:
            logger.error(f"Error validating amount: {e}")
            return {
                "valid": False,
                "error": str(e),
            }

    def _validate_date(self, date_str: str) -> Dict[str, Any]:
        """Validate date format and reasonableness."""
        try:
            from datetime import datetime, timedelta
            import dateutil.parser

            # Try to parse the date
            parsed_date = dateutil.parser.parse(date_str)

            # Check if date is reasonable (not too far in past/future)
            now = datetime.now()
            days_diff = abs((parsed_date - now).days)

            if days_diff > 3650:  # More than 10 years
                return {
                    "valid": False,
                    "message": "Date is too far in past or future",
                    "parsed_date": parsed_date.isoformat(),
                }

            return {
                "valid": True,
                "parsed_date": parsed_date.isoformat(),
                "format": "ISO8601",
            }

        except Exception as e:
            logger.error(f"Error validating date: {e}")
            return {
                "valid": False,
                "error": f"Invalid date format: {str(e)}",
            }

    def _run(self, input_str: str) -> Dict[str, Any]:
        """Validate entity against database."""
        db = SessionLocal()
        try:
            import json
            input_data = json.loads(input_str)
            entity_type = input_data.get("entity_type", "").lower()
            entity_value = input_data.get("entity_value", "")

            if not entity_type or not entity_value:
                return {
                    "success": False,
                    "error": "Missing entity_type or entity_value",
                }

            logger.info(f"Validating {entity_type}: {entity_value}")

            # Route to appropriate validator
            if entity_type in ["vendor", "vendor_name"]:
                result = self._validate_vendor(db, entity_value)
            elif entity_type in ["amount", "total_amount", "claim_amount"]:
                try:
                    amount = float(entity_value)
                    result = self._validate_amount(db, amount, entity_type)
                except ValueError:
                    result = {
                        "valid": False,
                        "error": f"Invalid amount format: {entity_value}",
                    }
            elif entity_type in ["date", "invoice_date", "due_date", "claim_date"]:
                result = self._validate_date(entity_value)
            else:
                result = {
                    "valid": True,
                    "message": f"No validation rules for {entity_type}",
                }

            return {
                "success": True,
                "entity_type": entity_type,
                "entity_value": entity_value,
                "validation_result": result,
            }

        except Exception as e:
            logger.error(f"Error in SQL validator: {e}")
            return {
                "success": False,
                "error": str(e),
            }
        finally:
            db.close()

    async def _arun(self, input_str: str) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(input_str)
